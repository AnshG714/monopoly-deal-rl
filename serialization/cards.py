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


def serialize_card(card: Card) -> dict:
    payload: dict = {"type": card.type.value, "value": card.value}

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
        return payload

    if isinstance(card, MultiColorProperty):
        payload["property_kind"] = "multi"
        payload["color1"] = card.color1.value
        payload["color2"] = card.color2.value
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
