from dataclasses import dataclass
import random
import time

from mcts.solver import ISMCTSSolver
from models.game.game import Game
from rollout import MovePolicyType, get_action_with_policy

MAX_STEPS = 10_000


@dataclass(frozen=True)
class GameSpec:
    seed: int
    mcts_seat: int
    mcts_rollout_policy: MovePolicyType
    opponent_policy: MovePolicyType
    mcts_iters: int
    rollout_depth: int | None
    max_candidate_moves: int | None
    max_interrupt_moves: int | None
    pruning_strategy: str
    max_game_seconds: float | None
    max_search_seconds: float | None


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


def run_game(spec: GameSpec) -> GameResult:
    """Play one seeded game and return the result from MCTS' perspective."""
    game = Game(rng=random.Random(spec.seed))
    game.start_match()

    solver_seed = spec.seed * 2 + spec.mcts_seat
    mcts = ISMCTSSolver(
        iterations=spec.mcts_iters,
        rng=random.Random(solver_seed),
        rollout_depth=spec.rollout_depth,
        max_candidate_moves=spec.max_candidate_moves,
        max_interrupt_moves=spec.max_interrupt_moves,
        pruning_strategy=spec.pruning_strategy,
        max_search_seconds=spec.max_search_seconds,
        rollout_policy=spec.mcts_rollout_policy,
    )

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

        if game.acting_player_idx == spec.mcts_seat:
            result = mcts.search(game)
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
