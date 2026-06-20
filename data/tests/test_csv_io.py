import csv
import json
import tempfile
import unittest
from pathlib import Path

from data.csv_io import decision_row_to_csv_record, write_decision_rows_csv
from data.generate_self_play_data import generate_self_play_data_for_game
from mcts import GameSpec


class DecisionCsvTests(unittest.TestCase):
    def test_write_decision_rows_csv_round_trip(self) -> None:
        spec = GameSpec(seed=5, both_players_mcts=True, mcts_iters=5)
        rows = generate_self_play_data_for_game(spec)
        self.assertGreaterEqual(len(rows), 1)

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "rows.csv"
            write_decision_rows_csv(path, rows)

            with path.open(newline="", encoding="utf-8") as handle:
                loaded = list(csv.DictReader(handle))

        self.assertEqual(len(loaded), len(rows))
        first = loaded[0]
        chosen = json.loads(first["chosen_move_json"])
        visits = json.loads(first["visits_json"])
        self.assertIn("kind", chosen)
        self.assertIn("params", chosen)
        self.assertIsInstance(visits, list)
        if visits:
            self.assertIn("move", visits[0])
            self.assertIn("visit_share", visits[0])

    def test_decision_row_to_csv_record_is_flat(self) -> None:
        spec = GameSpec(seed=1, both_players_mcts=True, mcts_iters=3)
        row = generate_self_play_data_for_game(spec)[0]
        record = decision_row_to_csv_record(row)
        for key, value in record.items():
            if key.endswith("_json"):
                self.assertIsInstance(value, str)
                json.loads(value)
            else:
                self.assertIsInstance(value, (int, bool))


if __name__ == "__main__":
    unittest.main()
