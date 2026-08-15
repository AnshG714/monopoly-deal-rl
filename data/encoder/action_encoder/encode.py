"""Encode legal moves / CSV visit payloads into fixed action feature vectors.

v1 layout (``ACTION_DIM``):
  kind one-hot | move-scoring bucket one-hot | hand_index/10 | color one-hot
"""

from __future__ import annotations

from typing import Any

from models.game.commands import GameCommand
from serialization.moves import move_to_dict

from data.encoder.dims import one_hot

from .layout import (
    ACTION_DIM,
    BUCKET_DIM,
    BUCKET_TO_INDEX,
    COLOR_TO_INDEX,
    KIND_BUCKET,
    KIND_DIM,
    KIND_TO_INDEX,
    MAX_HAND_INDEX,
)


def encode_action(move: GameCommand) -> list[float]:
    """Encode a live command (MCTS inference)."""
    return encode_action_payload(move_to_dict(move))


def encode_action_payload(payload: dict[str, Any]) -> list[float]:
    """Encode serialized ``{kind, params}`` from self-play CSV visits."""
    kind = str(payload.get("kind") or "")
    params = payload.get("params") or {}
    if not isinstance(params, dict):
        params = {}

    kind_vec = one_hot(KIND_TO_INDEX.get(kind), KIND_DIM)
    bucket = KIND_BUCKET.get(kind, "other")
    bucket_vec = one_hot(BUCKET_TO_INDEX[bucket], BUCKET_DIM)

    hand_index = params.get("hand_index")
    if isinstance(hand_index, (int, float)):
        hand_vec = [min(float(hand_index), MAX_HAND_INDEX) / MAX_HAND_INDEX]
    else:
        hand_vec = [0.0]

    color = _extract_color(params)
    color_vec = one_hot(COLOR_TO_INDEX.get(color) if color else None, len(COLOR_TO_INDEX))

    vector = kind_vec + bucket_vec + hand_vec + color_vec
    if len(vector) != ACTION_DIM:
        raise RuntimeError(f"expected {ACTION_DIM} action features, got {len(vector)}")
    return vector


def _extract_color(params: dict[str, Any]) -> str | None:
    for key in (
        "color",
        "into_color",
        "take_into_color",
        "target_color",
        "rent_color",
    ):
        value = params.get(key)
        if value is None:
            continue
        if hasattr(value, "value"):
            return str(value.value)
        return str(value)
    return None
