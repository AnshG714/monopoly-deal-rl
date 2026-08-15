"""Encode viewer hand features."""

from __future__ import annotations

from collections.abc import Sequence

from models.cards.action import ActionCard
from models.cards.base import Card
from models.cards.money import MoneyCard
from models.cards.property import PropertyCard, PropertySet
from models.cards.rent import RentCard, WildRentCard
from models.game.commands.rent import rent_card_allows_color, rent_m_due_for_color
from models.player import Player

from .layout import (
    ACTION_TYPES,
    BANK_DENOMINATIONS,
    COLORS,
    normalize_hand_count,
    normalize_rent,
    player_with_property_sets,
)


def encode_hand(
    hand: Sequence[Card],
    viewer_piles: Sequence[PropertySet],
) -> list[float]:
    viewer = player_with_property_sets(viewer_piles)
    return (
        _encode_hand_money(hand)
        + _encode_hand_property_eligibility(hand)
        + _encode_hand_max_charge(hand, viewer)
        + _encode_hand_actions(hand)
    )


def _encode_hand_money(hand: Sequence[Card]) -> list[float]:
    counts = dict.fromkeys(BANK_DENOMINATIONS, 0)
    for card in hand:
        if isinstance(card, MoneyCard) and card.value in counts:
            counts[card.value] += 1
    return [
        normalize_hand_count(counts[denomination])
        for denomination in BANK_DENOMINATIONS
    ]


def _encode_hand_property_eligibility(hand: Sequence[Card]) -> list[float]:
    counts = [0] * len(COLORS)
    for card in hand:
        if not isinstance(card, PropertyCard):
            continue
        for color in COLORS:
            if card.can_count_as(color):
                counts[COLORS.index(color)] += 1
    return [normalize_hand_count(count) for count in counts]


def _encode_hand_max_charge(hand: Sequence[Card], viewer: Player) -> list[float]:
    charges = [0.0] * len(COLORS)
    for color in COLORS:
        board_rent = rent_m_due_for_color(viewer, color)
        if board_rent <= 0:
            continue
        has_legal_rent_card = any(
            isinstance(card, (RentCard, WildRentCard))
            and rent_card_allows_color(card, color)
            for card in hand
        )
        if has_legal_rent_card:
            charges[COLORS.index(color)] = normalize_rent(board_rent)
    return charges


def _encode_hand_actions(hand: Sequence[Card]) -> list[float]:
    action_counts = dict.fromkeys(ACTION_TYPES, 0)
    rent_count = 0
    for card in hand:
        if isinstance(card, ActionCard):
            action_counts[card.action_type] += 1
        elif isinstance(card, (RentCard, WildRentCard)):
            rent_count += 1
    return [
        normalize_hand_count(action_counts[action_type]) for action_type in ACTION_TYPES
    ] + [normalize_hand_count(rent_count)]
