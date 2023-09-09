from pypokerengine.players import BasePokerPlayer
from pypokerengine.utils.card_utils import gen_cards
from pypokerengine.engine.hand_evaluator import HandEvaluator
import random
from pypokerengine.engine.card import Card


NB_SIMULATION = 1000


class StrategicKane(BasePokerPlayer):
    def declare_action(self, valid_actions, hole_card, round_state):
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
        self, num_simulations, total_players, hole_cards, community_cards=None
    ):
        if not community_cards:
            community_cards = []
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


def setup_ai() -> StrategicKane:
    return StrategicKane()
