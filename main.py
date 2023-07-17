from pypokerengine.api.game import setup_config, start_poker
from src.fish_player import FishPlayer
from src.prudent_kane import PrudentKane
from src.strategic_kane import StrategicKane
from src.kane import Kane


def find_winner(players):
    # Initialize variables to hold the name and stack size of the player with the highest stack
    max_stack = 0
    winner_name = None

    # Iterate over the list of players
    for player in players:
        # Check if the current player's stack size is greater than the current maximum
        if player["stack"] > max_stack:
            # If so, update max_stack and winner_name
            max_stack = player["stack"]
            winner_name = player["name"]

    # Return the name of the player with the highest stack
    return winner_name


temp = []
for game_count in range(1):
    config = setup_config(max_round=10, initial_stack=10000, small_blind_amount=5)
    config.register_player(name="fish_player", algorithm=FishPlayer())
    # config.register_player(name="prudent_player", algorithm=PrudentKane())
    config.register_player(name="strategic_kane", algorithm=StrategicKane())
    # config.register_player(name="kane", algorithm=Kane())
    game_result = start_poker(config, verbose=2)

    winner = find_winner(game_result["players"])

    # print who won the game
    print("The winner of game {} is {}.".format(game_count + 1, winner))

    temp.append(winner)

# # print how many games won by each player
# print("The players won the following number of games:")
# print({x: temp.count(x) for x in temp})
