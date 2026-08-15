from dataclasses import dataclass
import random
import time
from typing import Callable

from mcts.consts import (
    DEFAULT_ITERS,
    DEFAULT_MAX_CANDIDATE_MOVES,
    DEFAULT_MAX_INTERRUPT_MOVES,
    DEFAULT_MAX_SEARCH_SECONDS,
    DEFAULT_ROLLOUT_DEPTH,
)
from mcts.move_prior import MovePrior
from mcts.solver import ISMCTSSolver, ISMCTSSolverResult
from models.game.game import Game
from rollout import MovePolicyType, get_action_with_policy

MAX_STEPS = 10_000

DecisionCallback = Callable[[Game, ISMCTSSolverResult, int], None]


@dataclass(frozen=True)
class GameSpec:
    """One seeded game configuration. Only ``seed`` is required.

    By default only ``mcts_seat`` runs MCTS and the other seat uses
    ``opponent_policy``. Set ``both_players_mcts=True`` for symmetric
    self-play with the same search config on both sides.
    """

    seed: int
    mcts_seat: int = 0
    both_players_mcts: bool = False
    mcts_rollout_policy: MovePolicyType = MovePolicyType.HEURISTIC
    opponent_policy: MovePolicyType = MovePolicyType.HEURISTIC
    mcts_iters: int = DEFAULT_ITERS
    rollout_depth: int | None = DEFAULT_ROLLOUT_DEPTH
    max_candidate_moves: int | None = DEFAULT_MAX_CANDIDATE_MOVES
    max_interrupt_moves: int | None = DEFAULT_MAX_INTERRUPT_MOVES
    max_game_seconds: float | None = None
    max_search_seconds: float | None = DEFAULT_MAX_SEARCH_SECONDS
    leaf_evaluator: Callable[[Game, int], float] | None = None
    move_prior: MovePrior | None = None

    @property
    def mcts_seats(self) -> tuple[int, ...]:
        if self.both_players_mcts:
            return (0, 1)
        return (self.mcts_seat,)


@dataclass(frozen=True)
class GameResult:
    seed: int
    mcts_seat: int
    winner: int
    timed_out: bool
    steps: int
    mcts_decisions: int
    elapsed_s: float

    @property
    def mcts_won(self) -> bool:
        return not self.timed_out and self.winner == self.mcts_seat


def _make_solver(spec: GameSpec, seat: int) -> ISMCTSSolver:
    return ISMCTSSolver(
        iterations=spec.mcts_iters,
        rng=random.Random(spec.seed * 2 + seat),
        rollout_depth=spec.rollout_depth,
        max_candidate_moves=spec.max_candidate_moves,
        max_interrupt_moves=spec.max_interrupt_moves,
        max_search_seconds=spec.max_search_seconds,
        rollout_policy=spec.mcts_rollout_policy,
        leaf_evaluator=spec.leaf_evaluator,
        move_prior=spec.move_prior,
    )


def run_game(
    spec: GameSpec,
    decision_callback: DecisionCallback | None = None,
) -> GameResult:
    """Play one seeded game and return the result from ``spec.mcts_seat``'s view."""
    game = Game(rng=random.Random(spec.seed))
    game.start_match()

    solvers = {seat: _make_solver(spec, seat) for seat in spec.mcts_seats}

    steps = 0
    mcts_decisions = 0
    start = time.perf_counter()
    while not game.is_over() and steps < MAX_STEPS:
        elapsed_s = time.perf_counter() - start
        if spec.max_game_seconds is not None and elapsed_s >= spec.max_game_seconds:
            return GameResult(
                seed=spec.seed,
                mcts_seat=spec.mcts_seat,
                winner=-1,
                timed_out=True,
                steps=steps,
                mcts_decisions=mcts_decisions,
                elapsed_s=elapsed_s,
            )

        acting_idx = game.acting_player_idx
        solver = solvers.get(acting_idx)
        if solver is not None:
            result = solver.search(game)
            if decision_callback is not None:
                decision_callback(game, result, steps)
            move = result.move
            mcts_decisions += 1
        else:
            move = get_action_with_policy(game, spec.opponent_policy)
        game.apply(move)
        steps += 1

    winner = game.winner_idx()
    if winner is None:
        raise RuntimeError(
            f"Game did not finish after {MAX_STEPS} steps "
            f"(seed={spec.seed}, mcts_seat={spec.mcts_seat})"
        )

    return GameResult(
        seed=spec.seed,
        mcts_seat=spec.mcts_seat,
        winner=winner,
        timed_out=False,
        steps=steps,
        mcts_decisions=mcts_decisions,
        elapsed_s=time.perf_counter() - start,
    )
