import unittest

from data.decision_row import DecisionRow
from data.encoder.state_encoder.encode_global import encode_global
from data.encoder.state_encoder.layout import GLOBAL_DIM
from models.game.commands import EndTurn


class EncodeGlobalTests(unittest.TestCase):
    def _row(
        self,
        *,
        plays_this_turn: int = 0,
        opponent_hand_size: int = 0,
    ) -> DecisionRow:
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
            opponent_hand_size=opponent_hand_size,
            plays_this_turn=plays_this_turn,
            pending=None,
            timed_out=False,
            viewer_won=False,
        )

    def test_dim(self) -> None:
        self.assertEqual(len(encode_global(self._row())), GLOBAL_DIM)

    def test_turns_left_normalized(self) -> None:
        row = self._row(plays_this_turn=1)
        self.assertAlmostEqual(encode_global(row)[0], 2 / 3)

    def test_opponent_hand_size_normalized(self) -> None:
        row = self._row(opponent_hand_size=7)
        self.assertAlmostEqual(encode_global(row)[1], 1.0)


if __name__ == "__main__":
    unittest.main()
