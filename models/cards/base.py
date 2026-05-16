from enum import Enum


class CardType(Enum):
    PROPERTY = "property"
    ACTION = "action"
    MONEY = "money"
    RENT = "rent"


class Card:
    def __init__(self, type: CardType, value: int):
        self.type = type
        self.value = value
