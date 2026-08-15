"""Encode viewer and opponent property piles by color."""

from __future__ import annotations

from collections.abc import Sequence

from models.cards.property import (
    CARDS_IN_SET_FOR_COLOR,
    MultiColorProperty,
    PropertySet,
    WildColorProperty,
)
from models.game.commands.rent import rent_m_due_for_color
from models.player import Player

from .layout import (
    COLORS,
    FEATURES_PER_COLOR,
    normalize_rent,
    normalize_set_count,
    piles_by_color,
    player_with_property_sets,
)


def encode_properties(
    viewer_piles: Sequence[PropertySet],
    opponent_piles: Sequence[PropertySet],
) -> list[float]:
    viewer_player = player_with_property_sets(viewer_piles)
    opponent_player = player_with_property_sets(opponent_piles)
    return _encode_player_properties(
        viewer_piles, viewer_player
    ) + _encode_player_properties(opponent_piles, opponent_player)


def _encode_player_properties(
    piles: Sequence[PropertySet],
    player: Player,
) -> list[float]:
    by_color = piles_by_color(piles)
    out: list[float] = []
    for color in COLORS:
        pile = by_color.get(color)
        if pile is None:
            out.extend([0.0] * FEATURES_PER_COLOR)
            continue
        count = len(pile.cards)
        multi = sum(1 for card in pile.cards if isinstance(card, MultiColorProperty))
        wild = sum(1 for card in pile.cards if isinstance(card, WildColorProperty))
        cards_needed = max(0, CARDS_IN_SET_FOR_COLOR[color] - count)
        out.extend(
            [
                normalize_set_count(count, color),
                normalize_rent(rent_m_due_for_color(player, color)),
                1.0 if pile.has_house() else 0.0,
                1.0 if pile.has_hotel() else 0.0,
                normalize_set_count(cards_needed, color),
                normalize_set_count(multi, color),
                normalize_set_count(wild, color),
            ]
        )
    return out
