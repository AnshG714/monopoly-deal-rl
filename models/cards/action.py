from enum import Enum

from .base import Card, CardType


class ActionCardType(Enum):
    DEAL_BREAKER = "deal_breaker"
    DEBT_COLLECTOR = "debt_collector"
    DOUBLE_RENT = "double_rent"
    FORCED_DEAL = "forced_deal"
    SLY_DEAL = "sly_deal"
    HOUSE = "house"
    HOTEL = "hotel"
    ITS_MY_BIRTHDAY = "its_my_birthday"
    JUST_SAY_NO = "just_say_no"
    PASS_GO = "pass_go"


class ActionCard(Card):
    def __init__(self, action_type: ActionCardType, value: int):
        super().__init__(CardType.ACTION, value)
        self.action_type = action_type


class DealBreaker(ActionCard):
    def __init__(self):
        super().__init__(ActionCardType.DEAL_BREAKER, 5)


class DebtCollector(ActionCard):
    def __init__(self):
        super().__init__(ActionCardType.DEBT_COLLECTOR, 3)


class DoubleRent(ActionCard):
    def __init__(self):
        super().__init__(ActionCardType.DOUBLE_RENT, 1)


class ForcedDeal(ActionCard):
    def __init__(self):
        super().__init__(ActionCardType.FORCED_DEAL, 3)


class SlyDeal(ActionCard):
    def __init__(self):
        super().__init__(ActionCardType.SLY_DEAL, 3)


class ItsMyBirthday(ActionCard):
    def __init__(self):
        super().__init__(ActionCardType.ITS_MY_BIRTHDAY, 2)


class JustSayNo(ActionCard):
    def __init__(self):
        super().__init__(ActionCardType.JUST_SAY_NO, 4)


class PassGo(ActionCard):
    def __init__(self):
        super().__init__(ActionCardType.PASS_GO, 1)


class House(ActionCard):
    def __init__(self):
        super().__init__(ActionCardType.HOUSE, 3)


class Hotel(ActionCard):
    def __init__(self):
        super().__init__(ActionCardType.HOTEL, 4)
