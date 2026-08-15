"""Feature vector layout, dimensions, and shared normalization helpers."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from models.cards.action import ActionCardType
from models.cards.property import CARDS_IN_SET_FOR_COLOR, Color, PropertySet
from models.cards.registry import build_full_deck
from models.game.commands.base import MAX_PLAYS_PER_TURN
from models.player import Player

BANK_DENOMINATIONS: tuple[int, ...] = (1, 2, 3, 4, 5, 10)
FEATURES_PER_COLOR = 7
NUM_COLORS = len(Color)
PROPERTIES_PLAYER_DIM = NUM_COLORS * FEATURES_PER_COLOR
BANK_PLAYER_DIM = len(BANK_DENOMINATIONS)

GLOBAL_DIM = 2
BANK_DIM = BANK_PLAYER_DIM * 2
PROPERTIES_DIM = PROPERTIES_PLAYER_DIM * 2
PENDING_DIM = 34
HAND_DIM = 37

STATE_DIM = GLOBAL_DIM + BANK_DIM + PROPERTIES_DIM + PENDING_DIM + HAND_DIM

MAX_HAND_SIZE = 7
RENT_SCALE = 15.0
DEBT_SCALE = 20.0

ACTION_TYPES: tuple[ActionCardType, ...] = tuple(ActionCardType)
PENDING_KINDS: tuple[str, ...] = (
    "PaymentDue",
    "SlyDealPending",
    "ForcedDealPending",
    "DealBreakerPending",
)

COLORS: tuple[Color, ...] = tuple(Color)


def _bank_max_counts() -> dict[int, int]:
    counts: dict[int, int] = dict.fromkeys(BANK_DENOMINATIONS, 0)
    for card in build_full_deck():
        if card.value in counts:
            counts[card.value] += 1
    return counts


BANK_MAX_COUNTS: dict[int, int] = _bank_max_counts()


@dataclass(frozen=True)
class Slice:
    start: int
    end: int

    @property
    def length(self) -> int:
        return self.end - self.start


@dataclass(frozen=True)
class FeatureLayout:
    global_: Slice
    viewer_bank: Slice
    opponent_bank: Slice
    viewer_properties: Slice
    opponent_properties: Slice
    pending: Slice
    hand: Slice


FEATURE_LAYOUT = FeatureLayout(
    global_=Slice(0, GLOBAL_DIM),
    viewer_bank=Slice(GLOBAL_DIM, GLOBAL_DIM + BANK_PLAYER_DIM),
    opponent_bank=Slice(
        GLOBAL_DIM + BANK_PLAYER_DIM,
        GLOBAL_DIM + BANK_PLAYER_DIM * 2,
    ),
    viewer_properties=Slice(
        GLOBAL_DIM + BANK_DIM, GLOBAL_DIM + BANK_DIM + PROPERTIES_PLAYER_DIM
    ),
    opponent_properties=Slice(
        GLOBAL_DIM + BANK_DIM + PROPERTIES_PLAYER_DIM,
        GLOBAL_DIM + BANK_DIM + PROPERTIES_DIM,
    ),
    pending=Slice(
        GLOBAL_DIM + BANK_DIM + PROPERTIES_DIM,
        GLOBAL_DIM + BANK_DIM + PROPERTIES_DIM + PENDING_DIM,
    ),
    hand=Slice(
        GLOBAL_DIM + BANK_DIM + PROPERTIES_DIM + PENDING_DIM,
        STATE_DIM,
    ),
)


def normalize_count(value: int, *, maximum: float) -> float:
    if maximum <= 0:
        return 0.0
    return value / maximum


def normalize_turns_left(plays_this_turn: int) -> float:
    return normalize_count(
        MAX_PLAYS_PER_TURN - plays_this_turn,
        maximum=float(MAX_PLAYS_PER_TURN),
    )


def normalize_hand_count(value: int) -> float:
    return normalize_count(value, maximum=float(MAX_HAND_SIZE))


def normalize_bank_count(value: int, denomination: int) -> float:
    return normalize_count(value, maximum=float(BANK_MAX_COUNTS[denomination]))


def normalize_set_count(value: int, color: Color) -> float:
    return normalize_count(value, maximum=float(CARDS_IN_SET_FOR_COLOR[color]))


def normalize_rent(value: int) -> float:
    return value / RENT_SCALE


def normalize_debt(value: int) -> float:
    return value / DEBT_SCALE


def color_one_hot(color: Color | None) -> list[float]:
    out = [0.0] * NUM_COLORS
    if color is not None:
        out[COLORS.index(color)] = 1.0
    return out


def piles_by_color(piles: Sequence[PropertySet]) -> dict[Color, PropertySet]:
    return {pile.color: pile for pile in piles}


def player_with_property_sets(piles: Sequence[PropertySet]) -> Player:
    """Minimal player surface for ``rent_m_due_for_color``."""
    player = Player("_encode")
    player.property_sets = list(piles)
    return player
