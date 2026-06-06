from __future__ import annotations

from dataclasses import dataclass

from ...cards.action import ActionCardType
from ...cards.property import Color
from ..pending import ForcedDealPending, ForcedDealSwapIntent, JustSayNoNegotiation
from .base import (
    GameCommand,
    GameView,
    player_at,
    require_hand_action,
    require_main_phase_hand_play,
    spend_to_discard_and_interrupt,
)


def resolve_forced_deal(game: GameView, pending: ForcedDealPending) -> None:
    swap = pending.swap
    actor = player_at(game, pending.actor_idx)
    target = player_at(game, swap.target_player_idx)
    my_card = actor.take_property_card_at(swap.my_set_idx, swap.my_card_idx)
    their_card = target.take_property_card_at(swap.their_set_idx, swap.their_card_idx)
    actor.add_property_to_board(their_card, swap.take_into_color)
    target.add_property_to_board(my_card, swap.give_into_color)


@dataclass(frozen=True)
class PlayForcedDeal(GameCommand):
    hand_index: int
    target_player_idx: int
    my_set_idx: int
    my_card_idx: int
    their_set_idx: int
    their_card_idx: int
    take_into_color: Color
    give_into_color: Color

    def _build_intent(self, game: GameView) -> ForcedDealSwapIntent:

        # Make sure you're not swapping with yourself.
        if self.target_player_idx == game.current_player_idx:
            raise ValueError("Cannot swap with yourself")

        actor = game.current_player()
        target = player_at(game, self.target_player_idx)

        my_pile = actor.pile_at(self.my_set_idx)
        their_pile = target.pile_at(self.their_set_idx)

        if self.my_card_idx < 0 or self.my_card_idx >= len(my_pile.cards):
            raise IndexError("my_card_idx out of range")
        if self.their_card_idx < 0 or self.their_card_idx >= len(their_pile.cards):
            raise IndexError("their_card_idx out of range")

        # Can't steal from complete sets.
        if my_pile.is_complete() or their_pile.is_complete():
            raise ValueError("Cannot swap cards from or with a complete property set")

        my_card = my_pile.cards[self.my_card_idx]
        their_card = their_pile.cards[self.their_card_idx]
        if not their_card.can_count_as(self.take_into_color):
            raise ValueError(
                "Their card cannot be placed in your chosen property color"
            )
        if not my_card.can_count_as(self.give_into_color):
            raise ValueError(
                "Your card cannot be placed in their chosen property color"
            )
        return ForcedDealSwapIntent(
            target_player_idx=self.target_player_idx,
            my_set_idx=self.my_set_idx,
            my_card_idx=self.my_card_idx,
            their_set_idx=self.their_set_idx,
            their_card_idx=self.their_card_idx,
            take_into_color=self.take_into_color,
            give_into_color=self.give_into_color,
        )

    def validate(self, game: GameView) -> None:
        require_main_phase_hand_play(game, "play_forced_deal")
        require_hand_action(
            game, game.current_player_idx, self.hand_index, ActionCardType.FORCED_DEAL
        )
        self._build_intent(game)

    def apply(self, game: GameView) -> None:
        self.validate(game)
        actor_idx = game.current_player_idx
        spend_to_discard_and_interrupt(
            game,
            action_name="play_forced_deal",
            hand_index=self.hand_index,
            action_type=ActionCardType.FORCED_DEAL,
            pending=ForcedDealPending(
                actor_idx=actor_idx,
                swap=self._build_intent(game),
                jsn=JustSayNoNegotiation.opening_after_declare(
                    defender_idx=self.target_player_idx,
                    actor_idx=actor_idx,
                ),
            ),
            acting_player_idx=self.target_player_idx,
        )
