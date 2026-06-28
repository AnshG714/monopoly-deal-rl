"""Encode viewer and opponent bank denomination counts."""

from __future__ import annotations

from models.player import BankableCard

from .layout import BANK_DENOMINATIONS, BANK_DIM, normalize_bank_count


def encode_bank(
    viewer_bank: list[BankableCard],
    opponent_bank: list[BankableCard],
) -> list[float]:
    return _encode_player_bank(viewer_bank) + _encode_player_bank(opponent_bank)


def _encode_player_bank(bank: list[BankableCard]) -> list[float]:
    counts = dict.fromkeys(BANK_DENOMINATIONS, 0)
    for card in bank:
        if card.value in counts:
            counts[card.value] += 1
    return [
        normalize_bank_count(counts[denomination], denomination)
        for denomination in BANK_DENOMINATIONS
    ]


def bank_dim() -> int:
    return BANK_DIM
