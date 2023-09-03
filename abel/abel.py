from pypokerengine.players import BasePokerPlayer
from collections import defaultdict
import ast
import random


class Abel(BasePokerPlayer):
    def __init__(self, filepath):
        self.filepath = filepath
        self.strategies = defaultdict(int)

        with open(filepath, "r") as f:
            self.data = f.readlines()
            self._parse_strategy()

    def _parse_strategy(self):
        sep = ", defaultdict(<class 'int'>, "
        for d in self.data:
            splits = d.split(sep)
            infoset = splits[0]
            strategy_str = splits[1][:-2]

            # eval strategy_string to defaultdict
            strategy = defaultdict(int, ast.literal_eval(strategy_str))
            self.strategies[infoset] = strategy

    def get_strategy(self, infoset, valid_actions, pot):
        strategy = self.strategies[infoset]
        if strategy == 0:
            options = self.get_options_from_valid_actions(valid_actions, pot)
            n = len(options)
            strategy = {a: 1 / n for a in options}
        return strategy

    def generate_infoset(self, hole_card, round_state):
        stacks = self.starting_stacks.copy()

        community_card = round_state["community_card"]
        infoset = f"{hole_card}_{community_card}"
        action_histories = round_state["action_histories"]
        pot = 0
        history = [[], [], [], []]

        streets = ["preflop", "flop", "turn", "river"]
        action_mapper = {"FOLD": "f", "CALL": "c", "RAISE": "r"}

        for street in streets:
            if street in action_histories.keys():
                action_history = action_histories[street]
                if street == "preflop":
                    for action in action_history[:2]:
                        pot += action["amount"]
                    action_history = action_history[2:]
                for action in action_history:
                    if action["action"] in action_mapper.keys():
                        act = action_mapper[action["action"]]
                        player_uuid = action["uuid"]
                        if act == "r":
                            amount = action["amount"]
                            raise_act = self._get_closest_bet_action(
                                amount, pot, stacks[player_uuid]
                            )
                            history[streets.index(street)].append(raise_act)
                        else:
                            history[streets.index(street)].append(act)
                    stacks[player_uuid] -= action["amount"]
                    pot += action["amount"]

        infoset += f"_{history}"
        return infoset

    def _get_closest_bet_action(self, amount, pot, max_amount):
        def nearest_value(values, target):
            closest = None
            closest_diff = float("inf")

            for value in values:
                if isinstance(value, str):  # Skip string values during comparison
                    continue
                current_diff = abs(value - target)

                if current_diff < closest_diff:
                    closest_diff = current_diff
                    closest = value

            return closest

        all_bet_actions = [0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0]
        bet_to_pot = amount / pot

        if amount >= max_amount:
            return "a"

        return nearest_value(all_bet_actions, bet_to_pot)

    def get_options_from_valid_actions(self, valid_actions, pot):
        options = []
        for action in valid_actions:
            if action["action"] == "fold":
                options.append("f")
            elif action["action"] == "call":
                options.append("c")
            elif action["action"] == "raise":
                min_bet = action["amount"]["min"]
                max_bet = action["amount"]["max"]
                for i in [0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0]:
                    bet = i * pot
                    if bet >= min_bet and bet < max_bet:
                        options.append(i)
                options.append("a")
            else:
                options.append(action["action"])
        return options

    def generate_action_and_amount(self, infoset, pot, valid_actions):
        strategy = self.get_strategy(infoset, valid_actions, pot)
        strat_sum = 0
        dart = random.random()
        for a in strategy:
            strat_sum += strategy[a]
            if dart < strat_sum:
                act = a
                break
        if act == "f":
            action = "fold"
            amount = 0
        elif act == "c":
            action = "call"
            amount = valid_actions[1]["amount"]
        elif act == "a":
            action = "raise"
            amount = valid_actions[2]["amount"]["max"]
        else:
            action = "raise"
            amount = act * pot

        return action, amount

    def declare_action(self, valid_actions, hole_card, round_state):
        infoset = self.generate_infoset(hole_card, round_state)
        pot = round_state["pot"]["main"]["amount"]
        action, amount = self.generate_action_and_amount(infoset, pot, valid_actions)
        return action, amount

    def receive_game_start_message(self, game_info):
        self.nb_player = game_info["player_num"]

    def receive_round_start_message(self, round_count, hole_card, seats):
        self.starting_stacks = {seat["uuid"]: seat["stack"] for seat in seats}

    def receive_street_start_message(self, street, round_state):
        pass

    def receive_game_update_message(self, action, round_state):
        pass

    def receive_round_result_message(self, winners, hand_info, round_state):
        pass


def setup_ai():
    return Abel("holdemstrat.txt")
