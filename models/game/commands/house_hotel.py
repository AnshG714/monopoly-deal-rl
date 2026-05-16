from __future__ import annotations

from dataclasses import dataclass

from ...cards.action import ActionCardType
from ...cards.property import Color
from .base import (
    GameView,
    pop_from_hand,
    record_hand_plays,
    require_hand_action,
    require_main_phase_hand_play,
)


def _validate_build_target(color: Color) -> None:
    if color in (Color.RAILROAD, Color.UTILITY):
        raise ValueError("House/Hotel cannot be added to railroad or utility sets")


@dataclass(frozen=True)
class PlayHouse:
    hand_index: int
    target_set_idx: int

    def validate(self, game: GameView) -> None:
        require_main_phase_hand_play(game, "play_house")
        require_hand_action(
            game, game.current_player_idx, self.hand_index, ActionCardType.HOUSE
        )
        pile = game.current_player().pile_at(self.target_set_idx)
        _validate_build_target(pile.color)
        if not pile.is_complete():
            raise ValueError("House requires a complete property set")
        if pile.has_house():
            raise ValueError("Target set already has a house")

    def apply(self, game: GameView) -> None:
        self.validate(game)
        house = pop_from_hand(
            game,
            game.current_player_idx,
            self.hand_index,
            action_type=ActionCardType.HOUSE,
        )
        record_hand_plays(game, 1)
        pile = game.current_player().pile_at(self.target_set_idx)
        pile.attach_house(house)


@dataclass(frozen=True)
class PlayHotel:
    hand_index: int
    target_set_idx: int

    def validate(self, game: GameView) -> None:
        require_main_phase_hand_play(game, "play_hotel")
        require_hand_action(
            game, game.current_player_idx, self.hand_index, ActionCardType.HOTEL
        )
        pile = game.current_player().pile_at(self.target_set_idx)
        _validate_build_target(pile.color)
        if not pile.is_complete():
            raise ValueError("Hotel requires a complete property set")
        if not pile.has_house():
            raise ValueError("Hotel requires a house on the target set first")
        if pile.has_hotel():
            raise ValueError("Target set already has a hotel")

    def apply(self, game: GameView) -> None:
        self.validate(game)
        hotel = pop_from_hand(
            game,
            game.current_player_idx,
            self.hand_index,
            action_type=ActionCardType.HOTEL,
        )
        record_hand_plays(game, 1)
        pile = game.current_player().pile_at(self.target_set_idx)
        pile.attach_hotel(hotel)
