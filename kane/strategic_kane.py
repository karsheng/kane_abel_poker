from pypokerengine.players import BasePokerPlayer
from pypokerengine.utils.card_utils import gen_cards, estimate_hole_card_win_rate

NB_SIMULATION = 1000


class StrategicKane(BasePokerPlayer):
    def declare_action(self, valid_actions, hole_card, round_state):
        # Estimate the win rate
        win_rate = estimate_hole_card_win_rate(
            nb_simulation=1000,
            nb_player=self.nb_player,
            hole_card=gen_cards(hole_card),
            community_card=gen_cards(round_state["community_card"]),
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
