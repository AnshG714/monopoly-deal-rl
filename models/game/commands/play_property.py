from __future__ import annotations

from dataclasses import dataclass

from ...cards.property import Color, PropertyCard, PropertySet
from .base import GameCommand, GameView, require_main_phase_hand_play


def _pile_for_color(game: GameView, color: Color) -> PropertySet | None:
    player = game.current_player()
    for prop_set in player.property_sets:
        if prop_set.color == color:
            return prop_set
    return None


@dataclass(frozen=True)
class PlayPropertyFromHand(GameCommand):
    """Play a property (or property-wild) from hand onto the board in one pile color.

    ``into_color`` is the table pile to build toward. It must be legal for the card
    (``PropertyCard.can_count_as``), including two-color wilds and full-color wilds.
    """

    hand_index: int
    into_color: Color

    def validate(self, game: GameView) -> None:
        require_main_phase_hand_play(game, "play_property_from_hand")
        player = game.current_player()
        if self.hand_index < 0 or self.hand_index >= len(player.hand):
            raise IndexError("hand_index out of range")
        card = player.hand[self.hand_index]
        if not isinstance(card, PropertyCard):
            raise TypeError("Only property cards can be played to the board this way")
        if not card.can_count_as(self.into_color):
            raise ValueError(
                f"This property cannot be played into a {self.into_color.value} set"
            )
        pile = _pile_for_color(game, self.into_color)
        if pile is not None and pile.is_complete():
            raise ValueError("Cannot add to a complete property set")

    def apply(self, game: GameView) -> None:
        self.validate(game)
        player = game.current_player()
        card = player.hand.pop(self.hand_index)
        if not isinstance(card, PropertyCard):
            raise TypeError("Expected a property card")
        player.add_property_to_board(card, self.into_color)
        game.plays_this_turn += 1
