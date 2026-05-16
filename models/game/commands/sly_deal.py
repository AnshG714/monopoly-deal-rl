from __future__ import annotations

from dataclasses import dataclass

from ...cards.action import ActionCardType
from ...cards.property import Color
from ..pending import JustSayNoNegotiation, SlyDealPending, SlyDealStealIntent
from .base import (
    GameView,
    player_at,
    require_hand_action,
    require_main_phase_hand_play,
    spend_to_discard_and_interrupt,
)


def resolve_sly_deal(game: GameView, pending: SlyDealPending) -> None:
    steal = pending.steal
    victim = player_at(game, steal.victim_idx)
    actor = player_at(game, pending.actor_idx)
    victim_pile = victim.pile_at(steal.target_set_idx)
    if victim_pile.is_complete():
        raise ValueError("Cannot steal from a complete property set")
    stolen = victim_pile.cards[steal.target_card_idx]
    if not stolen.can_count_as(steal.into_color):
        raise ValueError("Invalid steal resolution")

    victim.give_property_card_to(
        actor,
        steal.target_set_idx,
        steal.target_card_idx,
        steal.into_color,
    )


@dataclass(frozen=True)
class PlaySlyDeal:
    hand_index: int
    target_player_idx: int
    target_set_idx: int
    target_card_idx: int
    into_color: Color

    def _build_intent(self, game: GameView) -> SlyDealStealIntent:
        if self.target_player_idx == game.current_player_idx:
            raise ValueError("Cannot steal from yourself")
        victim = player_at(game, self.target_player_idx)
        victim_pile = victim.pile_at(self.target_set_idx)
        if victim_pile.is_complete():
            raise ValueError("Cannot steal from a complete property set")
        if self.target_card_idx < 0 or self.target_card_idx >= len(victim_pile.cards):
            raise IndexError("target_card_idx out of range")

        stolen = victim_pile.cards[self.target_card_idx]
        if not stolen.can_count_as(self.into_color):
            raise ValueError(
                f"This card cannot be added to a {self.into_color.value} property set"
            )
        return SlyDealStealIntent(
            victim_idx=self.target_player_idx,
            target_set_idx=self.target_set_idx,
            target_card_idx=self.target_card_idx,
            into_color=self.into_color,
        )

    def validate(self, game: GameView) -> None:
        require_main_phase_hand_play(game, "play_sly_deal")
        require_hand_action(
            game, game.current_player_idx, self.hand_index, ActionCardType.SLY_DEAL
        )
        self._build_intent(game)

    def apply(self, game: GameView) -> None:
        self.validate(game)
        actor_idx = game.current_player_idx
        spend_to_discard_and_interrupt(
            game,
            action_name="play_sly_deal",
            hand_index=self.hand_index,
            action_type=ActionCardType.SLY_DEAL,
            pending=SlyDealPending(
                actor_idx=actor_idx,
                steal=self._build_intent(game),
                jsn=JustSayNoNegotiation.opening_after_declare(
                    defender_idx=self.target_player_idx,
                    actor_idx=actor_idx,
                ),
            ),
            acting_player_idx=self.target_player_idx,
        )
