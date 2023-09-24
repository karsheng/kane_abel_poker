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
    return winner_name, max_stack
