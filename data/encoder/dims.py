"""Shared encoding helpers (dimensions live in state_encoder / action_encoder layouts)."""

from __future__ import annotations


def one_hot(index: int | None, dim: int) -> list[float]:
    """Return a length-``dim`` one-hot vector (all zeros if index is invalid)."""
    vector = [0.0] * dim
    if index is not None and 0 <= index < dim:
        vector[index] = 1.0
    return vector
