"""Random legal-move rollout policy."""

from __future__ import annotations

import random

from models.game.game import Game, GameCommand


def choose_random_move(game: Game, rng: random.Random | None = None) -> GameCommand:
    """Pick uniformly from the current legal moves."""
    moves = game.legal_moves()
    if not moves:
        raise ValueError("No legal moves found")
    return (rng or game._rng).choice(moves)
