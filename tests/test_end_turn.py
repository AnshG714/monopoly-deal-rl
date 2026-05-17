from __future__ import annotations

import unittest

from models.cards.money import MoneyCard
from models.game.commands.end_turn import EndTurn
from models.game.game import Game
from models.game.pending import PaymentDue


class EndTurnTests(unittest.TestCase):
    def test_end_turn_advances_player_and_draws(self) -> None:
        game = Game()
        game.current_player_idx = 0
        game.acting_player_idx = 0
        game.plays_this_turn = 2
        game.players[0].hand = [MoneyCard(1)]
        deck_before = len(game.deck)

        game.end_turn()

        self.assertEqual(game.current_player_idx, 1)
        self.assertEqual(game.plays_this_turn, 0)
        self.assertEqual(len(game.players[1].hand), 2)
        self.assertEqual(len(game.deck), deck_before - 2)

    def test_end_turn_does_not_require_play_budget(self) -> None:
        game = Game()
        from models.game.commands.base import MAX_PLAYS_PER_TURN

        game.plays_this_turn = MAX_PLAYS_PER_TURN
        game.end_turn()
        self.assertEqual(game.current_player_idx, 1)

    def test_end_turn_rejects_oversized_hand(self) -> None:
        game = Game()
        game.players[0].hand = [MoneyCard(1)] * 8

        with self.assertRaises(ValueError):
            game.end_turn()

    def test_end_turn_rejects_while_pending(self) -> None:
        game = Game()
        game.pending = PaymentDue(creditor_idx=0, debtor_idx=1, amount_m=1)

        with self.assertRaises(RuntimeError):
            game.apply(EndTurn())

    def test_empty_hand_refill_before_passing(self) -> None:
        game = Game()
        game.players[0].hand = []
        deck_before = len(game.deck)

        game.end_turn()

        self.assertEqual(len(game.players[0].hand), 5)
        self.assertEqual(len(game.deck), deck_before - 5 - 2)


if __name__ == "__main__":
    unittest.main()
