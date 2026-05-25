from __future__ import annotations

import unittest

from models.game.game import Game
from rollout import choose_move, rollout
from rollout.jsn import debt_or_action_cancelled


class JsnLogicTests(unittest.TestCase):
    def test_defender_wins_with_extra_jsn(self) -> None:
        self.assertTrue(debt_or_action_cancelled(2, 1, "defender", False))

    def test_actor_wins_when_defender_has_no_jsn(self) -> None:
        self.assertFalse(debt_or_action_cancelled(0, 1, "defender", False))


class RolloutSmokeTests(unittest.TestCase):
    def test_rollout_runs_full_game(self) -> None:
        game = Game()
        game.start_match()
        steps = rollout(game, max_steps=5000)
        self.assertGreater(steps, 0)
        self.assertLess(steps, 5000)

    def test_choose_move_always_legal(self) -> None:
        game = Game()
        game.start_match()
        for _ in range(200):
            if game.is_over():
                break
            moves = game.legal_moves()
            chosen = choose_move(game)
            self.assertIn(chosen, moves)
            game.apply(chosen)


if __name__ == "__main__":
    unittest.main()
