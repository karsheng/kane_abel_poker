from typing import List, Tuple, Union, Optional, Dict
from pypokerengine.players import BasePokerPlayer
from pypokerengine.utils.card_utils import gen_cards
from pypokerengine.engine.hand_evaluator import HandEvaluator
from pypokerengine.engine.card import Card
import random

NB_SIMULATION = 1000


class StrategicKane(BasePokerPlayer):
    def declare_action(
        self,
        valid_actions: List[Dict[str, Union[int, Dict[str, int]]]],
        hole_card: List[str],
        round_state: Dict,
    ) -> Tuple[str, int]:
        """
        Declare the action to take given the current game state.

        Parameters
        ----------
        valid_actions : list
            A list of valid actions.
        hole_card : list
            List of hole cards.
        round_state : dict
            Information about the current round.

        Returns
        -------
        tuple
            The selected action and its amount.
        """

        # Estimate the win rate
        win_rate = self.calculate_win_probability(
            num_simulations=1000,
            total_players=self.nb_player,
            hole_cards=gen_cards(hole_card),
            community_cards=gen_cards(round_state["community_card"]),
        )

        # If the win rate is large enough, raise; otherwise, call
        if win_rate >= 0.8:
            action = valid_actions[2]  # raise
            action["amount"] = action["amount"]["max"]
        elif win_rate >= 0.5 and win_rate < 0.8:
            action = valid_actions[1]  # call
        else:
            if valid_actions[1]["amount"] == 0:
                action = valid_actions[1]
            else:
                action = valid_actions[0]  # fold

        return action["action"], action["amount"]

    def calculate_win_probability(
        self,
        num_simulations: int,
        total_players: int,
        hole_cards: List[Card],
        community_cards: Optional[List[Card]] = None,
    ) -> float:
        """
        Calculate the win probability.

        Parameters
        ----------
        num_simulations : int
            Number of simulations to estimate win probability.
        total_players : int
            Total number of players in the game.
        hole_cards : list
            Player's hole cards.
        community_cards : list, optional
            Known community cards, by default None.

        Returns
        -------
        float
            Estimated win probability.
        """

        if not community_cards:
            community_cards = []

        victories = sum(
            [
                self.monte_carlo_sim(total_players, hole_cards, community_cards)
                for _ in range(num_simulations)
            ]
        )
        return 1.0 * victories / num_simulations

    def monte_carlo_sim(
        self, total_players: int, hole_cards: List[Card], community_cards: List[Card]
    ) -> int:
        """
        Perform a Monte Carlo simulation to estimate win probability.

        Parameters
        ----------
        total_players : int
            Total number of players in the game.
        hole_cards : list
            Player's hole cards.
        community_cards : list
            Known community cards.

        Returns
        -------
        int
            1 if player wins, 0 otherwise.
        """

        # Complete community cards if less than 5
        community_cards = self._complete_community_cards(
            community_cards, already_used=hole_cards + community_cards
        )

        # Get remaining cards for opponents
        remaining_cards = self._get_remaining_cards(
            (total_players - 1) * 2, hole_cards + community_cards
        )

        # Distribute hole cards to opponents
        opponents_cards = [
            remaining_cards[2 * i : 2 * i + 2] for i in range(total_players - 1)
        ]

        # Calculate hand strength for all opponents
        opponents_points = [
            HandEvaluator.eval_hand(cards, community_cards) for cards in opponents_cards
        ]

        # Calculate hand strength for player
        my_points = HandEvaluator.eval_hand(hole_cards, community_cards)

        return 1 if my_points >= max(opponents_points) else 0

    def _complete_community_cards(
        self, current_cards: List[Card], already_used: List[Card]
    ) -> List[Card]:
        required_cards = 5 - len(current_cards)
        return current_cards + self._get_remaining_cards(required_cards, already_used)

    def _get_remaining_cards(
        self, num_cards: int, already_used: List[Card]
    ) -> List[Card]:
        # Convert cards to IDs
        used_ids = [card.to_id() for card in already_used]

        # Get available card IDs
        available = [card_id for card_id in range(1, 53) if card_id not in used_ids]

        # Randomly select the required number of cards
        selected = random.sample(available, num_cards)

        # Convert selected card IDs back to Card objects
        return [Card.from_id(card_id) for card_id in selected]

    def receive_game_start_message(self, game_info: Dict):
        pass

    def receive_round_start_message(
        self, round_count: int, hole_card: List[str], seats: List[Dict]
    ):
        self.nb_player = len(seats)

    def receive_street_start_message(self, street: str, round_state: Dict):
        pass

    def receive_game_update_message(self, action: Dict, round_state: Dict):
        pass

    def receive_round_result_message(self, winners, hand_info, round_state):
        pass


def setup_ai() -> StrategicKane:
    return StrategicKane()
