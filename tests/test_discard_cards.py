from __future__ import annotations

import unittest

from models.cards.money import MoneyCard
from models.game.commands.discard_cards import DiscardCards, excess_hand_count
from models.game.commands.end_turn import EndTurn
from models.game.game import Game


class DiscardCardsTests(unittest.TestCase):
    def test_excess_hand_count(self) -> None:
        self.assertEqual(excess_hand_count(7), 0)
        self.assertEqual(excess_hand_count(8), 1)
        self.assertEqual(excess_hand_count(10), 3)

    def test_discard_exact_excess(self) -> None:
        game = Game()
        game.players[0].hand = [MoneyCard(1)] * 8
        game.plays_this_turn = 2
        deck_before = len(game.deck)

        game.discard_cards([0])

        self.assertEqual(len(game.players[0].hand), 7)
        self.assertEqual(len(game.deck), deck_before + 1)
        self.assertEqual(len(game.discard_pile), 0)
        self.assertEqual(game.plays_this_turn, 2)

    def test_discard_three_from_ten(self) -> None:
        game = Game()
        game.players[0].hand = [MoneyCard(i) for i in range(10)]
        deck_before = len(game.deck)

        game.discard_cards([1, 4, 9])

        self.assertEqual(len(game.players[0].hand), 7)
        self.assertEqual(len(game.deck), deck_before + 3)
        self.assertEqual(len(game.discard_pile), 0)

    def test_rejects_wrong_count(self) -> None:
        game = Game()
        game.players[0].hand = [MoneyCard(1)] * 8

        with self.assertRaises(ValueError):
            game.discard_cards([0, 1])

    def test_rejects_when_hand_already_legal(self) -> None:
        game = Game()
        game.players[0].hand = [MoneyCard(1)] * 7

        with self.assertRaises(RuntimeError):
            game.discard_cards([0])

    def test_end_turn_after_discard(self) -> None:
        game = Game()
        game.players[0].hand = [MoneyCard(1)] * 8
        game.discard_cards([3])
        game.end_turn()
        self.assertEqual(game.current_player_idx, 1)


if __name__ == "__main__":
    unittest.main()
