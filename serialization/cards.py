"""Serialize engine card objects to JSON-safe dicts."""

from __future__ import annotations

from enum import Enum

from models.cards.action import ActionCard
from models.cards.base import Card
from models.cards.money import MoneyCard
from models.cards.property import (
    MultiColorProperty,
    PropertyCard,
    PropertySet,
    SingleColorProperty,
    WildColorProperty,
)
from models.cards.rent import RentCard, WildRentCard


ACTION_DISPLAY_NAMES = {
    "deal_breaker": "Deal Breaker",
    "debt_collector": "Debt Collector",
    "double_rent": "Double the Rent",
    "forced_deal": "Forced Deal",
    "sly_deal": "Sly Deal",
    "house": "House",
    "hotel": "Hotel",
    "its_my_birthday": "It's My Birthday",
    "just_say_no": "Just Say No",
    "pass_go": "Pass Go",
}


def _color_label(color: str) -> str:
    return color.replace("_", " ").title()


def _display_name(card: Card) -> str:
    if isinstance(card, MoneyCard):
        return f"${card.value}M"
    if isinstance(card, ActionCard):
        return ACTION_DISPLAY_NAMES.get(
            card.action_type.value, card.action_type.value.replace("_", " ").title()
        )
    if isinstance(card, RentCard):
        return f"{_color_label(card.color1.value)} / {_color_label(card.color2.value)} Rent"
    if isinstance(card, WildRentCard):
        return "Wild Rent"
    if isinstance(card, SingleColorProperty):
        return card.name
    if isinstance(card, MultiColorProperty):
        return f"{_color_label(card.color1.value)} / {_color_label(card.color2.value)} Wild"
    if isinstance(card, WildColorProperty):
        return "Property Wild"
    return card.type.value.replace("_", " ").title()


def serialize_card(card: Card) -> dict:
    payload: dict = {
        "type": card.type.value,
        "value": card.value,
        "display_name": _display_name(card),
    }

    if isinstance(card, MoneyCard):
        return payload

    if isinstance(card, ActionCard):
        payload["action_type"] = card.action_type.value
        return payload

    if isinstance(card, RentCard):
        payload["color1"] = card.color1.value
        payload["color2"] = card.color2.value
        return payload

    if isinstance(card, WildRentCard):
        return payload

    if isinstance(card, SingleColorProperty):
        payload["property_kind"] = "single"
        payload["color"] = card.color.value
        payload["name"] = card.name
        payload["rents"] = card.rents
        return payload

    if isinstance(card, MultiColorProperty):
        payload["property_kind"] = "multi"
        payload["color1"] = card.color1.value
        payload["color2"] = card.color2.value
        payload["color1_rents"] = card.color1Rents
        payload["color2_rents"] = card.color2Rents
        return payload

    if isinstance(card, WildColorProperty):
        payload["property_kind"] = "wild"
        return payload

    if isinstance(card, PropertyCard):
        payload["property_kind"] = "unknown"
        return payload

    return payload


def serialize_property_set(pile: PropertySet) -> dict:
    return {
        "color": pile.color.value,
        "cards": [serialize_card(card) for card in pile.cards],
        "complete": pile.is_complete(),
        "has_house": pile.has_house(),
        "has_hotel": pile.has_hotel(),
    }


def serialize_enum(value: Enum) -> str:
    return value.value
