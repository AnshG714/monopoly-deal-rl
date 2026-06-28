import tempfile
import unittest
from pathlib import Path

from data.csv_io import read_decision_rows_csv, write_decision_rows_csv
from data.decision_row import DecisionRow
from data.generate_self_play_data import generate_self_play_data_for_game
from encoder.encode import encode_decision_row, encode_decision_row_blocks
from encoder.layout import FEATURE_LAYOUT, STATE_DIM
from mcts import GameSpec
from models.game.commands import EndTurn


class EncodeDecisionRowTests(unittest.TestCase):
    def _empty_row(self) -> DecisionRow:
        return DecisionRow(
            seed=0,
            step=0,
            viewer_idx=0,
            chosen_move=EndTurn(),
            legal_moves=[],
            visits={},
            viewer_property_piles=[],
            viewer_hand=[],
            viewer_bank=[],
            opponent_property_piles=[],
            opponent_bank=[],
            opponent_hand_size=0,
            plays_this_turn=0,
            pending=None,
            timed_out=False,
            viewer_won=False,
        )

    def test_state_dim(self) -> None:
        vector = encode_decision_row(self._empty_row())
        self.assertEqual(len(vector), STATE_DIM)

    def test_blocks_concatenate_to_full_vector(self) -> None:
        row = self._empty_row()
        vector = encode_decision_row(row)
        blocks = encode_decision_row_blocks(row)
        rebuilt = [value for key in (
            "global",
            "viewer_bank",
            "opponent_bank",
            "viewer_properties",
            "opponent_properties",
            "pending",
            "hand",
        ) for value in blocks[key]]
        self.assertEqual(vector, rebuilt)

    def test_layout_slices_match_blocks(self) -> None:
        row = self._empty_row()
        vector = encode_decision_row(row)
        blocks = encode_decision_row_blocks(row)
        self.assertEqual(
            vector[FEATURE_LAYOUT.global_.start : FEATURE_LAYOUT.global_.end],
            blocks["global"],
        )
        self.assertEqual(
            vector[FEATURE_LAYOUT.pending.start : FEATURE_LAYOUT.pending.end],
            blocks["pending"],
        )

    def test_csv_round_trip_encoding(self) -> None:
        spec = GameSpec(seed=11, both_players_mcts=True, mcts_iters=5)
        rows = generate_self_play_data_for_game(spec)
        self.assertGreaterEqual(len(rows), 1)

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "rows.csv"
            write_decision_rows_csv(path, rows)
            loaded = read_decision_rows_csv(path)

        self.assertEqual(len(loaded), len(rows))
        for original, parsed in zip(rows, loaded, strict=True):
            self.assertEqual(
                encode_decision_row(original),
                encode_decision_row(parsed),
            )


if __name__ == "__main__":
    unittest.main()
