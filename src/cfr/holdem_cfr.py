import numpy as np
from pypokerengine.api.emulator import Emulator
from pypokerengine.engine.table import Table
from pypokerengine.engine.player import Player
from collections import defaultdict
from typing import Dict, List, Union
import random
from copy import deepcopy
from pypokerengine.utils.game_state_utils import (
    restore_game_state,
    attach_hole_card_from_deck,
    attach_hole_card,
)
from pypokerengine.utils.card_utils import gen_cards


class Node:
    def __init__(self, bet_options):
        # Initialize node with the available bet options
        self.num_actions = len(bet_options)

        # Regret sum keeps track of cumulative regrets for each action over time
        self.regret_sum = defaultdict(int)

        # Current strategy for the node given the current regret sums
        self.strategy = defaultdict(int)

        # Cumulative strategy over time; used to calculate the average strategy
        self.strategy_sum = defaultdict(int)

        # Available bet options for the current node (e.g. [check, bet, fold])
        self.bet_options = bet_options

    @classmethod
    def convert_to_relative_pot(cls, valid_actions, pot_size):
        actions = []

        # Extract call and raise actions
        call_action = next(
            action for action in valid_actions if action["action"] == "call"
        )
        raise_action = next(
            action for action in valid_actions if action["action"] == "raise"
        )

        # Handle fold
        if call_action["amount"] != 0:
            actions.append("f")

        # Handle call
        actions.append("c")

        # Handle raise based on your specified distribution
        specified_distribution = []  # [0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0]
        all_in_pot_ratio = raise_action["amount"]["max"] / pot_size

        for value in specified_distribution:
            if value == all_in_pot_ratio:  # Check if the value is same as all-in
                continue

            raise_amount = value * pot_size
            if (
                raise_action["amount"]["min"]
                <= raise_amount
                <= raise_action["amount"]["max"]
            ):
                actions.append(value)

        if raise_action["amount"]["max"] != -1:
            # Append all-in action if it's not already in the list
            actions.append("a")

        return actions

    def get_strategy(self):
        # This method computes and returns the current strategy for the node based on regret matching
        normalizing_sum = 0

        # Calculate strategy proportional to positive regrets
        for a in self.bet_options:
            if self.regret_sum[a] > 0:
                self.strategy[a] = self.regret_sum[a]
            else:
                # If regret is negative or zero, set strategy for this action to 0
                self.strategy[a] = 0

            normalizing_sum += self.strategy[a]

        # Normalize the strategy so probabilities sum to 1
        for a in self.bet_options:
            if normalizing_sum > 0:
                self.strategy[a] /= normalizing_sum
            else:
                # If all regrets are non-positive, assign uniform probability
                self.strategy[a] = 1.0 / self.num_actions

        return self.strategy

    def get_average_strategy(self):
        # This method computes and returns the average strategy across all iterations
        avg_strategy = defaultdict(int)
        normalizing_sum = 0

        # Calculate the sum of all strategy probabilities across all iterations
        for a in self.bet_options:
            normalizing_sum += self.strategy_sum[a]

        # Normalize to get average strategy
        for a in self.bet_options:
            if normalizing_sum > 0:
                avg_strategy[a] = self.strategy_sum[a] / normalizing_sum
            else:
                # If sum is zero, assign uniform probability
                avg_strategy[a] = 1.0 / self.num_actions

        return avg_strategy


class HoldemCFR:
    def __init__(self, iterations):
        self.emulator = Emulator()
        self.iterations = iterations  # Number of iterations to train
        self.nodes: Dict[str, Node] = {}  # Nodes used in the CFR process
        self.player_num = 2
        self.max_round = 1
        self.small_blind_amount = 1
        self.ante_amount = 0
        # emulator.set_game_rule(nb_player, final_round, sb_amount, ante)
        self.emulator.set_game_rule(
            player_num=self.player_num,
            max_round=self.max_round,
            small_blind_amount=self.small_blind_amount,
            ante_amount=self.ante_amount,
        )
        self.players_info = {
            0: {"name": "p0", "stack": 100},
            1: {"name": "p1", "stack": 100},
        }

        self.street_mapper = {
            "preflop": 0,
            "flop": 1,
            "turn": 2,
            "river": 3,
            "showdown": 4,
        }

    def get_street(self, round_state):
        return self.street_mapper[round_state["street"]]

    def cfr_iterations_external(self):
        util = np.zeros(2)  # Utility initialization for both players

        # Loop through each iteration to train
        for t in range(1, self.iterations + 1):
            for i in range(2):  # For both players
                print("Iteration: {}-{}".format(t, i))
                history = [[], [], [], []]
                cards = {1: ["SA", "HA"], 0: ["C2", "D7"]}
                initial_state = self.emulator.generate_initial_game_state(
                    self.players_info
                )
                game_state, events = self.emulator.start_new_round(initial_state)

                # for player in game_state["table"].seats.players:
                #     hole_card = gen_cards(cards[player.uuid])
                #     game_state = attach_hole_card(game_state, player.uuid, hole_card)

                # breakpoint()

                util[i] += self.external_cfr(game_state, events, history, 0, i)

        print("Average game value: {}".format(util[0] / (self.iterations)))

        # Save strategy to a file
        with open("holdemstrat.txt", "w+") as f:
            for i in sorted(self.nodes):
                f.write("{}, {}\n".format(i, self.nodes[i].get_average_strategy()))
                print(i, self.nodes[i].get_average_strategy())

    def external_cfr(
        self, game_state, events, history, nodes_touched, traversing_player_id
    ):
        event = events[-1]
        if "round_state" not in event:
            event = events[-2]

        pot = event["round_state"]["pot"]["main"]["amount"]
        round_state = event["round_state"]
        community_cards = round_state["community_card"]
        round = self.get_street(round_state)

        players: List[Player] = game_state["table"].seats.players

        cards = {player.uuid: get_hole_cards(player) for player in players}
        # if len(community_cards) > 0:
        #     print(community_cards)

        if event["type"] == "event_round_finish":
            regret = 0
            for player in players:
                if player.uuid == traversing_player_id:
                    regret += player.stack - 100
                    break
            # print("Winner: {}".format(event["winners"]))
            # print("Traversing player: {}".format(traversing_player_id))
            # print("Hole cards: {}".format(cards))
            # print(community_cards)
            # print(history)
            # breakpoint()
            return regret

        # Determine which player is acting based on the number of plays
        if event["type"] == "event_ask_player":
            table: Table = game_state["table"]
            valid_actions = event["valid_actions"]

            acting_player_id = event["uuid"]
            acting_player = table.seats.players[acting_player_id]

            infoset_bets = Node.convert_to_relative_pot(valid_actions, pot)
            hole_cards = get_hole_cards(acting_player)
            infoset = f"{hole_cards}_{str(community_cards)}_{str(history)}"

            # If the current infoset doesn't exist in the nodes dictionary, add it
            if infoset not in self.nodes:
                self.nodes[infoset] = Node(infoset_bets)

            nodes_touched += 1
            # If the acting player is the traversing player
            if acting_player_id == traversing_player_id:
                util = defaultdict(int)
                node_util = 0
                strategy = self.nodes[infoset].get_strategy()

                # Iterate over all valid actions and compute their utilities
                for a in infoset_bets:
                    next_history = deepcopy(history)
                    next_history[round].append(a)
                    action, amount = derive_action(a, valid_actions, pot)
                    new_game_state, new_events = self.emulator.apply_action(
                        game_state, action, amount
                    )

                    game_state = restore_game_state_fully(round_state, cards)

                    # breakpoint()
                    util[a] = self.external_cfr(
                        new_game_state,
                        new_events,
                        next_history,
                        nodes_touched,
                        traversing_player_id,
                    )
                    node_util += strategy[a] * util[a]

                # Update the regret sums for each action
                for a in infoset_bets:
                    regret = util[a] - node_util
                    self.nodes[infoset].regret_sum[a] += regret
                return node_util
            else:
                strategy = self.nodes[infoset].get_strategy()
                # Sample an action based on the strategy
                dart = random.random()
                strat_sum = 0
                for a in strategy:
                    strat_sum += strategy[a]
                    if dart < strat_sum:
                        act = a
                        action, amount = derive_action(act, valid_actions, pot)
                        break
                next_history = deepcopy(history)
                next_history[round].append(act)

                new_game_state, new_events = self.emulator.apply_action(
                    game_state, action, amount
                )

                game_state = restore_game_state_fully(round_state, cards)
                # breakpoint()
                util = self.external_cfr(
                    new_game_state,
                    new_events,
                    next_history,
                    nodes_touched,
                    traversing_player_id,
                )
                # Update the strategy sum for the current node
                for a in infoset_bets:
                    self.nodes[infoset].strategy_sum[a] += strategy[a]

                return util
        return 0


def restore_game_state_fully(round_state, cards):
    game_state = restore_game_state(round_state)
    for player in game_state["table"].seats.players:
        hole_card = gen_cards(cards[player.uuid])
        game_state = attach_hole_card(game_state, player.uuid, hole_card)

    game_state["table"].deck.shuffle()
    return game_state


def get_hole_cards(player: Player):
    return [str(c) for c in player.hole_card]


def derive_action(a, valid_actions, pot_size):
    if a == "f":
        return ("fold", 0)
    elif a == "c":
        call_amount = next(
            action for action in valid_actions if action["action"] == "call"
        )["amount"]
        return ("call", call_amount)
    elif a == "a":
        allin_amount = next(
            action for action in valid_actions if action["action"] == "raise"
        )["amount"]["max"]
        return ("raise", allin_amount)
    else:
        raise_amount = a * pot_size
        return ("raise", raise_amount)


if __name__ == "__main__":
    k = HoldemCFR(1000)
    k.cfr_iterations_external()
