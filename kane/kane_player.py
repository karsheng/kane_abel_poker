from pypokerengine.players import BasePokerPlayer
from pypokerengine.utils.card_utils import gen_cards
from pypokerengine.engine.hand_evaluator import HandEvaluator
import random
from typing import List, Optional
from pypokerengine.engine.card import Card


NB_SIMULATION = 1000


class Kane(BasePokerPlayer):
    """
    A poker player AI called Kane.

    Attributes
    ----------
    _win_rate : float
        The winning rate of the player.
    _is_drawing : bool
        Indicates whether the player is drawing.
    pot_odds : float
        The odds of the pot.
    ev : float
        Expected value.
    """

    def __init__(self):
        self._win_rate = None
        self._is_drawing = None
        self.pot_odds = None
        self.ev = None

    @property
    def win_rate(self) -> float:
        """Returns the player's win rate."""
        return self._win_rate

    @property
    def is_drawing(self) -> bool:
        """Returns whether the player is drawing."""
        return self._is_drawing

    def declare_action(
        self, valid_actions: List[dict], hole_card: List[str], round_state: dict
    ) -> (str, int):
        """
        Decide an action based on win rate, drawing potential, and game state.

        Parameters
        ----------
        valid_actions : list of dict
            Available actions.
        hole_card : list of str
            Player's hole cards.
        round_state : dict
            Current round state.

        Returns
        -------
        tuple
            Action and amount.
        """
        # Estimate the win rate
        win_rate = self.calculate_win_probability(
            num_simulations=1000,
            total_players=self.nb_player,
            hole_cards=hole_card,
            community_cards=round_state["community_card"],
        )

        # Semi-bluffing logic
        is_drawing = self.has_drawing_potential(
            hole_card, round_state["community_card"]
        )
        semi_bluff_chance = random.uniform(0, 1)

        # Decide action based on win rate and drawing potential
        # Details provided as inline comments within the logic

        # Raise scenario
        if win_rate >= 0.8:
            action = valid_actions[2]  # raise
            min_bet = action["amount"]["min"]
            max_bet = action["amount"]["max"]
            action["amount"] = max_bet

        # Call scenario
        elif (
            win_rate >= 0.5
            and win_rate < 0.8
            or (is_drawing and semi_bluff_chance > 0.8)
        ):
            action = valid_actions[1]  # call

        # Fold or call in special scenarios
        else:
            if valid_actions[1]["amount"] == 0:
                action = valid_actions[1]
            elif (
                round_state["street"] == "preflop"
                and valid_actions[1]["amount"] == round_state["small_blind_amount"] * 2
            ):
                action = valid_actions[1]
            else:
                action = valid_actions[0]  # fold

        # Update internal states for player's knowledge
        self._win_rate = win_rate
        self._is_drawing = is_drawing
        pot = round_state["pot"]["main"]["amount"]
        call_amount = valid_actions[1]["amount"]
        self.pot_odds = call_amount / (pot + call_amount)
        self.ev = win_rate * (pot + call_amount) - (1 - win_rate) * call_amount

        return action["action"], int(action["amount"])

    def calculate_win_probability(
        self,
        num_simulations: int,
        total_players: int,
        hole_cards: List[str],
        community_cards: Optional[List[str]] = None,
    ) -> float:
        """
        Estimate the winning probability by running Monte Carlo simulations.

        Parameters
        ----------
        num_simulations : int
            Number of simulations to be run to estimate win probability.
        total_players : int
            Total number of players participating in the game.
        hole_cards : list of str
            The player's hole cards.
        community_cards : list of str, optional
            Cards available on the board. If None, it's assumed no community cards are available.

        Returns
        -------
        float
            Winning probability estimated between 0 and 1.
        """
        if not community_cards:
            community_cards = []

        # Convert string representations of cards to actual card objects
        hole_cards = gen_cards(hole_cards)
        community_cards = gen_cards(community_cards)

        # Calculate victories using Monte Carlo simulation
        victories = sum(
            [
                self.monte_carlo_sim(total_players, hole_cards, community_cards)
                for _ in range(num_simulations)
            ]
        )
        return 1.0 * victories / num_simulations

    def monte_carlo_sim(
        self, total_players: int, hole_cards: List[str], community_cards: List[str]
    ) -> int:
        """
        Run a single Monte Carlo simulation to check if player's hand wins.

        Parameters
        ----------
        total_players : int
            Total number of players participating in the game.
        hole_cards : list of str
            The player's hole cards.
        community_cards : list of str
            Cards available on the board.

        Returns
        -------
        int
            1 if the player's hand is winning in this simulation, 0 otherwise.
        """
        # Complete the community cards for simulation if they are less than 5
        community_cards = self._complete_community_cards(
            community_cards, already_used=hole_cards + community_cards
        )

        # Get remaining cards in the deck after accounting for player's and community cards
        remaining_cards = self._get_remaining_cards(
            (total_players - 1) * 2, hole_cards + community_cards
        )

        # Generate opponents' hole cards for the simulation
        opponents_cards = [
            remaining_cards[2 * i : 2 * i + 2] for i in range(total_players - 1)
        ]

        # Evaluate hand strength for opponents
        opponents_points = [
            HandEvaluator.eval_hand(cards, community_cards) for cards in opponents_cards
        ]

        # Evaluate hand strength for the player
        my_points = HandEvaluator.eval_hand(hole_cards, community_cards)
        return 1 if my_points >= max(opponents_points) else 0

    def _complete_community_cards(
        self, current_cards: List[str], already_used: List[str]
    ) -> List[str]:
        """
        Complete the community cards to reach 5 cards if they are less.

        Parameters
        ----------
        current_cards : list of str
            Current available community cards.
        already_used : list of str
            Cards which are already used (including player's hole cards and community cards).

        Returns
        -------
        list of str
            Completed community cards.
        """
        required_cards = 5 - len(current_cards)
        return current_cards + self._get_remaining_cards(required_cards, already_used)

    def _get_remaining_cards(
        self, num_cards: int, already_used: List[str]
    ) -> List[str]:
        """
        Fetch the specified number of cards that haven't been used yet from the deck.

        Parameters
        ----------
        num_cards : int
            Number of cards to fetch from the remaining deck.
        already_used : list of str
            List of cards that are already in play and shouldn't be reused.

        Returns
        -------
        list of str
            List of cards fetched from the remaining deck.
        """
        # Convert cards to their respective IDs
        used_ids = [card.to_id() for card in already_used]

        # List all available card IDs that haven't been used
        available = [card_id for card_id in range(1, 53) if card_id not in used_ids]

        # Randomly select the required number of cards from the available cards
        selected = random.sample(available, num_cards)

        # Convert the selected card IDs back to card objects
        return [Card.from_id(card_id) for card_id in selected]

    def has_drawing_potential(
        self, hole_cards: List[str], community_cards: List[str]
    ) -> bool:
        """
        Determine if the given set of cards has potential for a draw.

        Parameters
        ----------
        hole_cards : list of str
            The player's hole cards.
        community_cards : list of str
            The current community cards on the table.

        Returns
        -------
        bool
            True if there is a drawing potential, False otherwise.
        """
        # Combine hole and community cards and convert them to card objects
        all_cards = gen_cards(hole_cards + community_cards)

        # Extract ranks and suits for analysis
        ranks = [card.rank for card in all_cards]
        suits = [card.suit for card in all_cards]

        # If we're already at the river round, there's no drawing potential
        if len(all_cards) == 7:
            return False

        # Check if there's potential for a flush
        if self.has_flush_draw(suits):
            return True

        # Check if there's potential for a straight
        if self.has_straight_draw(ranks):
            return True

        return False

    def has_flush_draw(self, suits: List[str]) -> bool:
        """
        Determine if there's potential for a flush given the card suits.

        Parameters
        ----------
        suits : list of str
            List of suits of the cards to be analyzed.

        Returns
        -------
        bool
            True if there's a flush draw potential, False otherwise.
        """
        # Check if any suit appears exactly 4 times, indicating a flush draw
        for suit in set(suits):
            if suits.count(suit) == 4:
                return True
        return False

    def has_straight_draw(self, ranks: List[int]) -> bool:
        """
        Determine if there's potential for a straight given the card ranks.

        Parameters
        ----------
        ranks : list of int
            List of ranks of the cards to be analyzed.

        Returns
        -------
        bool
            True if there's a straight draw potential, False otherwise.
        """
        # Ensure that ranks are unique and sorted for analysis
        ranks = sorted(set(ranks))

        # Check for open-ended straight draw potential
        for i in range(len(ranks) - 3):
            consecutive_diff = ranks[i + 3] - ranks[i]
            if consecutive_diff == 3:
                return True

        # Check for gutshot straight draw potential
        for i in range(len(ranks) - 3):
            if ranks[i + 3] - ranks[i] == 4:
                return True
        return False

    def receive_game_start_message(self, game_info):
        pass

    def receive_round_start_message(self, round_count, hole_card, seats):
        self.nb_player = len(seats)

    def receive_street_start_message(self, street, round_state):
        pass

    def receive_game_update_message(self, action, round_state):
        pass

    def receive_round_result_message(self, winners, hand_info, round_state):
        pass


def setup_ai() -> Kane:
    return Kane()
