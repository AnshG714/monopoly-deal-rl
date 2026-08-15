"""Encode viewer and opponent bank denomination counts."""

from __future__ import annotations

from collections.abc import Sequence

from models.player import BankableCard

from .layout import BANK_DENOMINATIONS, normalize_bank_count


def encode_bank(
    viewer_bank: Sequence[BankableCard],
    opponent_bank: Sequence[BankableCard],
) -> list[float]:
    return _encode_player_bank(viewer_bank) + _encode_player_bank(opponent_bank)


def _encode_player_bank(bank: Sequence[BankableCard]) -> list[float]:
    counts = dict.fromkeys(BANK_DENOMINATIONS, 0)
    for card in bank:
        if card.value in counts:
            counts[card.value] += 1
    return [
        normalize_bank_count(counts[denomination], denomination)
        for denomination in BANK_DENOMINATIONS
    ]
