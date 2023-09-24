from pypokerengine.api.game import setup_config, start_poker
from kane.kane_player import Kane
from abel.abel_player import Abel

# import pypokerengine deck
from pypokerengine.engine.deck import Deck
from pypokerengine.utils.card_utils import gen_cheat_deck
from helper import find_winner

custom_deck = [
    "SA",
    "SK",
    "SQ",
    "SJ",
    "ST",
    "S9",
    "HA",
    "HK",
    "HQ",
    "HJ",
    "HT",
    "CT",
    "C9",
    "D9",
    "D8",
    "D7",
]

cheat_deck = gen_cheat_deck(custom_deck)


temp = []
for game_count in range(10):
    config = setup_config(max_round=1000, initial_stack=20000, small_blind_amount=50)
    config.register_player(name="kane", algorithm=Kane())
    config.register_player(name="abel", algorithm=Abel("holdemstrat.txt"))

    game_result = start_poker(config, verbose=0, cheat_deck=cheat_deck)

    winner, max_stack = find_winner(game_result["players"])

    # print who won the game
    print(
        "The winner of game {} is {} with stack {}.".format(
            game_count + 1, winner, max_stack
        )
    )

    temp.append(winner)

# # print how many games won by each player
print("The players won the following number of games:")
print({x: temp.count(x) for x in temp})
