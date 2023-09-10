from pypokerengine.players import BasePokerPlayer
from pypokerengine.utils.card_utils import gen_cards
from pypokerengine.engine.hand_evaluator import HandEvaluator
import random
from typing import List
from pypokerengine.engine.card import Card


NB_SIMULATION = 1000


class Kane(BasePokerPlayer):
    def __init__(self):
        self._win_rate = None
        self._is_drawing = None

    @property
    def win_rate(self):
        return self._win_rate

    @property
    def is_drawing(self):
        return self._is_drawing

    def declare_action(self, valid_actions, hole_card, round_state):
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

        # If the win rate is large enough, raise; otherwise, call
        if win_rate >= 0.8:
            action = valid_actions[2]  # raise
            min_bet = action["amount"]["min"]
            max_bet = action["amount"]["max"]
            action["amount"] = max_bet
        elif (
            win_rate >= 0.5
            and win_rate < 0.8
            or (is_drawing and semi_bluff_chance > 0.8)
        ):
            action = valid_actions[1]  # call
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

        self._win_rate = win_rate
        self._is_drawing = is_drawing

        return action["action"], int(action["amount"])

    def calculate_win_probability(
        self, num_simulations, total_players, hole_cards, community_cards=None
    ):
        if not community_cards:
            community_cards = []

        hole_cards = gen_cards(hole_cards)
        community_cards = gen_cards(community_cards)

        victories = sum(
            [
                self.monte_carlo_sim(total_players, hole_cards, community_cards)
                for _ in range(num_simulations)
            ]
        )
        return 1.0 * victories / num_simulations

    def monte_carlo_sim(self, total_players, hole_cards, community_cards):
        community_cards = self._complete_community_cards(
            community_cards, already_used=hole_cards + community_cards
        )
        remaining_cards = self._get_remaining_cards(
            (total_players - 1) * 2, hole_cards + community_cards
        )
        opponents_cards = [
            remaining_cards[2 * i : 2 * i + 2] for i in range(total_players - 1)
        ]
        opponents_points = [
            HandEvaluator.eval_hand(cards, community_cards) for cards in opponents_cards
        ]
        my_points = HandEvaluator.eval_hand(hole_cards, community_cards)
        return 1 if my_points >= max(opponents_points) else 0

    def _complete_community_cards(self, current_cards, already_used):
        required_cards = 5 - len(current_cards)
        return current_cards + self._get_remaining_cards(required_cards, already_used)

    def _get_remaining_cards(self, num_cards, already_used):
        used_ids = [card.to_id() for card in already_used]
        available = [card_id for card_id in range(1, 53) if card_id not in used_ids]
        selected = random.sample(available, num_cards)
        return [Card.from_id(card_id) for card_id in selected]

    def has_drawing_potential(self, hole_cards, community_cards):
        all_cards = gen_cards(hole_cards + community_cards)
        ranks = [card.rank for card in all_cards]
        suits = [card.suit for card in all_cards]

        # Already at river - no drawing potential
        if len(all_cards) == 7:
            return False

        # Check for flush draw
        if self.has_flush_draw(suits):
            return True

        # Check for straight draw (open-ended or gutshot)
        if self.has_straight_draw(ranks):
            return True

        return False

    def has_flush_draw(self, suits: List[str]):
        for suit in set(suits):
            if suits.count(suit) == 4:
                return True
        return False

    def has_straight_draw(self, ranks):
        """Check if given ranks have a straight draw."""
        # Ensure ranks are unique and sorted
        ranks = sorted(set(ranks))

        # Check for open-ended straight draw
        for i in range(len(ranks) - 3):
            consecutive_diff = ranks[i + 3] - ranks[i]
            if consecutive_diff == 3:
                return True

        # Check for gutshot straight draw
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
