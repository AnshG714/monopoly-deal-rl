from __future__ import annotations

import argparse
import threading
import time
from concurrent.futures import Future, ProcessPoolExecutor
from copy import deepcopy
from dataclasses import replace
from pathlib import Path

from mcts import GameSpec, run_game
from mcts.solver import ISMCTSSolverResult
from models.game.game import Game

from .csv_io import merge_decision_rows_csvs, write_decision_rows_csv
from .decision_row import DecisionRow

DATA_DIR = Path(__file__).resolve().parent
TEMP_DIR = DATA_DIR / "temp"
SELF_PLAY_DIR = DATA_DIR / "self_play"


def _snapshot_row(
    spec: GameSpec,
    game: Game,
    result: ISMCTSSolverResult,
    step: int,
) -> DecisionRow:
    acting_idx = game.acting_player_idx
    opponent_idx = 1 - acting_idx
    viewer = game.players[acting_idx]
    opponent = game.players[opponent_idx]

    return DecisionRow(
        seed=spec.seed,
        step=step,
        viewer_idx=acting_idx,
        chosen_move=deepcopy(result.move),
        legal_moves=deepcopy(game.legal_moves()),
        visits=dict(result.visits),
        viewer_property_piles=deepcopy(viewer.property_sets),
        viewer_hand=list(viewer.hand),
        viewer_bank=list(viewer.money_pile),
        opponent_property_piles=deepcopy(opponent.property_sets),
        opponent_bank=list(opponent.money_pile),
        opponent_hand_size=len(opponent.hand),
        plays_this_turn=game.plays_this_turn,
        pending=deepcopy(game.pending),
        timed_out=False,
        viewer_won=False,
    )


def generate_self_play_data_for_game(spec: GameSpec) -> list[DecisionRow]:
    rows: list[DecisionRow] = []

    def record_decision(game: Game, result: ISMCTSSolverResult, step: int) -> None:
        rows.append(_snapshot_row(spec, game, result, step))

    game_result = run_game(spec, decision_callback=record_decision)

    return [
        replace(
            row,
            timed_out=game_result.timed_out,
            viewer_won=not game_result.timed_out
            and game_result.winner == row.viewer_idx,
        )
        for row in rows
    ]


def default_output_path(num_games: int, seed_start: int) -> Path:
    return SELF_PLAY_DIR / f"data_{num_games}_{seed_start}.csv"


def chunk_csv_path(temp_dir: Path, seed: int) -> Path:
    return temp_dir / f"seed_{seed}.csv"


def generate_self_play_data(
    num_games: int,
    *,
    seed_start: int = 0,
    workers: int = 1,
    temp_dir: Path | None = None,
) -> list[Path]:
    if num_games < 1:
        raise ValueError("num_games must be at least 1")

    chunk_dir = temp_dir or TEMP_DIR
    chunk_dir.mkdir(parents=True, exist_ok=True)

    temp_paths: list[Path] = []
    paths_lock = threading.Lock()
    done_count = 0
    done_counter_lock = threading.Lock()

    def write_chunk(future: Future[list[DecisionRow]], seed: int) -> None:
        nonlocal done_count
        path = chunk_csv_path(chunk_dir, seed)
        try:
            rows = future.result()
        except Exception as exc:
            print(
                f"Error generating self-play data for seed {seed}: {exc}",
                flush=True,
            )
            return
        write_decision_rows_csv(path, rows)
        with paths_lock:
            temp_paths.append(path)
        with done_counter_lock:
            done_count += 1
            print(f"Done {done_count} of {num_games} games", flush=True)

    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = [
            executor.submit(
                generate_self_play_data_for_game,
                GameSpec(seed=seed_start + game_idx, both_players_mcts=True),
            )
            for game_idx in range(num_games)
        ]
        for future, game_idx in zip(futures, range(num_games), strict=True):
            seed = seed_start + game_idx
            future.add_done_callback(lambda f, s=seed: write_chunk(f, s))

    return sorted(temp_paths, key=lambda path: int(path.stem.removeprefix("seed_")))


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate self-play decision CSV")
    parser.add_argument(
        "-n",
        "--games",
        type=int,
        default=1,
        help="number of games to generate (default: 1)",
    )
    parser.add_argument(
        "-s",
        "--seed-start",
        type=int,
        default=0,
        help="first game seed (default: 0)",
    )
    parser.add_argument(
        "-w",
        "--workers",
        type=int,
        default=1,
        help="number of workers to use (default: 1)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="final merged CSV path (default: data/self_play/data_{games}_{seed_start}.csv)",
    )
    parser.add_argument(
        "--temp-dir",
        type=Path,
        default=TEMP_DIR,
        help=f"directory for per-game chunk CSVs (default: {TEMP_DIR})",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    output = args.output or default_output_path(args.games, args.seed_start)
    start = time.perf_counter()
    print(f"Generating {args.games} game(s)...", flush=True)
    chunk_paths = generate_self_play_data(
        args.games,
        seed_start=args.seed_start,
        workers=args.workers,
        temp_dir=args.temp_dir,
    )
    row_count = merge_decision_rows_csvs(chunk_paths, output)
    for path in chunk_paths:
        path.unlink(missing_ok=True)
    elapsed = time.perf_counter() - start
    print(
        f"Merged {len(chunk_paths)} chunk(s), {row_count} decisions -> {output} "
        f"in {elapsed:.1f}s",
        flush=True,
    )


if __name__ == "__main__":
    main()
