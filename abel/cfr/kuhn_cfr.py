import numpy as np
import random


class Node:
    def __init__(self, num_actions):
        # Initial regret for each action set to zero.
        self.regret_sum = np.zeros(num_actions)

        # Current strategy initialized to a uniform distribution.
        self.strategy = np.zeros(num_actions)

        # Cumulative strategy across all iterations, used to compute the average strategy.
        self.strategy_sum = np.zeros(num_actions)

        # Number of possible actions from this node.
        self.num_actions = num_actions

    def get_strategy(self):
        # Get the current strategy for this node, based on positive regrets.

        # Sum used to normalize the strategy so that it becomes a probability distribution.
        normalizing_sum = 0

        # Convert positive regrets to strategy probabilities.
        for a in range(self.num_actions):
            self.strategy[a] = max(self.regret_sum[a], 0)
            normalizing_sum += self.strategy[a]

        # Normalize the strategy.
        for a in range(self.num_actions):
            # If all regrets are non-positive, we use a uniform strategy.
            self.strategy[a] = (
                self.strategy[a] / normalizing_sum
                if normalizing_sum > 0
                else 1.0 / self.num_actions
            )

        return self.strategy

    def get_average_strategy(self):
        # Get the average strategy across all iterations for this node.

        avg_strategy = np.zeros(self.num_actions)
        normalizing_sum = np.sum(self.strategy_sum)

        # Compute the average strategy.
        for a in range(self.num_actions):
            avg_strategy[a] = (
                self.strategy_sum[a] / normalizing_sum
                if normalizing_sum > 0
                else 1.0 / self.num_actions
            )

        return avg_strategy


import numpy as np
import random


class KuhnCFR:
    def __init__(self, iterations, decksize):
        # Number of possible betting options (bet or check/fold).
        self.nbets = 2

        # Number of iterations for the CFR algorithm.
        self.iterations = iterations

        # Size of the deck used in Kuhn Poker.
        self.decksize = decksize

        # Representing the cards in the deck.
        self.cards = np.arange(decksize)

        # Number of betting options (used for the Node strategy).
        self.bet_options = 2

        # Dictionary to store the game states or "information sets".
        self.nodes = {}

    def cfr_iterations_external(self):
        # Total utility for each player.
        util = np.zeros(2)

        # Run CFR for the given number of iterations.
        for t in range(1, self.iterations + 1):
            for i in range(2):
                # Shuffle the cards to get a random ordering.
                random.shuffle(self.cards)

                # Perform external sampling CFR.
                util[i] += self.external_cfr(self.cards[:2], [], 2, 0, i, t)
                print(i, util[i])

        # Display average game value.
        print("Average game value: {}".format(util[0] / (self.iterations)))

        # Display average strategy for each information set.
        for i in sorted(self.nodes):
            print(i, self.nodes[i].get_average_strategy())

    def external_cfr(self, cards, history, pot, nodes_touched, traversing_player, t):
        # Print current iteration for debugging.
        print("THIS IS ITERATION", t)
        print(cards, history, pot)

        # Number of actions taken in the current game.
        plays = len(history)

        # Determine which player is acting (0 or 1).
        acting_player = plays % 2
        opponent_player = 1 - acting_player

        # Check if the game has ended.
        if plays >= 2:
            # Player folded after a bet.
            if history[-1] == 0 and history[-2] == 1:
                return 1 if acting_player == traversing_player else -1

            # Check-check or bet-call; go to showdown.
            if (history[-1] == 0 and history[-2] == 0) or (
                history[-1] == 1 and history[-2] == 1
            ):
                if cards[acting_player] > cards[opponent_player]:
                    return pot / 2 if acting_player == traversing_player else -pot / 2
                else:
                    return -pot / 2 if acting_player == traversing_player else pot / 2

        # Create an information set for the current state.
        infoset = str(cards[acting_player]) + str(history)

        # If this information set has not been encountered, initialize a new node for it.
        if infoset not in self.nodes:
            self.nodes[infoset] = Node(self.bet_options)

        nodes_touched += 1

        # If the acting player is the player we're traversing for, we compute and backpropagate the counterfactual regret.
        if acting_player == traversing_player:
            util = np.zeros(self.bet_options)  # Utility for each action.
            node_util = 0
            strategy = self.nodes[infoset].get_strategy()
            for a in range(self.bet_options):
                next_history = history + [a]
                pot += a
                util[a] = self.external_cfr(
                    cards, next_history, pot, nodes_touched, traversing_player, t
                )
                node_util += strategy[a] * util[a]

            # Update the regret for each action.
            for a in range(self.bet_options):
                regret = util[a] - node_util
                self.nodes[infoset].regret_sum[a] += regret
            return node_util

        # If the acting player is not the traversing player, we sample one action based on the current strategy and continue.
        else:
            strategy = self.nodes[infoset].get_strategy()
            util = 0
            # Randomly select an action based on the strategy.
            if random.random() < strategy[0]:
                next_history = history + [0]
            else:
                next_history = history + [1]
                pot += 1
            util = self.external_cfr(
                cards, next_history, pot, nodes_touched, traversing_player, t
            )

            # Update the strategy sum for the information set.
            for a in range(self.bet_options):
                self.nodes[infoset].strategy_sum[a] += strategy[a]
            return util


if __name__ == "__main__":
    k = KuhnCFR(100000, 10)
    k.cfr_iterations_external()
