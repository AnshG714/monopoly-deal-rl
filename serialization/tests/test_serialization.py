from __future__ import annotations

import unittest

from models.cards.money import MoneyCard
from models.game.game import Game
from serialization.moves import encode_moves
from serialization.state import view_for_player


class SerializationTests(unittest.TestCase):
    def test_view_hides_opponent_hand(self) -> None:
        game = Game()
        game.players[0].hand = [MoneyCard(1), MoneyCard(2)]
        game.players[1].hand = [MoneyCard(3), MoneyCard(4), MoneyCard(5)]

        view = view_for_player(game, viewer_idx=0)

        human_hand = view["players"][0]["hand"]
        opponent_hand = view["players"][1]["hand"]
        self.assertEqual(human_hand["size"], 2)
        self.assertEqual(len(human_hand["cards"]), 2)
        self.assertEqual(opponent_hand["size"], 3)
        self.assertIsNone(opponent_hand["cards"])

    def test_encode_moves_matches_apply_by_id(self) -> None:
        game = Game()
        game.start_match()
        game.acting_player_idx = 0
        game.current_player_idx = 0

        moves = game.legal_moves()
        encoded = encode_moves(game, moves)
        self.assertEqual(len(encoded), len(moves))
        self.assertEqual([move["id"] for move in encoded], list(range(len(moves))))

        first_kind = encoded[0]["kind"]
        game.apply(moves[0])
        self.assertIsNotNone(first_kind)
