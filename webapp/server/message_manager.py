import time
import logging

import tornado.escape


def alert_server_restart(handler, uuid, sockets):
    soc = _find_socket_by_uuid(sockets, uuid)
    soc.write_message(_gen_alert_server_restart_message(handler))


def alert_players_no(handler, uuid, sockets):
    soc = _find_socket_by_uuid(sockets, uuid)
    soc.write_message(
        {"message_type": "alert_players_no", "message": "Not enough players"}
    )


def _gen_alert_server_restart_message(handler):
    message = (
        "Server has already run. Please restart the server to play the game again."
    )
    return {"message_type": "alert_restart_server", "message": message}


def broadcast_config_update(handler, game_manager, sockets):
    for soc in sockets:
        try:
            soc.write_message(
                _gen_config_update_message(handler, game_manager, soc.uuid)
            )
        except:
            logging.error("Error sending message", exc_info=True)


def _gen_config_update_message(handler, game_manager, uuid):
    registered = game_manager.get_human_player_info(uuid)
    html_str = handler.render_string(
        "game_config.html", config=game_manager, registered=registered
    )
    html = tornado.escape.to_basestring(html_str)

    return {"message_type": "config_update", "html": html, "registered": registered}


def broadcast_start_game(handler, game_manager, sockets):
    # broadcast message to browser bia sockets
    for soc in sockets:
        try:
            soc.write_message(_gen_start_game_message(handler, game_manager, soc.uuid))
        except:
            logging.error("Error sending message", exc_info=True)
    # broadcast message to ai by invoking proper callback method
    game_info = _gen_game_info(game_manager)
    for uuid, player in game_manager.ai_players.items():
        player.receive_game_start_message(game_info)
        player.set_uuid(uuid)


def _gen_game_info(game_manager):
    seats = game_manager.latest_messages[0][1]["message"]["seats"]
    copy_seats = [{k: v for k, v in player.items()} for player in seats]
    for player in copy_seats:
        player["stack"] = game_manager.rule["initial_stack"]
    player_num = len(seats)
    rule = {k: v for k, v in game_manager.rule.items()}
    rule["small_blind_amount"] = rule.pop("small_blind")
    return {
        "seats": copy_seats,
        "player_num": player_num,
        "rule": rule,
    }


def _gen_start_game_message(handler, game_manager, uuid):
    registered = game_manager.get_human_player_info(uuid)
    html_str = handler.render_string(
        "poker_game.html", config=game_manager, registered=registered
    )
    html = tornado.escape.to_basestring(html_str)

    return {"message_type": "start_game", "html": html}


def broadcast_update_game(handler, game_manager, sockets, mode="moderate"):
    for destination, update in game_manager.latest_messages:
        for uuid in _parse_destination(destination, game_manager, sockets):
            if len(str(uuid)) <= 2:
                ai_player = game_manager.ai_players[uuid]
                _broadcast_message_to_ai(ai_player, update)
            else:
                socket = _find_socket_by_uuid(sockets, uuid)
                if update["message"]["message_type"] == "street_start_message":
                    if update["message"]["round_state"]["street"] == "preflop":
                        game_manager.get_current_hole_cards()

                if update["message"]["message_type"] == "round_start_message":
                    round_count = update["message"]["round_count"]
                    hole_card = update["message"]["hole_card"]
                    seats = update["message"]["seats"]

                    game_manager.abel.receive_round_start_message(
                        round_count, hole_card, seats
                    )

                    game_manager.kane.receive_round_start_message(
                        round_count, hole_card, seats
                    )

                if update["message"]["message_type"] == "ask_message":
                    valid_actions = update["message"]["valid_actions"]
                    round_state = update["message"]["round_state"]
                    hole_card = update["message"]["hole_card"]

                    game_manager.get_recommendations(
                        valid_actions, hole_card, round_state
                    )
                    update["recommendations"] = game_manager.current_recommendations
                    update["win_rate"] = game_manager.get_win_rate()
                    update["is_drawing"] = game_manager.get_is_drawing()
                    update["pot_odds"] = game_manager.get_pot_odds()
                    update["ev"] = game_manager.get_ev()

                update["current_hole_cards"] = game_manager.round_hole_cards

                message = _gen_game_update_message(handler, update)
                try:
                    socket.write_message(message)
                except:
                    logging.error("Error sending message", exc_info=True)
                time.sleep(_calc_wait_interval(mode, update))


def _parse_destination(destination, game_manager, sockets):
    if destination == -1:
        return [soc.uuid for soc in sockets] + list(game_manager.ai_players.keys())
    else:
        return [destination]


def _find_socket_by_uuid(sockets, uuid):
    target = [sock for sock in sockets if sock.uuid == uuid]
    assert len(target) == 1
    return target[0]


def _gen_game_update_message(handler, message):
    message_type = message["message"]["message_type"]
    if "round_start_message" == message_type:
        round_count = message["message"]["round_count"]
        hole_card = message["message"]["hole_card"]
        event_html_str = handler.render_string(
            "event_round_start.html", round_count=round_count, hole_card=hole_card
        )
        content = {
            "update_type": message_type,
            "event_html": tornado.escape.to_basestring(event_html_str),
        }
    elif "street_start_message" == message_type:
        round_state = message["message"]["round_state"]
        street = message["message"]["street"]
        table_html_str = handler.render_string(
            "round_state.html", round_state=round_state
        )
        event_html_str = handler.render_string("event_street_start.html", street=street)
        content = {
            "update_type": message_type,
            "table_html": tornado.escape.to_basestring(table_html_str),
            "event_html": tornado.escape.to_basestring(event_html_str),
        }
    elif "game_update_message" == message_type:
        round_state = message["message"]["round_state"]
        action = message["message"]["action"]
        action_histories = message["message"]["action_histories"]
        table_html_str = handler.render_string(
            "round_state.html", round_state=round_state
        )
        event_html_str = handler.render_string(
            "event_update_game.html", action=action, round_state=round_state
        )
        content = {
            "update_type": message_type,
            "table_html": tornado.escape.to_basestring(table_html_str),
            "event_html": tornado.escape.to_basestring(event_html_str),
        }
    elif "round_result_message" == message_type:
        round_state = message["message"]["round_state"]
        hand_info = message["message"]["hand_info"]
        winners = message["message"]["winners"]
        round_count = message["message"]["round_count"]
        hole_cards = message["current_hole_cards"]

        table_html_str = handler.render_string(
            "round_state.html", round_state=round_state
        )
        event_html_str = handler.render_string(
            "event_round_result.html",
            round_state=round_state,
            hand_info=hand_info,
            winners=winners,
            round_count=round_count,
            hole_cards=hole_cards,
        )
        content = {
            "update_type": message_type,
            "table_html": tornado.escape.to_basestring(table_html_str),
            "event_html": tornado.escape.to_basestring(event_html_str),
        }
    elif "game_result_message" == message_type:
        game_info = message["message"]["game_information"]
        event_html_str = handler.render_string(
            "event_game_result.html", game_information=game_info
        )
        content = {
            "update_type": message_type,
            "event_html": tornado.escape.to_basestring(event_html_str),
        }
    elif "ask_message" == message_type:
        round_state = message["message"]["round_state"]
        hole_card = message["message"]["hole_card"]
        valid_actions = message["message"]["valid_actions"]
        action_histories = message["message"]["action_histories"]
        recommendations = message["recommendations"]
        win_rate = int(message["win_rate"] * 100)
        is_drawing = message["is_drawing"]
        pot_odds = int(message["pot_odds"] * 100)
        ev = int(message["ev"])

        table_html_str = handler.render_string(
            "round_state.html", round_state=round_state
        )
        event_html_str = handler.render_string(
            "event_ask_action.html",
            hole_card=hole_card,
            valid_actions=valid_actions,
            action_histories=action_histories,
        )

        recommendations_html_str = handler.render_string(
            "recommendations.html",
            recommendations=recommendations,
            win_rate=win_rate,
            is_drawing=is_drawing,
            pot_odds=pot_odds,
            ev=ev,
        )
        content = {
            "update_type": message_type,
            "table_html": tornado.escape.to_basestring(table_html_str),
            "event_html": tornado.escape.to_basestring(event_html_str),
            "rec_html": tornado.escape.to_basestring(recommendations_html_str),
        }
    else:
        raise Exception("Unexpected message received : %r" % message)

    return {"message_type": "update_game", "content": content}


def _broadcast_message_to_ai(ai_player, message):
    message_type = message["message"]["message_type"]
    if "round_start_message" == message_type:
        round_count = message["message"]["round_count"]
        hole_card = message["message"]["hole_card"]
        seats = message["message"]["seats"]
        ai_player.receive_round_start_message(round_count, hole_card, seats)
    elif "street_start_message" == message_type:
        street = message["message"]["street"]
        round_state = message["message"]["round_state"]
        ai_player.receive_street_start_message(street, round_state)
    elif "game_update_message" == message_type:
        action = message["message"]["action"]
        round_state = message["message"]["round_state"]
        ai_player.receive_game_update_message(action, round_state)
    elif "round_result_message" == message_type:
        winners = message["message"]["winners"]
        round_state = message["message"]["round_state"]
        hand_info = message["message"]["hand_info"]
        ai_player.receive_round_result_message(winners, hand_info, round_state)
    elif "game_result_message" == message_type:
        pass  # ai does not handle game result
    elif "ask_message" == message_type:
        pass  # ask message handling is done in global_game_config.ask_action_to_ai
    else:
        raise Exception("Unexpected message received : %r" % message)


def _calc_wait_interval(mode, update):
    message_type = update["message"]["message_type"]
    if "dev" == mode:
        return 0
    elif "slow" == mode:
        return SLOW_WAIT_INTERVAL[message_type]
    elif "moderate" == mode:
        return MODERATE_WAIT_INTERVAL[message_type]
    elif "fast" == mode:
        return FAST_WAIT_INTERVAL[message_type]
    else:
        raise Exception("Unexpected mode received [ %s ]" % mode)


SLOW_WAIT_INTERVAL = {  # TODO
    "round_start_message": 0,
    "street_start_message": 0,
    "ask_message": 0,
    "game_update_message": 0,
    "round_result_message": 0,
    "game_result_message": 0,
}

MODERATE_WAIT_INTERVAL = {
    "round_start_message": 3,
    "street_start_message": 2,
    "ask_message": 0,
    "game_update_message": 2,
    "round_result_message": 10,
    "game_result_message": 0,
}

FAST_WAIT_INTERVAL = {
    "round_start_message": 1,
    "street_start_message": 0.5,
    "ask_message": 0,
    "game_update_message": 0.5,
    "round_result_message": 3,
    "game_result_message": 0,
}
