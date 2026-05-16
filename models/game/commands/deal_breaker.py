from __future__ import annotations

from dataclasses import dataclass

from ...cards.action import ActionCardType
from ...cards.property import PropertyCard
from ..pending import (
    DealBreakerPending,
    DealBreakerTheftIntent,
    JustSayNoNegotiation,
)
from .base import (
    GameView,
    player_at,
    require_hand_action,
    require_main_phase_hand_play,
    spend_to_discard_and_interrupt,
)


def resolve_deal_breaker(game: GameView, pending: DealBreakerPending) -> None:
    theft = pending.theft
    victim = player_at(game, theft.victim_idx)
    actor = player_at(game, pending.actor_idx)
    pile = victim.pile_at(theft.victim_set_idx)
    if not pile.is_complete():
        raise ValueError("Deal Breaker target set is no longer complete")

    stolen_set = victim.take_property_set(theft.victim_set_idx)
    actor.merge_property_set(stolen_set)


@dataclass(frozen=True)
class PlayDealBreaker:
    hand_index: int
    victim_idx: int
    victim_set_idx: int

    def _build_intent(self, game: GameView) -> DealBreakerTheftIntent:
        if self.victim_idx == game.current_player_idx:
            raise ValueError("Cannot Deal Break yourself")
        victim = player_at(game, self.victim_idx)
        pile = victim.pile_at(self.victim_set_idx)
        if not pile.is_complete():
            raise ValueError("Deal Breaker requires a complete property set")
        return DealBreakerTheftIntent(
            victim_idx=self.victim_idx, victim_set_idx=self.victim_set_idx
        )

    def validate(self, game: GameView) -> None:
        require_main_phase_hand_play(game, "play_deal_breaker")
        require_hand_action(
            game, game.current_player_idx, self.hand_index, ActionCardType.DEAL_BREAKER
        )
        self._build_intent(game)

    def apply(self, game: GameView) -> None:
        self.validate(game)
        actor_idx = game.current_player_idx
        spend_to_discard_and_interrupt(
            game,
            action_name="play_deal_breaker",
            hand_index=self.hand_index,
            action_type=ActionCardType.DEAL_BREAKER,
            pending=DealBreakerPending(
                actor_idx=actor_idx,
                theft=self._build_intent(game),
                jsn=JustSayNoNegotiation.opening_after_declare(
                    defender_idx=self.victim_idx,
                    actor_idx=actor_idx,
                ),
            ),
            acting_player_idx=self.victim_idx,
        )
