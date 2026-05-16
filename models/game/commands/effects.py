from __future__ import annotations

from ..pending import DealBreakerPending, ForcedDealPending, SlyDealPending
from .base import GameView
from .deal_breaker import resolve_deal_breaker
from .forced_deal import resolve_forced_deal
from .sly_deal import resolve_sly_deal


def resolve_deal_interrupt(
    game: GameView,
    pending: SlyDealPending | ForcedDealPending | DealBreakerPending,
) -> None:
    if isinstance(pending, SlyDealPending):
        resolve_sly_deal(game, pending)
    elif isinstance(pending, ForcedDealPending):
        resolve_forced_deal(game, pending)
    else:
        resolve_deal_breaker(game, pending)
