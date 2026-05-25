from __future__ import annotations

from dataclasses import dataclass

from ...cards.property import Color, MultiColorProperty, PropertyCard, WildColorProperty
from .base import GameCommand, GameView, require_main_phase_hand_play
from .play_property import _pile_for_color


def _is_property_wild(card: PropertyCard) -> bool:
    return isinstance(card, (MultiColorProperty, WildColorProperty))


@dataclass(frozen=True)
class MoveWildProperty(GameCommand):
    """Move a property wild from one board pile to another color pile."""

    from_set_idx: int
    card_idx: int
    into_color: Color

    def validate(self, game: GameView) -> None:
        require_main_phase_hand_play(game, "move_wild_property")
        player = game.current_player()
        pile = player.pile_at(self.from_set_idx)
        if self.card_idx < 0 or self.card_idx >= len(pile.cards):
            raise IndexError("card_idx out of range")
        card = pile.cards[self.card_idx]
        if not _is_property_wild(card):
            raise TypeError("Only property wild cards can be moved between sets")
        if self.into_color == pile.color:
            raise ValueError("Destination color must differ from the source pile")
        if not card.can_count_as(self.into_color):
            raise ValueError(
                f"This wild cannot be moved into a {self.into_color.value} set"
            )
        dest_pile = _pile_for_color(game, self.into_color)
        if dest_pile is not None and dest_pile.is_complete():
            raise ValueError("Cannot move a wild onto a complete property set")

    def apply(self, game: GameView) -> None:
        self.validate(game)
        player = game.current_player()
        pile = player.pile_at(self.from_set_idx)
        breaks_complete_set = pile.is_complete()
        card = pile.pop_card_at(self.card_idx)
        player._drop_empty_pile_at(self.from_set_idx)
        if breaks_complete_set:
            hotel = pile.pop_hotel()
            house = pile.pop_house()
            if hotel is not None:
                player.money_pile.append(hotel)
            if house is not None:
                player.money_pile.append(house)
        player.add_property_to_board(card, self.into_color)
        game.plays_this_turn += 1
