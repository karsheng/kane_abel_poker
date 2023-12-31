import webapp.engine_wrapper as Engine
import webapp.ai_generator as AG
from abel.abel_player import Abel, setup_ai as setup_abel
from kane.kane_player import Kane, setup_ai as setup_kane


class GameManager(object):
    def __init__(self):
        self.rule = None
        self.members_info = []
        self.player1s = []
        self.player2s = []
        self.engine = None
        self.ai_players = {}
        self.is_playing_poker = False
        self.latest_messages = []
        self.next_player_uuid = None
        self.round_hole_cards = {}
        self.abel: Abel = setup_abel()
        self.kane: Kane = setup_kane()
        self.current_recommendations = {}

    def define_rule(self, max_round, initial_stack, small_blind, ante, blind_structure):
        self.rule = Engine.gen_game_config(
            max_round, initial_stack, small_blind, ante, blind_structure
        )

    def join_ai_player1s(self, name, setup_script_path):
        ai_uuid = str(len(self.player1s))
        self.player1s.append(gen_ai_player_info(name, ai_uuid, setup_script_path))

    def join_ai_player2s(self, name, setup_script_path):
        ai_uuid = str(len(self.player2s) + len(self.player1s))
        self.player2s.append(gen_ai_player_info(name, ai_uuid, setup_script_path))

    def join_ai_player(self, name, setup_script_path):
        ai_uuid = str(len(self.members_info))
        self.members_info.append(gen_ai_player_info(name, ai_uuid, setup_script_path))

    def join_human_player(self, name, uuid):
        self.player2s.append(gen_human_player_info(name, uuid))

    def get_human_player_info(self, uuid):
        for info in self.members_info:
            if info["type"] == "human" and info["uuid"] == uuid:
                return info

    def remove_human_player_info(self, uuid):
        member_info = self.get_human_player_info(uuid)
        assert member_info
        self.members_info.remove(member_info)

    def start_game(self):
        assert self.rule and len(self.members_info) >= 2 and not self.is_playing_poker
        uuid_list = [member["uuid"] for member in self.members_info]
        name_list = [member["name"] for member in self.members_info]
        players_info = Engine.gen_players_info(uuid_list, name_list)
        self.ai_players = build_ai_players(self.members_info)
        self.engine = Engine.EngineWrapper()
        use_cheat_deck = False
        if "abel_player_1" in name_list or "abel_player_2" in name_list:
            use_cheat_deck = True
        self.latest_messages = self.engine.start_game(
            players_info, self.rule, use_cheat_deck
        )
        self.is_playing_poker = True
        self.next_player_uuid = fetch_next_player_uuid(self.latest_messages)

    def update_game(self, action, amount):
        assert (
            len(self.latest_messages) != 0
        )  # check that start_game has already called
        self.latest_messages = self.engine.update_game(action, amount)
        self.next_player_uuid = fetch_next_player_uuid(self.latest_messages)

    def get_current_hole_cards(self):
        players = self.engine.current_state["table"].seats.players
        current_hole_cards = {
            player.uuid: [str(card) for card in player.hole_card] for player in players
        }
        self.round_hole_cards = current_hole_cards
        return current_hole_cards

    def ask_action_to_ai_player(self, uuid):
        assert uuid in self.ai_players
        ai_player = self.ai_players[uuid]
        ask_uuid, ask_message = self.latest_messages[-1]
        assert ask_message["type"] == "ask" and uuid == ask_uuid
        return ai_player.declare_action(
            ask_message["message"]["valid_actions"],
            ask_message["message"]["hole_card"],
            ask_message["message"]["round_state"],
        )

    def get_recommendations(self, valid_actions, hole_card, round_state):
        self.current_recommendations["kane"] = self.kane.declare_action(
            valid_actions, hole_card, round_state
        )
        self.current_recommendations["abel"] = self.abel.declare_action(
            valid_actions, hole_card, round_state
        )

    def get_win_rate(self):
        return self.kane.win_rate

    def get_is_drawing(self):
        return self.kane.is_drawing

    def get_pot_odds(self):
        return self.kane.pot_odds

    def get_ev(self):
        return self.kane.ev


def fetch_next_player_uuid(new_messages):
    if not has_game_finished(new_messages):
        ask_uuid, ask_message = new_messages[-1]
        assert ask_message["type"] == "ask"
        return ask_uuid


def has_game_finished(new_messages):
    _uuid, last_message = new_messages[-1]
    return "game_result_message" == last_message["message"]["message_type"]


def build_ai_players(members_info):
    holder = {}
    for member in members_info:
        if member["type"] == "human":
            continue
        holder[member["uuid"]] = _build_ai_player(member["setup_script_path"])
    return holder


def _build_ai_player(setup_script_path):
    if not AG.healthcheck(setup_script_path, quiet=True):
        raise Exception("Failed to setup ai from [ %s ]" % setup_script_path)
    setup_method = AG._import_setup_method(setup_script_path)
    return setup_method()


def gen_ai_player_info(name, uuid, setup_script_path):
    info = _gen_base_player_info("ai", name, uuid)
    info["setup_script_path"] = setup_script_path
    return info


def gen_human_player_info(name, uuid):
    return _gen_base_player_info("human", name, uuid)


def _gen_base_player_info(player_type, name, uuid):
    return {"type": player_type, "name": name, "uuid": uuid}
