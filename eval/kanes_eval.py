from pypokerengine.api.game import setup_config, start_poker
from kane.fish_player import FishPlayer
from kane.prudent_kane import PrudentKane
from kane.strategic_kane import StrategicKane
from kane.kane_player import Kane
from helper import find_winner
import pandas as pd
from itertools import combinations

players = {
    "fish_player": FishPlayer,
    "prudent_kane": PrudentKane,
    "strategic_kane": StrategicKane,
    "kane": Kane,
}


players_combo = list(combinations(players.keys(), 2))


def calculate_pair_win_rates(df):
    # First, calculate the win rate of player1 vs player2
    total_matches = df.groupby(["player1", "player2"]).size()
    wins = df[df["player1"] == df["winner"]].groupby(["player1", "player2"]).size()
    win_rate = (wins / total_matches).fillna(0).unstack(fill_value=0)

    # Then, calculate the win rate of player2 vs player1 and subtract it from 1
    # (Because if player1 has a win rate of 0.67 vs player2, then player2 has a win rate of 0.33 vs player1)
    total_matches_2 = df.groupby(["player2", "player1"]).size()
    wins_2 = df[df["player2"] == df["winner"]].groupby(["player2", "player1"]).size()
    win_rate_2 = (wins_2 / total_matches_2).fillna(0).unstack(fill_value=0)

    # Now, combine both win rates
    combined_win_rate = win_rate.add(win_rate_2, fill_value=0)

    # For the diagonal, where player1 == player2, fill with NaN
    for player in combined_win_rate.columns:
        combined_win_rate.loc[player, player] = float("nan")

    return combined_win_rate


results = []
for player1, player2 in players_combo:
    print(f"{player1} vs. {player2}")
    for game_count in range(1000):
        config = setup_config(
            max_round=1000, initial_stack=20000, small_blind_amount=50
        )
        config.register_player(name=player1, algorithm=players[player1]())
        config.register_player(name=player2, algorithm=players[player2]())

        game_result = start_poker(config, verbose=0)

        winner, max_stack = find_winner(game_result["players"])

        # print who won the game
        print(
            "The winner of game {} is {} with stack {}.".format(
                game_count + 1, winner, max_stack
            )
        )

        results.append(
            {
                "player1": player1,
                "player2": player2,
                "winner": winner,
            }
        )


# tabulate results
df = pd.DataFrame(results)
win_rates = calculate_pair_win_rates(df)


# save results
ordered_names = list(players.keys())
win_rates = win_rates.reindex(ordered_names, axis=0).reindex(ordered_names, axis=1)
win_rates = win_rates.fillna("-")
win_rates.to_csv("eval/results/kanes_win_rates.csv", index=True)
