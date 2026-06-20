from __future__ import annotations

import argparse
import time
from copy import deepcopy
from dataclasses import replace
from pathlib import Path

from mcts import GameSpec, run_game
from mcts.solver import ISMCTSSolverResult
from models.game.game import Game

from .csv_io import write_decision_rows_csv
from .decision_row import DecisionRow

DEFAULT_OUTPUT = Path(__file__).resolve().parent / "self_play_data.csv"


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


def generate_self_play_data(
    num_games: int,
    *,
    seed_start: int = 0,
) -> list[DecisionRow]:
    if num_games < 1:
        raise ValueError("num_games must be at least 1")

    rows: list[DecisionRow] = []
    for game_idx in range(num_games):
        spec = GameSpec(seed=seed_start + game_idx, both_players_mcts=True)
        rows.extend(generate_self_play_data_for_game(spec))
    return rows


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
        "--seed-start",
        type=int,
        default=0,
        help="first game seed (default: 0)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"output CSV path (default: {DEFAULT_OUTPUT})",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    start = time.perf_counter()
    print(f"Generating {args.games} game(s)...", flush=True)
    rows = generate_self_play_data(args.games, seed_start=args.seed_start)
    write_decision_rows_csv(args.output, rows)
    elapsed = time.perf_counter() - start
    print(
        f"Wrote {len(rows)} decisions to {args.output} in {elapsed:.1f}s",
        flush=True,
    )


if __name__ == "__main__":
    main()
