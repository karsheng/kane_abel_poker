from typing import List, Dict, Union, Tuple
from pypokerengine.players import BasePokerPlayer
from collections import defaultdict
import ast
import random


class Abel(BasePokerPlayer):
    def __init__(self, filepath: str):
        """
        Initialize the Abel poker player using a given strategy file.

        Parameters
        ----------
        filepath : str
            Path to the strategy file.
        """
        self.filepath = filepath
        self.strategies = defaultdict(int)

        with open(filepath, "r") as f:
            self.data = f.readlines()
            self._parse_strategy()

    def _parse_strategy(self) -> None:
        """Parse the strategy file to extract and store the strategy information."""
        sep = ", defaultdict(<class 'int'>, "
        for d in self.data:
            splits = d.split(sep)
            infoset = splits[0]
            strategy_str = splits[1][:-2]

            # eval strategy_string to defaultdict
            strategy = defaultdict(int, ast.literal_eval(strategy_str))
            self.strategies[infoset] = strategy

    def get_strategy(
        self,
        infoset: str,
        valid_actions: List[Dict[str, Union[int, Dict[str, int]]]],
        pot: int,
    ) -> Dict[Union[str, float], float]:
        """Retrieve the strategy for a given infoset or generate a default one."""

        # Fetch the strategy corresponding to the provided infoset from the stored strategies.
        strategy = self.strategies[infoset]

        # If no strategy exists for the given infoset (strategy is 0), generate a default strategy.
        if strategy == 0:
            # Extract possible actions the player can take from the list of valid actions.
            options = self.get_options_from_valid_actions(valid_actions, pot)

            # Calculate the number of possible actions.
            n = len(options)

            # Generate a default strategy that assigns equal probability to each action.
            strategy = {a: 1 / n for a in options}

        # Return the fetched or generated strategy.
        return strategy

    def generate_infoset(self, hole_card: List[str], round_state: Dict) -> str:
        """Generate the information set string representing the current game state."""

        # Create a copy of the starting stacks of the players.
        stacks = self.starting_stacks.copy()

        # Retrieve the community cards from the round state.
        community_card = round_state["community_card"]
        # Sort the first three community cards, and concatenate the rest without sorting.
        sorted_community_card = sorted(community_card[:3]) + community_card[3:]
        # Start forming the infoset string with the sorted hole cards and sorted community cards.
        infoset = f"{sorted(hole_card)}_{sorted_community_card}"

        # Retrieve action histories for all streets from the round state.
        action_histories = round_state["action_histories"]
        pot = 0
        # Create a nested list to store action histories for each street.
        history = [[], [], [], []]

        # Define the four streets in a poker round.
        streets = ["preflop", "flop", "turn", "river"]
        # Map poker actions to their single character representations.
        action_mapper = {"FOLD": "f", "CALL": "c", "RAISE": "r"}

        # Loop through each street to process its action history.
        for street in streets:
            # Check if the street has an action history.
            if street in action_histories.keys():
                action_history = action_histories[street]

                # For preflop, add the amounts of the first two actions to the pot.
                if street == "preflop":
                    for action in action_history[:2]:
                        pot += action["amount"]
                    # Remove the first two actions from the action history.
                    action_history = action_history[2:]

                # Process each action in the action history of the current street.
                for action in action_history:
                    # Convert actions like FOLD, CALL, and RAISE to their single character representations.
                    if action["action"] in action_mapper.keys():
                        act = action_mapper[action["action"]]
                        player_uuid = action["uuid"]

                        # For a RAISE action, determine its closest standard action (e.g., 0.5x pot).
                        if act == "r":
                            amount = action["amount"]
                            raise_act = self._get_closest_bet_action(
                                amount, pot, stacks[player_uuid]
                            )
                            history[streets.index(street)].append(raise_act)
                        else:
                            # For non-raise actions, simply append their representations.
                            history[streets.index(street)].append(act)

                        # Update the stack of the player who took the action.
                        stacks[player_uuid] -= action["amount"]
                        # Update the current pot size.
                        pot += action["amount"]

        # Append the action histories of all streets to the infoset string.
        infoset += f"_{history}"

        # Return the complete infoset string.
        return infoset

    def _get_closest_bet_action(
        self, amount: float, pot: float, max_amount: float
    ) -> Union[str, float]:
        """Get the closest standardized bet action given a specific amount."""

        # Define an internal function to find the nearest value from a list to a target value.
        def nearest_value(values, target):
            # Initialize 'closest' to None and 'closest_diff' to positive infinity.
            closest = None
            closest_diff = float("inf")

            # Loop through the provided values.
            for value in values:
                # If the value is a string, skip the comparison (this is mainly for the "all-in" action).
                if isinstance(value, str):
                    continue

                # Calculate the difference between the current value and the target.
                current_diff = abs(value - target)

                # If the current difference is less than the previous closest difference,
                # update 'closest' and 'closest_diff'.
                if current_diff < closest_diff:
                    closest_diff = current_diff
                    closest = value

            # Return the value that is closest to the target.
            return closest

        # List of standardized bet sizes as fractions of the pot.
        all_bet_actions = [0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0]

        # Calculate the ratio of the amount to the pot size.
        bet_to_pot = amount / pot

        # If the bet amount is greater than or equal to the maximum allowed amount, return 'a' for "all-in".
        if amount >= max_amount:
            return "a"

        # Return the standardized bet size that is closest to the 'bet_to_pot' ratio.
        return nearest_value(all_bet_actions, bet_to_pot)

    def get_options_from_valid_actions(
        self, valid_actions: List[Dict[str, Union[int, Dict[str, int]]]], pot: int
    ) -> List[Union[str, float]]:
        """Extract possible betting options from the list of valid actions."""

        # Initialize the list to store possible betting options.
        options = []

        # Loop through each action in the list of valid actions.
        for action in valid_actions:
            # If the action is 'fold', append 'f' to the options list.
            if action["action"] == "fold":
                options.append("f")
            # If the action is 'call', append 'c' to the options list.
            elif action["action"] == "call":
                options.append("c")
            # If the action is 'raise':
            elif action["action"] == "raise":
                # Extract the minimum and maximum bet amounts.
                min_bet = action["amount"]["min"]
                max_bet = action["amount"]["max"]
                # Loop through the predefined betting ratios.
                for i in [0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0]:
                    # Calculate the actual bet amount based on the pot size.
                    bet = i * pot
                    # If the bet is within the allowed range, add it to the options.
                    if bet >= min_bet and bet < max_bet:
                        options.append(i)
                # Add 'a' (all-in) to the options after considering the raise ratios.
                options.append("a")
            else:
                # For any other action, append it directly to the options list.
                options.append(action["action"])
        # Return the list of possible betting options.
        return options

    def generate_action_and_amount(
        self,
        infoset: str,
        pot: int,
        valid_actions: List[Dict[str, Union[int, Dict[str, int]]]],
        round_state: Dict,
    ) -> Tuple[str, int]:
        """Generate the action and its amount based on the player's strategy."""

        # Get the strategy for the provided information set.
        strategy = self.get_strategy(infoset, valid_actions, pot)

        # Variables to determine the chosen action based on the strategy probabilities.
        strat_sum = 0
        dart = random.random()  # Random value between 0 and 1.

        # Determine the action based on where the random value falls within the strategy's cumulative probability.
        for a in strategy:
            strat_sum += strategy[a]
            if dart < strat_sum:
                act = a
                break

        # Map the chosen action 'act' to the actual action string and determine the corresponding amount.
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

        # If the action is fold, check some conditions where it might be better to call instead.
        if action == "fold":
            call_amount = valid_actions[1]["amount"]

            # If the call amount is zero, choose to call instead of fold.
            if call_amount == 0:
                action = "call"
                amount = 0

            # Additional conditions for the preflop stage.
            if round_state["street"] == "preflop":
                no_of_actions = len(round_state["action_histories"]["preflop"])
                # If the player is the big blind and the call amount is equal to the big blind amount, choose to call.
                if no_of_actions == 3 and call_amount == 2:
                    action = "call"
                    amount = call_amount

        return action, amount

    def declare_action(
        self,
        valid_actions: List[Dict[str, Union[int, Dict[str, int]]]],
        hole_card: List[str],
        round_state: Dict,
    ) -> Tuple[str, int]:
        """Declare the action to take given the current game state."""

        # Calculate the amount of the big blind based on the small blind amount.
        big_blind_amount = round_state["small_blind_amount"] * 2

        # Process the valid actions based on the big blind amount to get a standardized list of actions.
        valid_actions = self._process_valid_actions(valid_actions, big_blind_amount)

        # Generate the information set string that represents the current game state.
        infoset = self.generate_infoset(hole_card, round_state)

        # Extract the current pot amount.
        pot = round_state["pot"]["main"]["amount"]

        # Generate the best action and its corresponding amount based on the player's strategy.
        action, amount = self.generate_action_and_amount(
            infoset, pot, valid_actions, round_state
        )

        # Return the chosen action and its amount (cast to an integer).
        return action, int(amount)

    def _process_valid_actions(
        self,
        valid_actions: List[Dict[str, Union[int, Dict[str, int]]]],
        big_blind_amount: int,
    ) -> List[Dict[str, Union[int, Dict[str, int]]]]:
        """Process and adjust valid actions according to the big blind amount."""

        # Initialize an empty list to hold the processed actions.
        parsed_valid_actions = []

        # Iterate over each action in the valid_actions list.
        for action in valid_actions:
            # Check if the current action is a "raise".
            if action["action"] == "raise":
                # Check if the "amount" key of the action is an integer or float (i.e., not a dictionary).
                if isinstance(action["amount"], (int, float)):
                    # Store the current value of "amount" into the variable max_amount.
                    max_amount = action["amount"]

                    # Overwrite the "amount" key with an empty dictionary.
                    action["amount"] = {}

                    # Set the "min" key of the "amount" dictionary to the big_blind_amount.
                    action["amount"]["min"] = big_blind_amount

                    # Set the "max" key of the "amount" dictionary to max_amount.
                    action["amount"]["max"] = max_amount

            # Append the processed action to the parsed_valid_actions list.
            parsed_valid_actions.append(action)

        # Return the list of processed actions.
        return parsed_valid_actions

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


def setup_ai() -> Abel:
    return Abel("holdemstrat.txt")
