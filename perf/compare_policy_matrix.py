"""Run a rollout-policy matrix through ``compare_agents``."""

from __future__ import annotations

import argparse
import csv
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mcts.consts import (  # noqa: E402
    DEFAULT_ITERS,
    DEFAULT_MAX_CANDIDATE_MOVES,
    DEFAULT_MAX_INTERRUPT_MOVES,
    DEFAULT_MAX_SEARCH_SECONDS,
    DEFAULT_PRUNING_STRATEGY,
    DEFAULT_ROLLOUT_DEPTH,
)
from perf.compare_agents import (  # noqa: E402
    POLICY_HEURISTIC,
    POLICY_RANDOM,
    SUPPORTED_POLICIES,
    BenchmarkSummary,
    compare_agents,
)

DEFAULT_MATRIX_GAMES = 20
MATRIX: tuple[tuple[str, str], ...] = (
    (POLICY_RANDOM, POLICY_RANDOM),
    (POLICY_RANDOM, POLICY_HEURISTIC),
    (POLICY_HEURISTIC, POLICY_RANDOM),
    (POLICY_HEURISTIC, POLICY_HEURISTIC),
)


def _optional_int(value: str) -> int | None:
    if value.lower() == "none":
        return None
    return int(value)


def _summary_row(
    *,
    mcts_rollout_policy: str,
    opponent_policy: str,
    summary: BenchmarkSummary,
    mcts_iters: int,
    rollout_depth: int | None,
    max_candidate_moves: int | None,
    max_interrupt_moves: int | None,
    pruning_strategy: str,
    max_search_seconds: float | None,
) -> dict[str, object]:
    return {
        "mcts_rollout_policy": mcts_rollout_policy,
        "opponent_policy": opponent_policy,
        "mcts_iters": mcts_iters,
        "rollout_depth": rollout_depth,
        "max_candidate_moves": max_candidate_moves,
        "max_interrupt_moves": max_interrupt_moves,
        "pruning_strategy": pruning_strategy,
        "max_search_seconds": max_search_seconds,
        "games": summary.games,
        "mcts_wins": summary.mcts_wins,
        "opponent_wins": summary.opponent_wins,
        "timeouts": summary.timeouts,
        "mcts_win_rate": f"{summary.win_rate:.3f}",
        "approx_95_ci_half_width": f"{summary.approx_95_ci_half_width:.3f}",
        "elapsed_s": f"{summary.elapsed_s:.1f}",
        "avg_game_s": f"{summary.avg_game_s:.2f}",
        "mcts_decisions_per_s": f"{summary.mcts_decisions_per_s:.2f}",
        "wins_by_mcts_seat": summary.wins_by_mcts_seat,
        "games_by_mcts_seat": summary.games_by_mcts_seat,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run MCTS rollout-policy comparison matrix"
    )
    parser.add_argument(
        "-n",
        "--games",
        type=int,
        default=DEFAULT_MATRIX_GAMES,
        help=(
            "paired games per matrix cell; must be even "
            f"(default: {DEFAULT_MATRIX_GAMES})"
        ),
    )
    parser.add_argument(
        "-j",
        "--workers",
        type=int,
        default=1,
        help="worker processes per matrix cell (default: 1)",
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
        default=0,
        help="first paired game seed reused for each matrix cell (default: 0)",
    )
    parser.add_argument(
        "--rollout-depth",
        type=_optional_int,
        default=DEFAULT_ROLLOUT_DEPTH,
        help=(
            "limit each MCTS rollout before static evaluation; use 'none' for "
            f"full rollouts (default: {DEFAULT_ROLLOUT_DEPTH})"
        ),
    )
    parser.add_argument(
        "--policy",
        choices=SUPPORTED_POLICIES,
        action="append",
        help="limit matrix to one policy; pass twice for two policies",
    )
    parser.add_argument(
        "--pruned",
        action="store_true",
        help="use the current heuristic candidate-pruning defaults",
    )
    parser.add_argument(
        "--pruning-strategy",
        choices=("global", "bucketed"),
        default=DEFAULT_PRUNING_STRATEGY,
        help=(
            "candidate-pruning strategy when --pruned is set "
            f"(default: {DEFAULT_PRUNING_STRATEGY})"
        ),
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
        help=(
            "stop one MCTS search after this many seconds "
            f"(default: {DEFAULT_MAX_SEARCH_SECONDS})"
        ),
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=Path("./outputs"),
        help="directory for matrix CSV output (default: outputs/)",
    )
    return parser.parse_args()


def _selected_matrix(policies: list[str] | None) -> tuple[tuple[str, str], ...]:
    if not policies:
        return MATRIX
    selected = set(policies)
    return tuple(
        (mcts_policy, opponent_policy)
        for mcts_policy, opponent_policy in MATRIX
        if mcts_policy in selected and opponent_policy in selected
    )


def main() -> None:
    args = _parse_args()
    matrix = _selected_matrix(args.policy)
    max_candidate_moves = DEFAULT_MAX_CANDIDATE_MOVES if args.pruned else None
    max_interrupt_moves = DEFAULT_MAX_INTERRUPT_MOVES if args.pruned else None

    rows: list[dict[str, object]] = []
    for mcts_rollout_policy, opponent_policy in matrix:
        print(
            "\n"
            f"=== MCTS rollout={mcts_rollout_policy} "
            f"vs opponent={opponent_policy} ===",
            flush=True,
        )
        summary = compare_agents(
            num_games=args.games,
            workers=args.workers,
            mcts_iters=args.mcts_iters,
            seed=args.seed,
            mcts_rollout_policy=mcts_rollout_policy,
            opponent_policy=opponent_policy,
            rollout_depth=args.rollout_depth,
            max_candidate_moves=max_candidate_moves,
            max_interrupt_moves=max_interrupt_moves,
            pruning_strategy=args.pruning_strategy,
            max_game_seconds=args.max_game_seconds,
            max_search_seconds=args.max_search_seconds,
        )
        row = _summary_row(
            mcts_rollout_policy=mcts_rollout_policy,
            opponent_policy=opponent_policy,
            summary=summary,
            mcts_iters=args.mcts_iters,
            rollout_depth=args.rollout_depth,
            max_candidate_moves=max_candidate_moves,
            max_interrupt_moves=max_interrupt_moves,
            pruning_strategy=args.pruning_strategy,
            max_search_seconds=args.max_search_seconds,
        )
        rows.append(row)
        print(
            "cell result: "
            f"MCTS {summary.mcts_wins}, Opponent {summary.opponent_wins}, "
            f"Timeouts {summary.timeouts}, "
            f"win_rate={summary.win_rate:.3f} "
            f"+/- {summary.approx_95_ci_half_width:.3f}",
            flush=True,
        )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    output_path = (
        args.output_dir
        / f"mcts_policy_matrix_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    )
    with output_path.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nWrote {output_path}")


if __name__ == "__main__":
    main()
