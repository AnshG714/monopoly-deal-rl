"""Heuristic rollout: play a game to completion using the policy in policy.py.

Includes a CLI entry point (``python -m rollout.rollout``) for running a
single game with optional verbose move-by-move output.
"""

from __future__ import annotations

import argparse
import random
import secrets
from typing import Callable

from models.game.game import Game

from rollout.policy import choose_move

DEFAULT_MAX_STEPS = 10_000

# on_step callback receives (step_number, game_before_apply, chosen_move).
StepCallback = Callable[[int, Game, object], None]


def rollout(
    game: Game,
    *,
    max_steps: int = DEFAULT_MAX_STEPS,
    on_step: StepCallback | None = None,
) -> dict:
    """Play ``game`` to completion using heuristic policy. Returns steps taken and the winner."""
    steps = 0
    while steps < max_steps:
        winner = game.winner_idx()
        if winner is not None:
            return {"steps": steps, "winner": winner}

        move = choose_move(game)
        if on_step is not None:
            on_step(steps, game, move)
        game.apply(move)
        steps += 1

    raise RuntimeError(f"Hit step limit ({max_steps}) without a winner")


def _move_label(game: Game, move: object) -> str:
    """Human-readable label: command name + who is acting if it's an interrupt."""
    name = type(move).__name__
    acting = game.players[game.acting_player_idx].name
    turn = game.players[game.current_player_idx].name
    if acting != turn:
        return f"{name} ({acting} responds)"
    return name


def _verbose_step(step: int, game: Game, move: object) -> None:
    """on_step callback that prints each move."""
    sets = [p.complete_set_count() for p in game.players]
    print(
        f"{step + 1:4d}  turn={game.players[game.current_player_idx].name}  "
        f"sets={sets}  {_move_label(game, move)}"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Play one rollout game")
    parser.add_argument(
        "--seed",
        "-s",
        type=int,
        default=None,
        help="RNG seed (default: random)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="print each move",
    )
    parser.add_argument("--max-steps", "-m", type=int, default=DEFAULT_MAX_STEPS)
    args = parser.parse_args(argv)

    seed = args.seed if args.seed is not None else secrets.randbelow(2**31)
    game = Game(rng=random.Random(seed))
    game.start_match()

    if args.verbose:
        print(f"seed={seed}")
        for i, player in enumerate(game.players):
            print(
                f"  {player.name}: {len(player.hand)} cards, "
                f"{player.complete_set_count()} sets"
            )
        print()

    result = rollout(
        game,
        max_steps=args.max_steps,
        on_step=_verbose_step if args.verbose else None,
    )

    win = game.winner_idx()
    winner = game.players[win].name if win is not None else "none"
    sets = [p.complete_set_count() for p in game.players]
    if args.verbose:
        print(f"\n>>> {winner} wins ({win}) in {result['steps']} steps")
    else:
        print(f"seed={seed}  steps={result['steps']}  winner={winner}  sets={sets}")

    return 0
