from .base import Card, CardType
from .property import Color


class RentCard(Card):
    """Every normal rent card has 2 colors that are rentable."""

    def __init__(self, color1: Color, color2: Color):
        super().__init__(CardType.RENT, 1)
        self.color1 = color1
        self.color2 = color2


class WildRentCard(Card):
    """Wild rent cards can be used to charge any color."""

    def __init__(self):
        super().__init__(CardType.RENT, 3)
