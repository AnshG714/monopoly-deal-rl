import csv
import json
import tempfile
import unittest
from pathlib import Path

from data.csv_io import (
    decision_row_to_csv_record,
    merge_decision_rows_csvs,
    write_decision_rows_csv,
)
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

    def test_merge_decision_rows_csvs_concatenates_chunks(self) -> None:
        specs = [
            GameSpec(seed=1, both_players_mcts=True, mcts_iters=3),
            GameSpec(seed=2, both_players_mcts=True, mcts_iters=3),
        ]
        chunks = [generate_self_play_data_for_game(spec) for spec in specs]

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            chunk_paths = [
                tmp_path / f"seed_{spec.seed}.csv" for spec in specs
            ]
            for path, rows in zip(chunk_paths, chunks, strict=True):
                write_decision_rows_csv(path, rows)

            merged_path = tmp_path / "merged.csv"
            row_count = merge_decision_rows_csvs(chunk_paths, merged_path)

            with merged_path.open(newline="", encoding="utf-8") as handle:
                merged = list(csv.DictReader(handle))

        expected_rows = sum(len(rows) for rows in chunks)
        self.assertEqual(row_count, expected_rows)
        self.assertEqual(len(merged), expected_rows)
        seeds = {int(row["seed"]) for row in merged}
        self.assertEqual(seeds, {1, 2})


if __name__ == "__main__":
    unittest.main()
