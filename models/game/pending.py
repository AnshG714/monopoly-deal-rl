"""Interrupt prompts — single source of truth for 'who must act and why'."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, TypeAlias

from ..cards.property import Color


@dataclass
class JustSayNoNegotiation:
    """Alternating Just Say No responses; defender is the player harmed by the action."""

    defender_idx: int
    actor_idx: int
    responder: Literal["defender", "actor"]
    chain_started: bool

    @staticmethod
    def opening_after_declare(
        defender_idx: int, actor_idx: int
    ) -> JustSayNoNegotiation:
        """Victim may play JSN or allow the action (e.g. Sly Deal declared)."""
        return JustSayNoNegotiation(
            defender_idx=defender_idx,
            actor_idx=actor_idx,
            responder="defender",
            chain_started=False,
        )


@dataclass
class SlyDealStealIntent:
    victim_idx: int
    target_set_idx: int
    target_card_idx: int
    into_color: Color


@dataclass
class ForcedDealSwapIntent:
    target_player_idx: int
    my_set_idx: int
    my_card_idx: int
    their_set_idx: int
    their_card_idx: int
    take_into_color: Color
    give_into_color: Color


@dataclass
class DealBreakerTheftIntent:
    victim_idx: int
    victim_set_idx: int


@dataclass
class PaymentDue:
    """Debtor must pay ``amount_m`` to creditor (Monopoly money units), or Just Say No chain."""

    creditor_idx: int
    debtor_idx: int
    amount_m: int
    jsn: JustSayNoNegotiation | None = None


@dataclass
class SlyDealPending:
    """Actor played Sly Deal; awaiting Just Say No or resolution."""

    actor_idx: int
    steal: SlyDealStealIntent
    jsn: JustSayNoNegotiation


@dataclass
class ForcedDealPending:
    """Actor played Forced Deal; awaiting Just Say No or resolution."""

    actor_idx: int
    swap: ForcedDealSwapIntent
    jsn: JustSayNoNegotiation


@dataclass
class DealBreakerPending:
    """Actor played Deal Breaker; awaiting Just Say No or resolution."""

    actor_idx: int
    theft: DealBreakerTheftIntent
    jsn: JustSayNoNegotiation


Pending: TypeAlias = (
    PaymentDue | SlyDealPending | ForcedDealPending | DealBreakerPending
)


def jsn_responder_player_idx(jsn: JustSayNoNegotiation) -> int:
    """Return the player index of the current player who needs to respond to the Just Say No window."""
    return jsn.defender_idx if jsn.responder == "defender" else jsn.actor_idx
