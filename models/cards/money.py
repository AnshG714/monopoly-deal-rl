from .base import Card, CardType


class MoneyCard(Card):
    def __init__(self, value: int):
        super().__init__(CardType.MONEY, value)
