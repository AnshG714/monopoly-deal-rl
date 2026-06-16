"""Compare MCTS vs. another policy with paired, seeded games."""

from __future__ import annotations

import argparse
import math
import os
import random
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable

from mcts.consts import (
    DEFAULT_ITERS,
    DEFAULT_MAX_CANDIDATE_MOVES,
    DEFAULT_MAX_INTERRUPT_MOVES,
    DEFAULT_MAX_SEARCH_SECONDS,
    DEFAULT_PRUNING_STRATEGY,
    DEFAULT_ROLLOUT_DEPTH,
)
from mcts.solver import ISMCTSSolver
from models.game.commands import GameCommand
from models.game.game import Game
from rollout import MovePolicyType, get_action_with_policy

DEFAULT_NUM_GAMES = 100
DEFAULT_SEED = 0
MAX_STEPS = 10_000
POLICY_HEURISTIC = MovePolicyType.HEURISTIC.value
POLICY_RANDOM = MovePolicyType.RANDOM.value
SUPPORTED_POLICIES = tuple(policy.value for policy in MovePolicyType)
MovePolicy = Callable[[Game], GameCommand]


def _optional_int(value: str) -> int | None:
    if value.lower() == "none":
        return None
    return int(value)


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


@dataclass(frozen=True)
class BenchmarkSummary:
    results: tuple[GameResult, ...]
    elapsed_s: float

    @property
    def games(self) -> int:
        return len(self.results)

    @property
    def mcts_wins(self) -> int:
        return sum(1 for result in self.results if result.mcts_won)

    @property
    def opponent_wins(self) -> int:
        return sum(
            1
            for result in self.results
            if not result.timed_out and result.winner != result.mcts_seat
        )

    @property
    def heuristic_wins(self) -> int:
        return self.opponent_wins

    @property
    def timeouts(self) -> int:
        return sum(1 for result in self.results if result.timed_out)

    @property
    def win_rate(self) -> float:
        completed_games = self.games - self.timeouts
        if completed_games == 0:
            return 0.0
        return self.mcts_wins / completed_games

    @property
    def avg_game_s(self) -> float:
        if self.games == 0:
            return 0.0
        return self.elapsed_s / self.games

    @property
    def mcts_decisions_per_s(self) -> float:
        total_decisions = sum(result.mcts_decisions for result in self.results)
        if self.elapsed_s <= 0:
            return 0.0
        return total_decisions / self.elapsed_s

    @property
    def wins_by_mcts_seat(self) -> dict[int, int]:
        return {
            seat: sum(
                1
                for result in self.results
                if result.mcts_seat == seat and result.mcts_won
            )
            for seat in (0, 1)
        }

    @property
    def games_by_mcts_seat(self) -> dict[int, int]:
        return {
            seat: sum(1 for result in self.results if result.mcts_seat == seat)
            for seat in (0, 1)
        }

    @property
    def approx_95_ci_half_width(self) -> float:
        if self.games == 0:
            return 0.0
        z = 1.96
        completed_games = self.games - self.timeouts
        if completed_games == 0:
            return 0.0
        p = self.mcts_wins / completed_games
        denominator = 1 + z**2 / completed_games
        numerator = p * (1 - p) + z**2 / (4 * completed_games)
        return z * math.sqrt(numerator / completed_games) / denominator


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


def _build_specs(
    *,
    num_games: int,
    seed: int,
    mcts_rollout_policy: MovePolicyType,
    opponent_policy: MovePolicyType,
    mcts_iters: int,
    rollout_depth: int | None,
    max_candidate_moves: int | None,
    max_interrupt_moves: int | None,
    pruning_strategy: str,
    max_game_seconds: float | None,
    max_search_seconds: float | None,
) -> list[GameSpec]:
    if num_games < 2:
        raise ValueError("paired benchmark needs at least 2 games")
    if num_games % 2 != 0:
        raise ValueError("paired benchmark needs an even --games value")

    specs: list[GameSpec] = []
    for pair_idx in range(num_games // 2):
        game_seed = seed + pair_idx
        specs.append(
            GameSpec(
                game_seed,
                0,
                mcts_rollout_policy,
                opponent_policy,
                mcts_iters,
                rollout_depth,
                max_candidate_moves,
                max_interrupt_moves,
                pruning_strategy,
                max_game_seconds,
                max_search_seconds,
            )
        )
        specs.append(
            GameSpec(
                game_seed,
                1,
                mcts_rollout_policy,
                opponent_policy,
                mcts_iters,
                rollout_depth,
                max_candidate_moves,
                max_interrupt_moves,
                pruning_strategy,
                max_game_seconds,
                max_search_seconds,
            )
        )
    return specs


def compare_agents(
    *,
    num_games: int = DEFAULT_NUM_GAMES,
    workers: int | None = None,
    mcts_iters: int = DEFAULT_ITERS,
    seed: int = DEFAULT_SEED,
    mcts_rollout_policy: MovePolicyType = MovePolicyType.HEURISTIC,
    opponent_policy: MovePolicyType = MovePolicyType.HEURISTIC,
    rollout_depth: int | None = DEFAULT_ROLLOUT_DEPTH,
    max_candidate_moves: int | None = DEFAULT_MAX_CANDIDATE_MOVES,
    max_interrupt_moves: int | None = DEFAULT_MAX_INTERRUPT_MOVES,
    pruning_strategy: str = DEFAULT_PRUNING_STRATEGY,
    max_game_seconds: float | None = None,
    max_search_seconds: float | None = DEFAULT_MAX_SEARCH_SECONDS,
) -> BenchmarkSummary:
    """Run paired, seat-swapped games across worker processes."""
    specs = _build_specs(
        num_games=num_games,
        seed=seed,
        mcts_rollout_policy=mcts_rollout_policy,
        opponent_policy=opponent_policy,
        mcts_iters=mcts_iters,
        rollout_depth=rollout_depth,
        max_candidate_moves=max_candidate_moves,
        max_interrupt_moves=max_interrupt_moves,
        pruning_strategy=pruning_strategy,
        max_game_seconds=max_game_seconds,
        max_search_seconds=max_search_seconds,
    )
    if workers is None:
        workers = os.process_cpu_count() or 1
    workers = min(workers, len(specs))

    results: list[GameResult] = []

    def record_progress(result: GameResult) -> None:
        results.append(result)
        mcts_wins = sum(1 for item in results if item.mcts_won)
        opponent_wins = sum(
            1
            for item in results
            if not item.timed_out and item.winner != item.mcts_seat
        )
        timeouts = sum(1 for item in results if item.timed_out)
        print(
            f"{len(results)}/{len(specs)} - "
            f"MCTS {mcts_wins}, Opponent {opponent_wins}, "
            f"Timeouts {timeouts} "
            f"(seed={result.seed}, seat={result.mcts_seat}, "
            f"timeout={result.timed_out}, "
            f"{result.elapsed_s:.1f}s)",
            flush=True,
        )

    start = time.perf_counter()
    if workers == 1:
        for spec in specs:
            record_progress(run_game(spec))
    else:
        try:
            with ProcessPoolExecutor(max_workers=workers) as executor:
                futures = [executor.submit(run_game, spec) for spec in specs]
                for future in as_completed(futures):
                    record_progress(future.result())
        except PermissionError as error:
            print(
                f"Process pool unavailable ({error}); falling back to serial.",
                flush=True,
            )
            results.clear()
            for spec in specs:
                record_progress(run_game(spec))

    results.sort(key=lambda result: (result.seed, result.mcts_seat))
    return BenchmarkSummary(tuple(results), time.perf_counter() - start)


def _summary_text(
    summary: BenchmarkSummary,
    *,
    mcts_iters: int,
    seed: int,
    mcts_rollout_policy: MovePolicyType,
    opponent_policy: MovePolicyType,
    rollout_depth: int | None,
    max_candidate_moves: int | None,
    max_interrupt_moves: int | None,
    pruning_strategy: str,
    max_game_seconds: float | None,
    max_search_seconds: float | None,
) -> str:
    lines = [
        "MCTS policy benchmark",
        f"games: {summary.games}",
        f"mcts_iters: {mcts_iters}",
        f"mcts_rollout_policy: {mcts_rollout_policy.value}",
        f"opponent_policy: {opponent_policy.value}",
        f"rollout_depth: {rollout_depth}",
        f"max_candidate_moves: {max_candidate_moves}",
        f"max_interrupt_moves: {max_interrupt_moves}",
        f"pruning_strategy: {pruning_strategy}",
        f"max_game_seconds: {max_game_seconds}",
        f"max_search_seconds: {max_search_seconds}",
        f"seed_start: {seed}",
        f"mcts_wins: {summary.mcts_wins}",
        f"opponent_wins: {summary.opponent_wins}",
        f"timeouts: {summary.timeouts}",
        f"mcts_win_rate: {summary.win_rate:.3f}",
        f"approx_95_ci_half_width: {summary.approx_95_ci_half_width:.3f}",
        f"elapsed_s: {summary.elapsed_s:.1f}",
        f"avg_game_s: {summary.avg_game_s:.2f}",
        f"mcts_decisions_per_s: {summary.mcts_decisions_per_s:.2f}",
        f"wins_by_mcts_seat: {summary.wins_by_mcts_seat}",
        f"games_by_mcts_seat: {summary.games_by_mcts_seat}",
        "",
        "seed,mcts_seat,winner,mcts_won,timed_out,steps,mcts_decisions,elapsed_s",
    ]
    for result in summary.results:
        lines.append(
            f"{result.seed},{result.mcts_seat},{result.winner},"
            f"{int(result.mcts_won)},{int(result.timed_out)},"
            f"{result.steps},{result.mcts_decisions},{result.elapsed_s:.3f}"
        )
    return "\n".join(lines)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark MCTS vs. another policy")
    parser.add_argument(
        "-n",
        "--games",
        type=int,
        default=DEFAULT_NUM_GAMES,
        help=(
            f"total paired games to play; must be even "
            f"(default: {DEFAULT_NUM_GAMES})"
        ),
    )
    parser.add_argument(
        "-j",
        "--workers",
        type=int,
        default=None,
        help="worker processes (default: CPU count; use 1 for single-process)",
    )
    parser.add_argument(
        "--mcts-iters",
        type=int,
        default=DEFAULT_ITERS,
        help=f"MCTS iterations per move (default: {DEFAULT_ITERS})",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help=f"first paired game seed (default: {DEFAULT_SEED})",
    )
    parser.add_argument(
        "--mcts-rollout-policy",
        choices=SUPPORTED_POLICIES,
        default=POLICY_HEURISTIC,
        help="policy used inside MCTS simulations",
    )
    parser.add_argument(
        "--opponent-policy",
        choices=SUPPORTED_POLICIES,
        default=POLICY_HEURISTIC,
        help="policy used by the non-MCTS opponent",
    )
    parser.add_argument(
        "--rollout-depth",
        type=_optional_int,
        default=DEFAULT_ROLLOUT_DEPTH,
        help="limit each MCTS rollout to this many policy moves before evaluation; use 'none' for full rollouts",
    )
    parser.add_argument(
        "--max-candidate-moves",
        type=_optional_int,
        default=DEFAULT_MAX_CANDIDATE_MOVES,
        help="cap large MCTS move lists to the top K one-step evaluator moves; use 'none' to disable",
    )
    parser.add_argument(
        "--max-interrupt-moves",
        type=_optional_int,
        default=DEFAULT_MAX_INTERRUPT_MOVES,
        help="cap pending interrupt move lists to the top K interrupt-scored moves; use 'none' to disable",
    )
    parser.add_argument(
        "--pruning-strategy",
        choices=("global", "bucketed"),
        default=DEFAULT_PRUNING_STRATEGY,
        help="strategy used when --max-candidate-moves prunes legal moves",
    )
    parser.add_argument(
        "--max-game-seconds",
        type=float,
        default=None,
        help="record a timeout if a single benchmark game exceeds this wall time",
    )
    parser.add_argument(
        "--max-search-seconds",
        type=float,
        default=DEFAULT_MAX_SEARCH_SECONDS,
        help="stop a single MCTS search after this many seconds and use the best current child",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=Path("./outputs"),
        help="directory for result files (default: outputs/)",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    mcts_rollout_policy = MovePolicyType(args.mcts_rollout_policy)
    opponent_policy = MovePolicyType(args.opponent_policy)
    specs = _build_specs(
        num_games=args.games,
        seed=args.seed,
        mcts_rollout_policy=mcts_rollout_policy,
        opponent_policy=opponent_policy,
        mcts_iters=args.mcts_iters,
        rollout_depth=args.rollout_depth,
        max_candidate_moves=args.max_candidate_moves,
        max_interrupt_moves=args.max_interrupt_moves,
        pruning_strategy=args.pruning_strategy,
        max_game_seconds=args.max_game_seconds,
        max_search_seconds=args.max_search_seconds,
    )
    effective_workers = args.workers or os.process_cpu_count() or 1
    effective_workers = min(effective_workers, len(specs))

    print(
        f"Running {len(specs)} paired games across {effective_workers} worker"
        f"{'' if effective_workers == 1 else 's'}..."
    )

    summary = compare_agents(
        num_games=args.games,
        workers=args.workers,
        mcts_iters=args.mcts_iters,
        seed=args.seed,
        mcts_rollout_policy=mcts_rollout_policy,
        opponent_policy=opponent_policy,
        rollout_depth=args.rollout_depth,
        max_candidate_moves=args.max_candidate_moves,
        max_interrupt_moves=args.max_interrupt_moves,
        pruning_strategy=args.pruning_strategy,
        max_game_seconds=args.max_game_seconds,
        max_search_seconds=args.max_search_seconds,
    )
    result_text = _summary_text(
        summary,
        mcts_iters=args.mcts_iters,
        seed=args.seed,
        mcts_rollout_policy=mcts_rollout_policy,
        opponent_policy=opponent_policy,
        rollout_depth=args.rollout_depth,
        max_candidate_moves=args.max_candidate_moves,
        max_interrupt_moves=args.max_interrupt_moves,
        pruning_strategy=args.pruning_strategy,
        max_game_seconds=args.max_game_seconds,
        max_search_seconds=args.max_search_seconds,
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    output_path = (
        args.output_dir / f"mcts_policy_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    )
    output_path.write_text(result_text + "\n")

    print(result_text.split("\n\n", maxsplit=1)[0])
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
