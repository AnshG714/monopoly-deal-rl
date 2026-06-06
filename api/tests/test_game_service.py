from __future__ import annotations

import unittest

from api.services.game_service import GameService, NotHumanTurnError
from api.store.memory import GameStore


class GameServiceTests(unittest.TestCase):
    def test_create_game_starts_on_human_turn(self) -> None:
        service = GameService(store=GameStore(), default_mcts_iterations=1)
        payload = service.create_game(seed=42)

        self.assertEqual(payload["viewer"], 0)
        self.assertEqual(payload["acting_player_idx"], 0)
        self.assertFalse(payload["is_over"])
        self.assertGreater(len(payload["legal_moves"]), 0)
        self.assertEqual(payload["seed"], 42)

    def test_apply_move_runs_ai_until_human_turn(self) -> None:
        service = GameService(store=GameStore(), default_mcts_iterations=1)
        created = service.create_game(seed=7)
        game_id = created["game_id"]

        end_turn_id = next(
            move["id"]
            for move in created["legal_moves"]
            if move["kind"] == "EndTurn"
        )
        after_turn = service.apply_human_move(game_id, end_turn_id)

        self.assertIn(
            after_turn["acting_player_idx"],
            {0, after_turn["viewer"]},
        )
        if not after_turn["is_over"]:
            self.assertEqual(after_turn["acting_player_idx"], after_turn["viewer"])
            self.assertGreater(len(after_turn["legal_moves"]), 0)

    def test_apply_move_rejects_when_not_human_turn(self) -> None:
        store = GameStore()
        service = GameService(store=store, default_mcts_iterations=1)
        created = service.create_game(seed=1)
        session = store.get(created["game_id"])
        assert session is not None
        session.game.acting_player_idx = 1

        with self.assertRaises(NotHumanTurnError):
            service.apply_human_move(created["game_id"], 0)
