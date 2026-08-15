"""Action-vector layout and dimension constants."""

from __future__ import annotations

from models.cards.property import Color

# Stable orders — rematerialize policy data if these change.
ACTION_KINDS: tuple[str, ...] = (
    "DiscardCards",
    "EndTurn",
    "MoveWildProperty",
    "PassJustSayNo",
    "PayDebt",
    "PlayDealBreaker",
    "PlayDebtCollector",
    "PlayDoubleRent",
    "PlayForcedDeal",
    "PlayHotel",
    "PlayHouse",
    "PlayItsMyBirthday",
    "PlayJustSayNo",
    "PlayMoneyFromHand",
    "PlayPassGo",
    "PlayPropertyFromHand",
    "PlayRent",
    "PlaySlyDeal",
)

ACTION_BUCKETS: tuple[str, ...] = (
    "complete",
    "charge",
    "draw",
    "property",
    "disrupt",
    "build",
    "bank",
    "other",
)

# Same Color enum order as state_encoder.layout.COLORS (string values for CSV params).
COLORS: tuple[str, ...] = tuple(c.value for c in Color)

KIND_TO_INDEX = {kind: i for i, kind in enumerate(ACTION_KINDS)}
BUCKET_TO_INDEX = {bucket: i for i, bucket in enumerate(ACTION_BUCKETS)}
COLOR_TO_INDEX = {color: i for i, color in enumerate(COLORS)}

# Kind → bucket without needing a live Game (no "completes set" bonus).
KIND_BUCKET: dict[str, str] = {
    "PlayDealBreaker": "complete",
    "PlayRent": "charge",
    "PlayDoubleRent": "charge",
    "PlayDebtCollector": "charge",
    "PlayItsMyBirthday": "charge",
    "PlayPassGo": "draw",
    "PlayPropertyFromHand": "property",
    "MoveWildProperty": "property",
    "PlaySlyDeal": "disrupt",
    "PlayForcedDeal": "disrupt",
    "PlayHouse": "build",
    "PlayHotel": "build",
    "PlayMoneyFromHand": "bank",
}

KIND_DIM = len(ACTION_KINDS)
BUCKET_DIM = len(ACTION_BUCKETS)
COLOR_DIM = len(COLORS)
HAND_INDEX_DIM = 1
ACTION_DIM = KIND_DIM + BUCKET_DIM + HAND_INDEX_DIM + COLOR_DIM

MAX_HAND_INDEX = 10.0
