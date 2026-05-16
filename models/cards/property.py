from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum

from .base import Card, CardType


class Color(Enum):
    RED = "red"
    BLUE = "blue"  # dark blue property set
    GREEN = "green"
    YELLOW = "yellow"
    PINK = "pink"  # purple / pink property set
    ORANGE = "orange"
    BROWN = "brown"
    LIGHT_BLUE = "light_blue"
    RAILROAD = "railroad"
    UTILITY = "utility"


CARDS_IN_SET_FOR_COLOR = {
    Color.RED: 3,
    Color.BLUE: 2,
    Color.GREEN: 3,
    Color.YELLOW: 3,
    Color.PINK: 3,
    Color.ORANGE: 3,
    Color.BROWN: 2,
    Color.LIGHT_BLUE: 3,
    Color.RAILROAD: 4,
    Color.UTILITY: 2,
}


class PropertyCard(Card, ABC):
    """Property cards in hand or bank have no chosen color; on the table they sit in a PropertySet."""

    def __init__(self, value: int):
        super().__init__(CardType.PROPERTY, value)

    @abstractmethod
    def can_count_as(self, color: Color) -> bool:
        """Whether this card may be placed in a set building toward ``color``."""
        raise NotImplementedError


class SingleColorProperty(PropertyCard):
    def __init__(self, color: Color, name: str, rents: list[int], value: int):
        super().__init__(value)
        self.color = color
        self.name = name

        assert (
            len(rents) == CARDS_IN_SET_FOR_COLOR[color]
        ), "Incorrect number of rents for color"
        self.rents: list[int] = rents

    def can_count_as(self, color: Color) -> bool:
        return color == self.color


class MultiColorProperty(PropertyCard):
    def __init__(
        self,
        color1: Color,
        color1Rents: list[int],
        color2: Color,
        color2Rents: list[int],
        value: int,
    ):
        super().__init__(value)
        self.color1 = color1
        self.color1Rents = color1Rents
        self.color2 = color2
        self.color2Rents = color2Rents

    def can_count_as(self, color: Color) -> bool:
        return color in (self.color1, self.color2)


class WildColorProperty(PropertyCard):
    """Full-color wild while unassigned; any set color is valid until you specialize this type."""

    def __init__(self):
        super().__init__(0)

    def can_count_as(self, color: Color) -> bool:
        return True


class PropertySet:
    """One table pile toward a single color; wilds and dual-color cards are committed by membership."""

    def __init__(self, color: Color):
        self.color = color
        self.cards: list[PropertyCard] = []

    def add(self, card: PropertyCard) -> None:
        if not card.can_count_as(self.color):
            raise ValueError(
                f"{type(card).__name__} cannot count as {self.color.value}"
            )
        self.cards.append(card)

    def remove(self, card: PropertyCard) -> None:
        self.cards.remove(card)

    def pop_card_at(self, idx: int) -> PropertyCard:
        if idx < 0 or idx >= len(self.cards):
            raise IndexError("card index out of range")
        return self.cards.pop(idx)

    def is_complete(self) -> bool:
        return len(self.cards) == CARDS_IN_SET_FOR_COLOR[self.color]
