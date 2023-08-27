Leduc Poker is a simplified poker game often used as a benchmark in poker AI research, much like Kuhn Poker. Here's a basic overview of Leduc Poker:

**Deck**:

- Leduc Poker uses a deck of six cards, typically consisting of two suits (let's say Hearts and Spades). Each suit has three values: J (Jack), Q (Queen), and K (King). So, the deck is: J♥, Q♥, K♥, J♠, Q♠, K♠.

**Rules**:

1. **Initial Deal**:

   - Each player is dealt one private card from the deck.

2. **First Betting Round**:

   - Players can either check or raise. If one player raises, the other player can either call or fold. If the other player folds, the player who raised wins the pot. If both players check or one player calls the raise, the game proceeds to the next phase.

3. **Second Deal**:

   - After the first betting round, a single community card is dealt face up in the center.

4. **Second Betting Round**:

   - Another round of betting occurs, much like the first round. Players can check, raise, or fold based on the combination of their private card and the community card.

5. **Showdown**:
   - If both players remain (neither folds), they reveal their private cards. The player with the pair (e.g., a private J and a community J) wins. If neither player has a pair, the player with the highest card value wins, with the card values ordered as J < Q < K. In case of a tie (both have the same high card value and no pair), the pot is split.

**Game's Purpose in Research**:

Leduc Poker serves as a more complex game compared to Kuhn Poker but is still much simpler than full-scale poker games. It's used to test and validate poker AI algorithms because the game has enough complexity to present non-trivial challenges but remains tractable for computational solutions and analysis.

Given its well-defined structure and increased complexity over Kuhn Poker, Leduc Poker provides a good bridge between trivial toy poker games and real-world poker variants, making it a popular choice in the AI research community.
