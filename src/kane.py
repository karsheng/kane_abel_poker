from pypokerengine.players import BasePokerPlayer
from pypokerengine.utils.card_utils import gen_cards, estimate_hole_card_win_rate
import random

NB_SIMULATION = 1000


class Kane(BasePokerPlayer):
    def declare_action(self, valid_actions, hole_card, round_state):
        community_card = round_state["community_card"]
        win_rate = estimate_hole_card_win_rate(
            nb_simulation=NB_SIMULATION,
            nb_player=self.nb_player,
            hole_card=gen_cards(hole_card),
            community_card=gen_cards(community_card),
        )

        # Estimate villain's call frequency (this is very rudimentary and could be replaced by a better estimate)
        villain_call_frequency = 1  # random.uniform(0.5, 1)

        # Estimate the current pot
        current_pot = round_state["pot"]["main"]["amount"]

        # Calculate fold equity
        fold_equity = (1 - villain_call_frequency) * current_pot

        # Semi-bluff: If the win rate is low but there's high fold equity, consider raising
        if win_rate < 0.5 and fold_equity > 0.5 * current_pot:
            action = valid_actions[2]  # raise
            action["amount"] = action["amount"]["max"]

        # If the win rate is high, raise
        elif win_rate >= 0.8:
            action = valid_actions[2]  # raise
            action["amount"] = action["amount"]["max"]

        # Otherwise, call
        else:
            action = valid_actions[1]  # call

        return action["action"], action["amount"]

    def receive_game_start_message(self, game_info):
        self.nb_player = game_info["player_num"]

    def receive_round_start_message(self, round_count, hole_card, seats):
        pass

    def receive_street_start_message(self, street, round_state):
        pass

    def receive_game_update_message(self, action, round_state):
        pass

    def receive_round_result_message(self, winners, hand_info, round_state):
        pass


def setup_ai():
    return StrategicKane()
