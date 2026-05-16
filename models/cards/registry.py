"""
Full Monopoly Deal deck (106 cards) per official counts.
"""

from __future__ import annotations

from collections.abc import Callable

from .action import (
    DealBreaker,
    DebtCollector,
    DoubleRent,
    ForcedDeal,
    House,
    Hotel,
    ItsMyBirthday,
    JustSayNo,
    PassGo,
    SlyDeal,
)
from .base import Card
from .money import MoneyCard
from .property import (
    Color,
    MultiColorProperty,
    SingleColorProperty,
    WildColorProperty,
)
from .rent import RentCard, WildRentCard

# Rent ladders (M) indexed by properties placed in that color — matches standard US card faces.
_RENT_BROWN = [1, 2]
_RENT_LIGHT_BLUE = [1, 2, 3]
_RENT_PINK = [1, 2, 4]
_RENT_ORANGE = [1, 3, 5]
_RENT_RED = [2, 3, 6]
_RENT_YELLOW = [2, 4, 6]
_RENT_GREEN = [2, 4, 7]
_RENT_DARK_BLUE = [3, 8]
_RENT_RAILROAD = [1, 2, 3, 4]
_RENT_UTILITY = [1, 2]


def _extend(out: list[Card], n: int, factory: Callable[[], Card]) -> None:
    out.extend(factory() for _ in range(n))


def _single_properties() -> list[Card]:
    cards: list[Card] = []
    # Brown (2)
    cards += [
        SingleColorProperty(Color.BROWN, "Mediterranean Avenue", _RENT_BROWN, 1),
        SingleColorProperty(Color.BROWN, "Baltic Avenue", _RENT_BROWN, 1),
    ]
    # Light blue (3)
    cards += [
        SingleColorProperty(Color.LIGHT_BLUE, "Oriental Avenue", _RENT_LIGHT_BLUE, 1),
        SingleColorProperty(Color.LIGHT_BLUE, "Vermont Avenue", _RENT_LIGHT_BLUE, 1),
        SingleColorProperty(
            Color.LIGHT_BLUE, "Connecticut Avenue", _RENT_LIGHT_BLUE, 1
        ),
    ]
    # Pink / purple (3)
    cards += [
        SingleColorProperty(Color.PINK, "St. Charles Place", _RENT_PINK, 2),
        SingleColorProperty(Color.PINK, "States Avenue", _RENT_PINK, 2),
        SingleColorProperty(Color.PINK, "Virginia Avenue", _RENT_PINK, 2),
    ]
    # Orange (3)
    cards += [
        SingleColorProperty(Color.ORANGE, "St. James Place", _RENT_ORANGE, 2),
        SingleColorProperty(Color.ORANGE, "Tennessee Avenue", _RENT_ORANGE, 2),
        SingleColorProperty(Color.ORANGE, "New York Avenue", _RENT_ORANGE, 2),
    ]
    # Red (3)
    cards += [
        SingleColorProperty(Color.RED, "Kentucky Avenue", _RENT_RED, 3),
        SingleColorProperty(Color.RED, "Indiana Avenue", _RENT_RED, 3),
        SingleColorProperty(Color.RED, "Illinois Avenue", _RENT_RED, 3),
    ]
    # Yellow (3)
    cards += [
        SingleColorProperty(Color.YELLOW, "Atlantic Avenue", _RENT_YELLOW, 3),
        SingleColorProperty(Color.YELLOW, "Ventnor Avenue", _RENT_YELLOW, 3),
        SingleColorProperty(Color.YELLOW, "Marvin Gardens", _RENT_YELLOW, 3),
    ]
    # Green (3)
    cards += [
        SingleColorProperty(Color.GREEN, "Pacific Avenue", _RENT_GREEN, 4),
        SingleColorProperty(Color.GREEN, "North Carolina Avenue", _RENT_GREEN, 4),
        SingleColorProperty(Color.GREEN, "Pennsylvania Avenue", _RENT_GREEN, 4),
    ]
    # Dark blue (2)
    cards += [
        SingleColorProperty(Color.BLUE, "Park Place", _RENT_DARK_BLUE, 4),
        SingleColorProperty(Color.BLUE, "Boardwalk", _RENT_DARK_BLUE, 4),
    ]
    # Railroads (4)
    cards += [
        SingleColorProperty(Color.RAILROAD, "Reading Railroad", _RENT_RAILROAD, 2),
        SingleColorProperty(Color.RAILROAD, "Pennsylvania Railroad", _RENT_RAILROAD, 2),
        SingleColorProperty(Color.RAILROAD, "B. & O. Railroad", _RENT_RAILROAD, 2),
        SingleColorProperty(Color.RAILROAD, "Short Line", _RENT_RAILROAD, 2),
    ]
    # Utilities (2)
    cards += [
        SingleColorProperty(Color.UTILITY, "Electric Company", _RENT_UTILITY, 2),
        SingleColorProperty(Color.UTILITY, "Water Works", _RENT_UTILITY, 2),
    ]
    return cards


def _property_wildcards() -> list[Card]:
    return [
        # 2x pink / orange
        MultiColorProperty(Color.PINK, _RENT_PINK, Color.ORANGE, _RENT_ORANGE, 2),
        MultiColorProperty(Color.PINK, _RENT_PINK, Color.ORANGE, _RENT_ORANGE, 2),
        # 1x light blue / brown
        MultiColorProperty(
            Color.LIGHT_BLUE, _RENT_LIGHT_BLUE, Color.BROWN, _RENT_BROWN, 1
        ),
        # 1x light blue / railroad
        MultiColorProperty(
            Color.LIGHT_BLUE, _RENT_LIGHT_BLUE, Color.RAILROAD, _RENT_RAILROAD, 4
        ),
        # 1x dark blue / green
        MultiColorProperty(Color.BLUE, _RENT_DARK_BLUE, Color.GREEN, _RENT_GREEN, 4),
        # 1x railroad / green
        MultiColorProperty(Color.RAILROAD, _RENT_RAILROAD, Color.GREEN, _RENT_GREEN, 4),
        # 2x red / yellow
        MultiColorProperty(Color.RED, _RENT_RED, Color.YELLOW, _RENT_YELLOW, 3),
        MultiColorProperty(Color.RED, _RENT_RED, Color.YELLOW, _RENT_YELLOW, 3),
        # 1x railroad / utility
        MultiColorProperty(
            Color.RAILROAD, _RENT_RAILROAD, Color.UTILITY, _RENT_UTILITY, 2
        ),
        # 2x ten-color wild (no monetary value)
        WildColorProperty(),
        WildColorProperty(),
    ]


def _rent_cards() -> list[Card]:
    cards: list[Card] = []
    _extend(cards, 2, lambda: RentCard(Color.PINK, Color.ORANGE))
    _extend(cards, 2, lambda: RentCard(Color.RAILROAD, Color.UTILITY))
    _extend(cards, 2, lambda: RentCard(Color.GREEN, Color.BLUE))
    _extend(cards, 2, lambda: RentCard(Color.BROWN, Color.LIGHT_BLUE))
    _extend(cards, 2, lambda: RentCard(Color.RED, Color.YELLOW))
    _extend(cards, 3, WildRentCard)
    return cards


def _money_cards() -> list[Card]:
    cards: list[Card] = []
    _extend(cards, 1, lambda: MoneyCard(10))
    _extend(cards, 2, lambda: MoneyCard(5))
    _extend(cards, 3, lambda: MoneyCard(4))
    _extend(cards, 3, lambda: MoneyCard(3))
    _extend(cards, 5, lambda: MoneyCard(2))
    _extend(cards, 6, lambda: MoneyCard(1))
    return cards


def _action_cards() -> list[Card]:
    cards: list[Card] = []
    _extend(cards, 2, DealBreaker)
    _extend(cards, 3, JustSayNo)
    _extend(cards, 3, SlyDeal)
    _extend(cards, 3, ForcedDeal)
    _extend(cards, 3, DebtCollector)
    _extend(cards, 3, ItsMyBirthday)
    _extend(cards, 10, PassGo)
    _extend(cards, 3, House)
    _extend(cards, 2, Hotel)
    _extend(cards, 2, DoubleRent)
    return cards


def build_full_deck() -> list[Card]:
    """Return all 106 playable cards: 28 properties + 11 wildcards + 34 actions + 13 rents + 20 money."""
    out: list[Card] = []
    out += _single_properties()
    out += _property_wildcards()
    out += _action_cards()
    out += _rent_cards()
    out += _money_cards()
    return out
