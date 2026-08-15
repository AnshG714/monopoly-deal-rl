import random
import time
from dataclasses import dataclass
from typing import Callable

from mcts.consts import (
    DEFAULT_ITERS,
    DEFAULT_MAX_CANDIDATE_MOVES,
    DEFAULT_MAX_INTERRUPT_MOVES,
    DEFAULT_ROLLOUT_DEPTH,
)
from mcts.evaluator import evaluate_reward
from mcts.move_prior import HeuristicMovePrior, MovePrior
from mcts.move_scoring import select_interrupt_moves
from mcts.node import ISMCTSNode
from mcts.determinize import determinize
from models.game.game import Game, GameCommand
from rollout import MovePolicyType, rollout, get_action_with_policy


@dataclass
class ISMCTSSolverResult:
    move: GameCommand
    visits: dict[GameCommand, float]


class ISMCTSSolver:
    def __init__(
        self,
        iterations: int = DEFAULT_ITERS,
        rng: random.Random | None = None,
        rollout_depth: int | None = DEFAULT_ROLLOUT_DEPTH,
        max_candidate_moves: int | None = DEFAULT_MAX_CANDIDATE_MOVES,
        max_interrupt_moves: int | None = DEFAULT_MAX_INTERRUPT_MOVES,
        max_search_seconds: float | None = None,
        rollout_policy: MovePolicyType = MovePolicyType.HEURISTIC,
        leaf_evaluator: Callable[[Game, int], float] | None = None,
        move_prior: MovePrior | None = None,
    ):
        if rollout_depth is not None and rollout_depth < 0:
            raise ValueError("rollout_depth must be non-negative")
        if max_candidate_moves is not None and max_candidate_moves < 1:
            raise ValueError("max_candidate_moves must be positive")
        if max_interrupt_moves is not None and max_interrupt_moves < 1:
            raise ValueError("max_interrupt_moves must be positive")
        if max_search_seconds is not None and max_search_seconds <= 0:
            raise ValueError("max_search_seconds must be positive")
        self.iterations = iterations
        self._rng = rng or random.Random()
        self.rollout_depth = rollout_depth
        self.max_candidate_moves = max_candidate_moves
        self.max_interrupt_moves = max_interrupt_moves
        self.max_search_seconds = max_search_seconds
        self.rollout_policy = rollout_policy
        self.leaf_evaluator = leaf_evaluator or evaluate_reward
        self.move_prior: MovePrior = move_prior or HeuristicMovePrior()

    def search(self, game: Game) -> ISMCTSSolverResult:
        root_player_idx = game.acting_player_idx
        root_node = ISMCTSNode()
        start = time.perf_counter()

        for _ in range(self.iterations):
            if (
                self.max_search_seconds is not None
                and time.perf_counter() - start >= self.max_search_seconds
            ):
                break

            # 1. Determinize the game for the root player.
            determinized_game = determinize(game, rng=self._rng)
            node = root_node

            unexpanded_moves = []

            # 2. Select a node to expand via UCT.
            while not determinized_game.is_over():
                if (
                    self.max_search_seconds is not None
                    and time.perf_counter() - start >= self.max_search_seconds
                ):
                    break

                legal_moves = self._candidate_moves(
                    determinized_game,
                    root_player_idx,
                )
                unexpanded_moves = node.get_unexpanded_moves(legal_moves)

                if unexpanded_moves:
                    break

                next_node = node.choose_child_uct(
                    legal_moves,
                    maximize=(
                        self.max_candidate_moves is None
                        or determinized_game.acting_player_idx == root_player_idx
                    ),
                )
                if next_node is None:
                    break
                node = next_node
                determinized_game.apply(node.move)

            # 3. Expand the node.
            if not determinized_game.is_over() and len(unexpanded_moves) > 0:
                move = self._choose_expansion_move(
                    determinized_game,
                    unexpanded_moves,
                    root_player_idx,
                )
                determinized_game.apply(move)
                new_node = ISMCTSNode(move, node)
                node.children.append(new_node)

                node = new_node

            # 4. Simulate from the expanded node.
            reward = self._simulate(determinized_game, root_player_idx)

            # 5. Backpropagate the result.
            node.backpropagate(reward)

        if not root_node.children:
            return ISMCTSSolverResult(
                move=get_action_with_policy(game, self.rollout_policy),
                visits=root_node.normalized_visits(),
            )

        best_child_move = root_node.best_child().move
        if best_child_move is None:
            # Should not happen because we gate this above.
            raise ValueError("Best child has no move")

        return ISMCTSSolverResult(
            move=best_child_move, visits=root_node.normalized_visits()
        )

    def _candidate_moves(
        self,
        game: Game,
        root_player_idx: int,
    ) -> list[GameCommand]:
        moves = game.legal_moves()
        if not moves:
            return moves

        if game.pending is not None and self.max_interrupt_moves is not None:
            return select_interrupt_moves(
                game,
                moves,
                root_player_idx=root_player_idx,
                max_moves=self.max_interrupt_moves,
            )

        if self.max_candidate_moves is None or len(moves) <= self.max_candidate_moves:
            return moves

        return self.move_prior.select_candidates(
            game,
            moves,
            root_player_idx=root_player_idx,
            max_moves=self.max_candidate_moves,
            heuristic_move=get_action_with_policy(game, MovePolicyType.HEURISTIC),
        )

    def _simulate(self, game: Game, root_player_idx: int) -> float:
        if self.rollout_depth is None:
            simulation_result = rollout(game, move_policy=self.rollout_policy)
            return 1.0 if simulation_result["winner"] == root_player_idx else 0.0

        for _ in range(self.rollout_depth):
            if game.is_over():
                break
            game.apply(get_action_with_policy(game, self.rollout_policy))

        return self.leaf_evaluator(game, root_player_idx)

    def _choose_expansion_move(
        self,
        game: Game,
        moves: list[GameCommand],
        root_player_idx: int,
    ) -> GameCommand:
        if self.max_candidate_moves is None:
            return self._rng.choice(moves)

        scored_moves = [
            (self.move_prior.score(game, move, root_player_idx), -idx, move)
            for idx, move in enumerate(moves)
        ]
        if game.acting_player_idx == root_player_idx:
            return max(scored_moves, key=lambda item: (item[0], item[1]))[2]
        return min(scored_moves, key=lambda item: (item[0], -item[1]))[2]
