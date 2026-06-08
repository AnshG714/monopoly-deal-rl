"""Compare MCTS vs. heuristic performance on the same game."""

from __future__ import annotations

import argparse
import os
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Callable

from mcts.consts import DEFAULT_ITERS
from mcts.solver import ISMCTSSolver
from models.game.commands import GameCommand
from models.game.game import Game
from rollout import choose_move

DEFAULT_NUM_GAMES = 1000


def run_game(
    agent1: Callable[[Game], GameCommand],
    agent2: Callable[[Game], GameCommand],
) -> int:
    """Play one game and return the winner index (0 or 1)."""
    game = Game()
    game.start_match()

    while not game.is_over():
        if game.acting_player_idx == 0:
            move = agent1(game)
        else:
            move = agent2(game)
        game.apply(move)

    winner = game.winner_idx()
    assert winner is not None
    return winner


def _run_single_game(mcts_iters: int) -> int:
    """Worker entry point: play one MCTS vs. heuristic game."""
    mcts = ISMCTSSolver(iterations=mcts_iters)
    return run_game(mcts.search, choose_move)


def compare_agents(
    *,
    num_games: int = DEFAULT_NUM_GAMES,
    workers: int | None = None,
    mcts_iters: int = DEFAULT_ITERS,
) -> tuple[int, int]:
    """Run games across worker processes (use ``workers=1`` for a single process)."""
    if workers is None:
        workers = os.process_cpu_count() or 1
    workers = min(workers, num_games)

    wins1 = 0
    wins2 = 0
    completed = 0

    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = [
            executor.submit(_run_single_game, mcts_iters) for _ in range(num_games)
        ]
        for future in as_completed(futures):
            winner = future.result()
            if winner == 0:
                wins1 += 1
            else:
                wins2 += 1
            completed += 1
            print(
                f"{completed}/{num_games} — MCTS {wins1}, Heuristic {wins2}",
                flush=True,
            )

    return wins1, wins2


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Benchmark MCTS vs. heuristic rollout policy"
    )
    parser.add_argument(
        "-n",
        "--games",
        type=int,
        default=DEFAULT_NUM_GAMES,
        help=f"number of games to play (default: {DEFAULT_NUM_GAMES})",
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
        "-o",
        "--output-dir",
        type=Path,
        default=Path("./outputs"),
        help="directory for result files (default: outputs/)",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    effective_workers = args.workers or os.process_cpu_count() or 1
    effective_workers = min(effective_workers, args.games)

    print(
        f"Running {args.games} games across {effective_workers} worker"
        f"{'' if effective_workers == 1 else 's'}..."
    )

    start = time.perf_counter()
    wins1, wins2 = compare_agents(
        num_games=args.games,
        workers=args.workers,
        mcts_iters=args.mcts_iters,
    )
    elapsed = time.perf_counter() - start

    result = (
        f"MCTS wins: {wins1}, Heuristic wins: {wins2} "
        f"({args.games} games in {elapsed:.1f}s)"
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    output_path = (
        args.output_dir
        / f"mcts_vs_heuristic_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    )
    output_path.write_text(result + "\n")

    print(result)
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
