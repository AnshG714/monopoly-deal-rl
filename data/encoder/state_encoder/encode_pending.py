"""Encode interrupt / pending-state features."""

from __future__ import annotations

from collections.abc import Sequence

from models.cards.property import (
    MultiColorProperty,
    PropertyCard,
    PropertySet,
    WildColorProperty,
)
from models.game.pending import (
    DealBreakerPending,
    ForcedDealPending,
    PaymentDue,
    Pending,
    SlyDealPending,
    jsn_responder_player_idx,
)

from .layout import (
    NUM_COLORS,
    PENDING_DIM,
    PENDING_KINDS,
    color_one_hot,
    normalize_debt,
)


def encode_pending(
    pending: Pending | None,
    viewer_idx: int,
    viewer_piles: Sequence[PropertySet],
    opponent_piles: Sequence[PropertySet],
) -> list[float]:
    if pending is None:
        return [0.0] * PENDING_DIM

    kind = [0.0] * len(PENDING_KINDS)
    kind[PENDING_KINDS.index(type(pending).__name__)] = 1.0

    debt = 0.0
    take_color: list[float] = [0.0] * NUM_COLORS
    give_color: list[float] = [0.0] * NUM_COLORS
    take_set_whole = 0.0
    take_multi = 0.0
    take_wild = 0.0
    give_multi = 0.0
    give_wild = 0.0
    am_i_debtor = 0.0
    jsn_active = 0.0
    am_i_jsn_responder = 0.0
    jsn_chain_started = 0.0

    if isinstance(pending, PaymentDue):
        debt = normalize_debt(pending.amount_m)
        if pending.jsn is not None:
            jsn_active = 1.0
            am_i_jsn_responder = (
                1.0 if jsn_responder_player_idx(pending.jsn) == viewer_idx else 0.0
            )
            jsn_chain_started = 1.0 if pending.jsn.chain_started else 0.0
        am_i_debtor = 1.0 if viewer_idx == pending.debtor_idx else 0.0

    elif isinstance(pending, SlyDealPending):
        take_color = color_one_hot(pending.steal.into_color)
        victim_piles = _piles_for_player(
            pending.steal.victim_idx, viewer_idx, viewer_piles, opponent_piles
        )
        taken = _card_at(victim_piles, pending.steal.target_set_idx, pending.steal.target_card_idx)
        take_multi, take_wild = _wild_multi_flags(taken)
        jsn_active = 1.0
        am_i_jsn_responder = (
            1.0 if jsn_responder_player_idx(pending.jsn) == viewer_idx else 0.0
        )
        jsn_chain_started = 1.0 if pending.jsn.chain_started else 0.0

    elif isinstance(pending, ForcedDealPending):
        swap = pending.swap
        take_color = color_one_hot(swap.take_into_color)
        give_color = color_one_hot(swap.give_into_color)
        actor_piles = _piles_for_player(
            pending.actor_idx, viewer_idx, viewer_piles, opponent_piles
        )
        target_piles = _piles_for_player(
            swap.target_player_idx, viewer_idx, viewer_piles, opponent_piles
        )
        taken = _card_at(target_piles, swap.their_set_idx, swap.their_card_idx)
        given = _card_at(actor_piles, swap.my_set_idx, swap.my_card_idx)
        take_multi, take_wild = _wild_multi_flags(taken)
        give_multi, give_wild = _wild_multi_flags(given)
        jsn_active = 1.0
        am_i_jsn_responder = (
            1.0 if jsn_responder_player_idx(pending.jsn) == viewer_idx else 0.0
        )
        jsn_chain_started = 1.0 if pending.jsn.chain_started else 0.0

    elif isinstance(pending, DealBreakerPending):
        take_set_whole = 1.0
        victim_piles = _piles_for_player(
            pending.theft.victim_idx, viewer_idx, viewer_piles, opponent_piles
        )
        pile = _pile_at(victim_piles, pending.theft.victim_set_idx)
        if pile is not None:
            take_color = color_one_hot(pile.color)
        jsn_active = 1.0
        am_i_jsn_responder = (
            1.0 if jsn_responder_player_idx(pending.jsn) == viewer_idx else 0.0
        )
        jsn_chain_started = 1.0 if pending.jsn.chain_started else 0.0

    return (
        kind
        + [debt]
        + take_color
        + give_color
        + [
            take_set_whole,
            take_multi,
            take_wild,
            give_multi,
            give_wild,
            am_i_debtor,
            jsn_active,
            am_i_jsn_responder,
            jsn_chain_started,
        ]
    )


def _piles_for_player(
    player_idx: int,
    viewer_idx: int,
    viewer_piles: Sequence[PropertySet],
    opponent_piles: Sequence[PropertySet],
) -> Sequence[PropertySet]:
    if player_idx == viewer_idx:
        return viewer_piles
    return opponent_piles


def _pile_at(piles: Sequence[PropertySet], set_idx: int) -> PropertySet | None:
    if set_idx < 0 or set_idx >= len(piles):
        return None
    return piles[set_idx]


def _card_at(
    piles: Sequence[PropertySet],
    set_idx: int,
    card_idx: int,
) -> PropertyCard | None:
    pile = _pile_at(piles, set_idx)
    if pile is None or card_idx < 0 or card_idx >= len(pile.cards):
        return None
    return pile.cards[card_idx]


def _wild_multi_flags(card: PropertyCard | None) -> tuple[float, float]:
    if card is None:
        return 0.0, 0.0
    return (
        1.0 if isinstance(card, MultiColorProperty) else 0.0,
        1.0 if isinstance(card, WildColorProperty) else 0.0,
    )
