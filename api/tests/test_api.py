from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from api.main import create_app


class ApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(create_app())

    def test_create_get_and_move_flow(self) -> None:
        create_resp = self.client.post(
            "/games",
            json={"seed": 99, "mcts_iterations": 1},
        )
        self.assertEqual(create_resp.status_code, 200)
        created = create_resp.json()
        game_id = created["game_id"]
        self.assertEqual(created["acting_player_idx"], 0)
        self.assertGreater(len(created["legal_moves"]), 0)

        get_resp = self.client.get(f"/games/{game_id}")
        self.assertEqual(get_resp.status_code, 200)
        self.assertEqual(get_resp.json()["game_id"], game_id)

        end_turn_id = next(
            move["id"]
            for move in created["legal_moves"]
            if move["kind"] == "EndTurn"
        )
        move_resp = self.client.post(
            f"/games/{game_id}/moves",
            json={"move_id": end_turn_id},
        )
        self.assertEqual(move_resp.status_code, 200)
        body = move_resp.json()
        if not body["is_over"]:
            self.assertEqual(body["acting_player_idx"], body["viewer"])

    def test_unknown_game_returns_404(self) -> None:
        resp = self.client.get("/games/does-not-exist")
        self.assertEqual(resp.status_code, 404)

    def test_deck_returns_serialized_full_deck(self) -> None:
        resp = self.client.get("/api/deck")
        self.assertEqual(resp.status_code, 200)

        body = resp.json()
        self.assertEqual(body["total"], 106)
        self.assertEqual(len(body["cards"]), 106)
        self.assertIn("display_name", body["cards"][0])
