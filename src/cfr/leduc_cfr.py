import numpy as np
import random
from collections import defaultdict
from typing import List, Dict, DefaultDict, Union, Any


class Node:
    def __init__(self, bet_options):
        # Initialize node with the available bet options
        self.num_actions = len(bet_options)

        # Regret sum keeps track of cumulative regrets for each action over time
        self.regret_sum = defaultdict(int)

        # Current strategy for the node given the current regret sums
        self.strategy = defaultdict(int)

        # Cumulative strategy over time; used to calculate the average strategy
        self.strategy_sum = defaultdict(int)

        # Available bet options for the current node (e.g. [check, bet, fold])
        self.bet_options = bet_options

    def get_strategy(self):
        # This method computes and returns the current strategy for the node based on regret matching
        normalizing_sum = 0

        # Calculate strategy proportional to positive regrets
        for a in self.bet_options:
            if self.regret_sum[a] > 0:
                self.strategy[a] = self.regret_sum[a]
            else:
                # If regret is negative or zero, set strategy for this action to 0
                self.strategy[a] = 0

            normalizing_sum += self.strategy[a]

        # Normalize the strategy so probabilities sum to 1
        for a in self.bet_options:
            if normalizing_sum > 0:
                self.strategy[a] /= normalizing_sum
            else:
                # If all regrets are non-positive, assign uniform probability
                self.strategy[a] = 1.0 / self.num_actions

        return self.strategy

    def get_average_strategy(self):
        # This method computes and returns the average strategy across all iterations
        avg_strategy = defaultdict(int)
        normalizing_sum = 0

        # Calculate the sum of all strategy probabilities across all iterations
        for a in self.bet_options:
            normalizing_sum += self.strategy_sum[a]

        # Normalize to get average strategy
        for a in self.bet_options:
            if normalizing_sum > 0:
                avg_strategy[a] = self.strategy_sum[a] / normalizing_sum
            else:
                # If sum is zero, assign uniform probability
                avg_strategy[a] = 1.0 / self.num_actions

        return avg_strategy


class LeducCFR:
    def __init__(self, iterations, decksize, starting_stack):
        # self.nbets = 2
        self.iterations = iterations  # Number of iterations to train
        self.decksize = decksize  # Size of the deck used
        self.bet_options = starting_stack  # Initial stack/betting options
        # Create a sorted deck with two cards of each type from 0 to decksize
        self.cards = sorted(np.concatenate((np.arange(decksize), np.arange(decksize))))
        self.nodes = {}  # Nodes used in the CFR process

    def cfr_iterations_external(self):
        util = np.zeros(2)  # Utility initialization for both players

        # Loop through each iteration to train
        for t in range(1, self.iterations + 1):
            for i in range(2):  # For both players
                random.shuffle(self.cards)
                util[i] += self.external_cfr(self.cards[:3], [[], []], 0, 2, 0, i, t)

        print("Average game value: {}".format(util[0] / (self.iterations)))

        # Save strategy to a file
        with open("leducnlstrat.txt", "w+") as f:
            for i in sorted(self.nodes):
                f.write("{}, {}\n".format(i, self.nodes[i].get_average_strategy()))
                print(i, self.nodes[i].get_average_strategy())

    def winning_hand(self, cards):
        # Determines the winning hand based on card values
        if cards[0] == cards[2]:
            return 0
        elif cards[1] == cards[2]:
            return 1
        elif cards[0] > cards[1]:
            return 0
        elif cards[1] > cards[0]:
            return 1
        elif cards[1] == cards[0]:
            return -1

    def valid_bets(self, history, rd, acting_player):
        # Calculate the acting player's current stack
        if acting_player == 0:
            acting_stack = int(
                19 - (np.sum(history[0][0::2]) + np.sum(history[1][0::2]))
            )
        elif acting_player == 1:
            acting_stack = int(
                19 - (np.sum(history[0][1::2]) + np.sum(history[1][1::2]))
            )

        # print('VALID BETS CHECK HISTORY', history)
        # print('VALID BETS CHECK ROUND', rd)
        # print('VALID BETS CHECK ACTING STACK', acting_stack)
        curr_history = history[rd]  # Current round's history

        if len(history[rd]) == 0:
            # print('CASE LEN 0', [*np.arange(acting_stack+1)])
            return [*np.arange(acting_stack + 1)]

        elif len(history[rd]) == 1:
            min_raise = curr_history[0] * 2
            call_amount = curr_history[0]
            if min_raise > acting_stack:
                if history[rd] == [acting_stack]:
                    # print('CASE LEN 1', [0, acting_stack])
                    return [0, acting_stack]
                else:
                    # print('CASE LEN 1', [0, call_amount, acting_stack])
                    return [0, call_amount, acting_stack]
            else:
                if history[rd] == [0]:
                    # print('CASE LEN 1', [*np.arange(min_raise, acting_stack+1)])
                    return [*np.arange(min_raise, acting_stack + 1)]
                else:
                    # print('CASE LEN 1', [0, call_amount, *np.arange(min_raise, acting_stack+1)])
                    return [0, call_amount, *np.arange(min_raise, acting_stack + 1)]

        elif len(history[rd]) == 2:
            min_raise = 2 * (curr_history[1] - curr_history[0])
            call_amount = curr_history[1] - curr_history[0]
            if min_raise > acting_stack:
                if call_amount == acting_stack:
                    # print('CASE LEN 2', [0, acting_stack])
                    return [0, acting_stack]
                else:
                    # print('CASE LEN 2', [0, call_amount, acting_stack])
                    return [0, call_amount, acting_stack]
            else:
                # print('CASE LEN 2', [0, call_amount, *np.arange(min_raise, acting_stack+1)])
                return [0, call_amount, *np.arange(min_raise, acting_stack + 1)]

        elif len(history[rd]) == 3:
            call_amount = np.abs(curr_history[1] - curr_history[2] - curr_history[0])
            # print('CASE LEN 3', [0, call_amount])
            return [0, call_amount]  # final bet (4 maximum per rd)

    def external_cfr(
        self,
        cards: List[int],
        history: List[List[int]],
        rd: int,
        pot: int,
        nodes_touched: int,
        traversing_player: int,
        t: int,
    ) -> float:
        """
        Executes the Counterfactual Regret Minimization for a given game state.

        Parameters:
        - cards (List[int]): A list of cards held by the players.
        - history (List[List[int]]): A nested list containing the history of actions taken.
        - rd (int): Current round index.
        - pot (int): Current pot value.
        - nodes_touched (int): Count of nodes that have been traversed.
        - traversing_player (int): The index of the current traversing player.
        - t (int): The current iteration count.

        Returns:
        - float: The utility value for the current game state.
        """
        # Check if the iteration count is a multiple of 1000 (for logging purposes)
        if t % 1000 == 0 and t > 0:
            print("THIS IS ITERATION", t)

        # Determine the number of plays made in the current round
        plays = len(history[rd])

        # Determine which player is acting based on the number of plays
        acting_player = plays % 2

        # Check if there are at least 2 plays in the current round
        if plays >= 2:
            # Calculate the total bets made by each player in the current round
            p0total = np.sum(history[rd][0::2])  # even indices i.e. 0, 2, 4, ...
            p1total = np.sum(history[rd][1::2])  # odd indices i.e 1, 3, 5, ...

            # If both players have made equal bets
            if p0total == p1total:
                # If it's the initial round and player 0's total bet isn't 19
                if rd == 0 and p0total != 19:
                    rd = 1  # Move to the next round
                else:
                    # If it's a showdown
                    winner = self.winning_hand(cards)
                    if winner == -1:  # If it's a tie
                        return 0
                    # Return reward or penalty based on the traversing player and the winner
                    elif traversing_player == winner:
                        return pot / 2
                    elif traversing_player != winner:
                        return -pot / 2

            # If the last play in the current round was a fold
            elif history[rd][-1] == 0:
                # Calculate the reward or penalty based on who folded and the traversing player
                if acting_player == 0:
                    return (
                        p1total + 1
                        if acting_player == traversing_player
                        else -(p1total + 1)
                    )
                elif acting_player == 1:
                    return (
                        p0total + 1
                        if acting_player == traversing_player
                        else -(p0total + 1)
                    )

        # Create an information set to uniquely identify the state
        if rd == 0:
            infoset = str(cards[acting_player]) + str(history)
        elif rd == 1:
            infoset = str(cards[acting_player]) + str(cards[2]) + str(history)

        # Get the valid bets that can be made by the acting player
        infoset_bets = self.valid_bets(history, rd, acting_player)

        # If the current infoset doesn't exist in the nodes dictionary, add it
        if infoset not in self.nodes:
            self.nodes[infoset] = Node(infoset_bets)

        # Update the count of nodes touched
        nodes_touched += 1

        # If the acting player is the traversing player
        if acting_player == traversing_player:
            util = defaultdict(int)
            node_util = 0
            strategy = self.nodes[infoset].get_strategy()

            # Iterate over all valid actions and compute their utilities
            for a in infoset_bets:
                if rd == 0:
                    next_history = [history[0] + [a], history[1]]
                elif rd == 1:
                    next_history = [history[0], history[1] + [a]]

                pot += a
                util[a] = self.external_cfr(
                    cards, next_history, rd, pot, nodes_touched, traversing_player, t
                )
                node_util += strategy[a] * util[a]

            # Update the regret sums for each action
            for a in infoset_bets:
                regret = util[a] - node_util
                self.nodes[infoset].regret_sum[a] += regret
            return node_util

        # If the acting player isn't the traversing player
        else:
            strategy = self.nodes[infoset].get_strategy()

            # Sample an action based on the strategy
            dart = random.random()
            strat_sum = 0
            for a in strategy:
                strat_sum += strategy[a]
                if dart < strat_sum:
                    action = a
                    break

            # Update the history and pot based on the chosen action
            if rd == 0:
                next_history = [history[0] + [action], history[1]]
            elif rd == 1:
                next_history = [history[0], history[1] + [action]]
            pot += action

            # Compute the utility of the chosen action
            util = self.external_cfr(
                cards, next_history, rd, pot, nodes_touched, traversing_player, t
            )

            # Update the strategy sum for the current node
            for a in infoset_bets:
                self.nodes[infoset].strategy_sum[a] += strategy[a]
            return util


if __name__ == "__main__":
    k = LeducCFR(5000, 3, 20)
    k.cfr_iterations_external()
    breakpoint()
    # for i in range(20):
    # 	print(k.valid_bets([[i],[]], 0, 19))
    # a = k.valid_bets([[4, 18],[]], 0, 15)
    # print(a)
