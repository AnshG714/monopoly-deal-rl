"""Encode global tempo and opponent hand-size features."""

from __future__ import annotations

from data.decision_row import DecisionRow

from .layout import normalize_hand_count, normalize_turns_left


def encode_global(row: DecisionRow) -> list[float]:
    return [
        normalize_turns_left(row.plays_this_turn),
        normalize_hand_count(row.opponent_hand_size),
    ]
