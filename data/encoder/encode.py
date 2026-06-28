"""Orchestrate full DecisionRow state encoding."""

from __future__ import annotations

from data.decision_row import DecisionRow

from .encode_bank import encode_bank
from .encode_global import encode_global
from .encode_hand import encode_hand
from .encode_pending import encode_pending
from .encode_properties import encode_properties
from .layout import FEATURE_LAYOUT, STATE_DIM


def encode_decision_row(row: DecisionRow) -> list[float]:
    """Return a normalized feature vector of length ``STATE_DIM``."""
    parts = [
        encode_global(row),
        encode_bank(row.viewer_bank, row.opponent_bank),
        encode_properties(row.viewer_property_piles, row.opponent_property_piles),
        encode_pending(
            row.pending,
            row.viewer_idx,
            row.viewer_property_piles,
            row.opponent_property_piles,
        ),
        encode_hand(row.viewer_hand, row.viewer_property_piles),
    ]
    vector = [value for part in parts for value in part]
    if len(vector) != STATE_DIM:
        raise RuntimeError(f"expected {STATE_DIM} features, got {len(vector)}")
    return vector


def encode_decision_row_blocks(row: DecisionRow) -> dict[str, list[float]]:
    """Return named block vectors matching ``FEATURE_LAYOUT``."""
    bank = encode_bank(row.viewer_bank, row.opponent_bank)
    properties = encode_properties(
        row.viewer_property_piles,
        row.opponent_property_piles,
    )
    return {
        "global": encode_global(row),
        "viewer_bank": bank[: FEATURE_LAYOUT.viewer_bank.length],
        "opponent_bank": bank[FEATURE_LAYOUT.viewer_bank.length :],
        "viewer_properties": properties[: FEATURE_LAYOUT.viewer_properties.length],
        "opponent_properties": properties[FEATURE_LAYOUT.viewer_properties.length :],
        "pending": encode_pending(
            row.pending,
            row.viewer_idx,
            row.viewer_property_piles,
            row.opponent_property_piles,
        ),
        "hand": encode_hand(row.viewer_hand, row.viewer_property_piles),
    }
