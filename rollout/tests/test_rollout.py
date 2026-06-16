from __future__ import annotations

import random
import unittest

from models.cards.property import Color, MultiColorProperty, SingleColorProperty
from models.game.commands import MoveWildProperty
from models.game.game import Game
from rollout import MovePolicyType, get_action_with_policy, rollout
from rollout.jsn import debt_or_action_cancelled
from rollout.heuristic_policy import (
    _move_wild_breaks_complete_set,
    _move_wild_completes_set,
)

_RENT_PINK = [1, 2, 4]
_RENT_ORANGE = [1, 3, 5]


class JsnLogicTests(unittest.TestCase):
    def test_defender_wins_with_extra_jsn(self) -> None:
        self.assertTrue(debt_or_action_cancelled(2, 1, "defender", False))

    def test_actor_wins_when_defender_has_no_jsn(self) -> None:
        self.assertFalse(debt_or_action_cancelled(0, 1, "defender", False))


class RolloutSmokeTests(unittest.TestCase):
    def test_rollout_runs_full_game(self) -> None:
        game = Game()
        game.start_match()
        result = rollout(game, max_steps=5000)
        self.assertGreater(result["steps"], 0)
        self.assertLess(result["steps"], 5000)

    def test_heuristic_policy_always_legal(self) -> None:
        game = Game()
        game.start_match()
        for _ in range(200):
            if game.is_over():
                break
            moves = game.legal_moves()
            chosen = get_action_with_policy(game, MovePolicyType.HEURISTIC)
            self.assertIn(chosen, moves)
            game.apply(chosen)

    def test_random_policy_always_legal(self) -> None:
        game = Game(rng=random.Random(0))
        game.start_match()
        for _ in range(200):
            if game.is_over():
                break
            moves = game.legal_moves()
            chosen = get_action_with_policy(game, MovePolicyType.RANDOM)
            self.assertIn(chosen, moves)
            game.apply(chosen)

    def test_rollout_completes_after_mcts_leaf_seed_4(self) -> None:
        """Regression: wild shuffle between complete sets used to stall rollouts."""
        from mcts.determinize import determinize
        from mcts.node import ISMCTSNode

        g = Game(rng=random.Random(4))
        g.start_match()
        root = ISMCTSNode()

        for _ in range(94):
            dg = determinize(g)
            node = root
            while not dg.is_over():
                unexp = node.get_unexpanded_moves(dg.legal_moves())
                if unexp:
                    break
                child = node.choose_child_uct(dg.legal_moves())
                if child is None:
                    break
                dg.apply(child.move)
                node = child
            unexp = node.get_unexpanded_moves(dg.legal_moves())
            if not dg.is_over() and unexp:
                move = dg._rng.choice(unexp)
                dg.apply(move)
                node.children.append(ISMCTSNode(move, node))
                node = node.children[-1]

        result = rollout(dg, max_steps=10_000)
        self.assertIn(result["winner"], (0, 1))


class MoveWildRolloutPolicyTests(unittest.TestCase):
    def test_rejects_wild_move_that_breaks_complete_set(self) -> None:
        wild = MultiColorProperty(
            Color.PINK, _RENT_PINK, Color.ORANGE, _RENT_ORANGE, 2
        )
        game = Game()
        player = game.players[0]
        game.current_player_idx = 0
        game.acting_player_idx = 0
        player.add_property_to_board(
            SingleColorProperty(Color.ORANGE, "A", _RENT_ORANGE, 3), Color.ORANGE
        )
        player.add_property_to_board(
            SingleColorProperty(Color.ORANGE, "B", _RENT_ORANGE, 3), Color.ORANGE
        )
        player.add_property_to_board(wild, Color.ORANGE)
        player.add_property_to_board(
            SingleColorProperty(Color.PINK, "C", _RENT_PINK, 2), Color.PINK
        )
        player.add_property_to_board(
            SingleColorProperty(Color.PINK, "D", _RENT_PINK, 2), Color.PINK
        )

        orange_idx = next(
            i for i, pile in enumerate(player.property_sets) if pile.color == Color.ORANGE
        )
        move = MoveWildProperty(
            from_set_idx=orange_idx, card_idx=2, into_color=Color.PINK
        )

        self.assertTrue(_move_wild_completes_set(game, move))
        self.assertTrue(_move_wild_breaks_complete_set(game, move))
        self.assertNotIn(
            move,
            [
                m
                for m in game.legal_moves()
                if isinstance(m, MoveWildProperty)
                and _move_wild_completes_set(game, m)
                and not _move_wild_breaks_complete_set(game, m)
            ],
        )


if __name__ == "__main__":
    unittest.main()
