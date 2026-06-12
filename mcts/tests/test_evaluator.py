from __future__ import annotations

import random
import unittest

from mcts.evaluator import evaluate_reward
from mcts.solver import ISMCTSSolver
from models.cards.property import CARDS_IN_SET_FOR_COLOR, Color, SingleColorProperty
from models.game.game import Game
from rollout import choose_random_move


def _add_properties(game: Game, player_idx: int, color: Color, count: int) -> None:
    rents = list(range(1, CARDS_IN_SET_FOR_COLOR[color] + 1))
    for _ in range(count):
        game.players[player_idx].add_property_to_board(
            SingleColorProperty(color, "X", rents, 3),
            color,
        )


class EvaluatorTests(unittest.TestCase):
    def test_complete_set_advantage_scores_above_even(self) -> None:
        game = Game(rng=random.Random(0))
        _add_properties(game, 0, Color.RED, 3)

        self.assertGreater(evaluate_reward(game, 0), 0.5)
        self.assertLess(evaluate_reward(game, 1), 0.5)

    def test_terminal_state_scores_win_or_loss(self) -> None:
        game = Game(rng=random.Random(0))
        _add_properties(game, 0, Color.RED, 3)
        _add_properties(game, 0, Color.BLUE, 2)
        _add_properties(game, 0, Color.GREEN, 3)

        self.assertEqual(evaluate_reward(game, 0), 1.0)
        self.assertEqual(evaluate_reward(game, 1), 0.0)

    def test_depth_limited_solver_returns_legal_move(self) -> None:
        game = Game(rng=random.Random(0))
        game.start_match()

        move = ISMCTSSolver(
            iterations=5,
            rng=random.Random(0),
            rollout_depth=4,
        ).search(game)

        self.assertIn(move, game.legal_moves())

    def test_pruned_depth_limited_solver_returns_legal_move(self) -> None:
        game = Game(rng=random.Random(1))
        game.start_match()

        move = ISMCTSSolver(
            iterations=5,
            rng=random.Random(1),
            rollout_depth=4,
            max_candidate_moves=5,
            max_interrupt_moves=2,
        ).search(game)

        self.assertIn(move, game.legal_moves())

    def test_solver_accepts_random_rollout_policy(self) -> None:
        game = Game(rng=random.Random(2))
        game.start_match()

        move = ISMCTSSolver(
            iterations=5,
            rng=random.Random(2),
            rollout_depth=4,
            max_candidate_moves=None,
            max_interrupt_moves=None,
            rollout_policy=choose_random_move,
        ).search(game)

        self.assertIn(move, game.legal_moves())


if __name__ == "__main__":
    unittest.main()
