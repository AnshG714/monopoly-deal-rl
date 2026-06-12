from __future__ import annotations

import random
import unittest

from models.cards.money import MoneyCard
from models.game.game import Game
from mcts.determinize import determinize


def _unknown_pool_values(game: Game) -> list[tuple]:
    """(type, value) pairs for opponent hand + deck — the hidden pool."""
    other_idx = 1 - game.acting_player_idx
    cards = game.players[other_idx].hand + game.deck
    return sorted((c.type, c.value) for c in cards)


def _controlled_game(*, acting_player_idx: int = 0, seed: int = 0) -> Game:
    """Minimal 2-player state with distinct, easy-to-reason-about cards."""
    game = Game(rng=random.Random(seed))
    game.acting_player_idx = acting_player_idx
    game.players[0].hand = [MoneyCard(1), MoneyCard(2)]
    game.players[1].hand = [MoneyCard(5), MoneyCard(10), MoneyCard(20)]
    game.deck = [MoneyCard(50), MoneyCard(3), MoneyCard(4)]
    return game


class DeterminizeTests(unittest.TestCase):
    def test_does_not_mutate_input(self) -> None:
        game = _controlled_game()
        before_other_hand = list(game.players[1].hand)
        before_deck = list(game.deck)

        determinize(game)

        self.assertEqual(game.players[1].hand, before_other_hand)
        self.assertEqual(game.deck, before_deck)

    def test_does_not_mutate_input_rng_state(self) -> None:
        game = _controlled_game(seed=123)
        before = game._rng.getstate()

        determinize(game)

        self.assertEqual(game._rng.getstate(), before)

    def test_preserves_unknown_pool_multiset(self) -> None:
        game = _controlled_game()
        before = _unknown_pool_values(game)

        new_game = determinize(game)

        self.assertEqual(_unknown_pool_values(new_game), before)

    def test_preserves_opponent_hand_size(self) -> None:
        game = _controlled_game()
        expected_size = len(game.players[1].hand)

        new_game = determinize(game)

        self.assertEqual(len(new_game.players[1].hand), expected_size)

    def test_leaves_acting_player_hand_unchanged(self) -> None:
        game = _controlled_game(acting_player_idx=0)
        before = [(c.type, c.value) for c in game.players[0].hand]

        new_game = determinize(game)

        after = [(c.type, c.value) for c in new_game.players[0].hand]
        self.assertEqual(after, before)

    def test_reproducible_with_same_seed(self) -> None:
        g1 = _controlled_game(seed=99)
        g2 = _controlled_game(seed=99)

        n1 = determinize(g1)
        n2 = determinize(g2)

        hand1 = [(c.type, c.value) for c in n1.players[1].hand]
        hand2 = [(c.type, c.value) for c in n2.players[1].hand]
        self.assertEqual(hand1, hand2)


if __name__ == "__main__":
    unittest.main()
