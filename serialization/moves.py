"""Encode legal moves for API clients."""

from __future__ import annotations

import dataclasses
from enum import Enum
from typing import Any

from models.cards.property import Color
from models.game.commands import GameCommand
from models.game.game import Game


def move_label(game: Game, move: GameCommand) -> str:
    acting = game.players[game.acting_player_idx].name
    turn = game.players[game.current_player_idx].name
    name = type(move).__name__
    if acting != turn:
        return f"{name} ({acting} responds)"
    return name


def _serialize_param(value: Any) -> Any:
    if isinstance(value, Color):
        return value.value
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, list):
        return [_serialize_param(item) for item in value]
    return value


def encode_move(game: Game, move_id: int, move: GameCommand) -> dict:
    params: dict[str, Any] = {}
    if dataclasses.is_dataclass(move):
        for field in dataclasses.fields(move):
            params[field.name] = _serialize_param(getattr(move, field.name))

    return {
        "id": move_id,
        "kind": type(move).__name__,
        "label": move_label(game, move),
        "params": params,
    }


def encode_moves(game: Game, moves: list[GameCommand]) -> list[dict]:
    return [encode_move(game, move_id, move) for move_id, move in enumerate(moves)]
