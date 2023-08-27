import numpy as np
from pypokerengine.api.emulator import Emulator
from collections import defaultdict
from typing import Dict, List, Union


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

        # Handle fold
        actions.append(0)

        # Extract call and raise actions
        call_action = next(
            action for action in valid_actions if action["action"] == "call"
        )
        raise_action = next(
            action for action in valid_actions if action["action"] == "raise"
        )

        # Handle call
        call_value = call_action["amount"] / pot_size
        if call_value not in actions:
            actions.append(call_value)

        # Handle raise based on your specified distribution
        specified_distribution = [0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0]

        for value in specified_distribution:
            raise_amount = value * pot_size
            if (
                raise_action["amount"]["min"]
                <= raise_amount
                <= raise_action["amount"]["max"]
                and value not in actions
            ):
                actions.append(value)

        # Append all-in action if it's not already in the list
        all_in = raise_action["amount"]["max"] / pot_size
        if all_in not in actions:
            actions.append(all_in)

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
            "uuid-1": {"name": "player1", "stack": 100},
            "uuid-2": {"name": "player2", "stack": 100},
        }

    def cfr_iterations_external(self):
        util = np.zeros(2)  # Utility initialization for both players

        # Loop through each iteration to train
        for t in range(1, self.iterations + 1):
            for i in range(2):  # For both players
                util[i] += self.external_cfr(0, i)

        print("Average game value: {}".format(util[0] / (self.iterations)))

        # Save strategy to a file
        with open("holdemstrat.txt", "w+") as f:
            for i in sorted(self.nodes):
                f.write("{}, {}\n".format(i, self.nodes[i].get_average_strategy()))
                print(i, self.nodes[i].get_average_strategy())

    def external_cfr(self, nodes_touched, traversing_player):
        initial_state = self.emulator.generate_initial_game_state(self.players_info)
        game_state, events = self.emulator.start_new_round(initial_state)
        valid_actions = events[-1]["valid_actions"]
        pot = events[-1]["round_state"]["pot"]["main"]["amount"]

        breakpoint()


if __name__ == "__main__":
    k = HoldemCFR(100)
    k.cfr_iterations_external()
    breakpoint()
