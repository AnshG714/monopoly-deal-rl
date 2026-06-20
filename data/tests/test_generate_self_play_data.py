import unittest

from data.generate_self_play_data import generate_self_play_data_for_game
from mcts import GameSpec


class GenerateSelfPlayDataTests(unittest.TestCase):
    def test_snapshots_do_not_alias_live_game_state(self) -> None:
        spec = GameSpec(seed=7, both_players_mcts=True, mcts_iters=5)
        rows = generate_self_play_data_for_game(spec)
        self.assertGreaterEqual(len(rows), 2)

        first, last = rows[0], rows[-1]
        self.assertIsNot(first.viewer_hand, last.viewer_hand)
        self.assertNotEqual(first.step, last.step)

    def test_symmetric_mcts_logs_both_seats(self) -> None:
        spec = GameSpec(seed=3, both_players_mcts=True, mcts_iters=5)
        rows = generate_self_play_data_for_game(spec)
        seats = {row.viewer_idx for row in rows}
        self.assertEqual(seats, {0, 1})

    def test_viewer_won_matches_game_winner(self) -> None:
        spec = GameSpec(seed=11, both_players_mcts=True, mcts_iters=5)
        rows = generate_self_play_data_for_game(spec)
        winners = {row.viewer_won for row in rows if row.viewer_idx == 0}
        self.assertEqual(len(winners), 1)


if __name__ == "__main__":
    unittest.main()
