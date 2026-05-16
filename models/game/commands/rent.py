from __future__ import annotations

from dataclasses import dataclass

from ...cards.base import CardType
from ...cards.property import Color, MultiColorProperty, SingleColorProperty
from ...cards.rent import RentCard, WildRentCard
from ...player import Player
from ..pending import PaymentDue
from .base import (
    GameView,
    open_payment,
    play_hand_card_to_discard,
    player_at,
    require_main_phase_hand_play,
)


def rent_m_due_for_color(creditor: Player, color: Color) -> int:
    """Monopoly money owed for ``color`` on the victim's board (partial or full set)."""
    for pile in creditor.property_sets:
        if pile.color != color:
            continue
        n = len(pile.cards)
        if n == 0:
            return 0
        rents: list[int] | None = None
        for c in pile.cards:
            if isinstance(c, SingleColorProperty) and c.color == color:
                rents = c.rents
                break
            if isinstance(c, MultiColorProperty):
                if c.color1 == color:
                    rents = c.color1Rents
                    break
                if c.color2 == color:
                    rents = c.color2Rents
                    break
        if rents is None:
            return 0
        idx = min(n, len(rents)) - 1
        return rents[idx]
    return 0


def require_hand_rent_card(
    game: GameView, player_idx: int, hand_index: int
) -> RentCard | WildRentCard:
    player = game.players[player_idx]
    if hand_index < 0 or hand_index >= len(player.hand):
        raise IndexError("hand_index out of range")
    card = player.hand[hand_index]
    if card.type != CardType.RENT:
        raise TypeError("Card must be a rent card")
    if not isinstance(card, (RentCard, WildRentCard)):
        raise TypeError("Card must be a rent card")
    return card


def rent_card_allows_color(card: RentCard | WildRentCard, color: Color) -> bool:
    if isinstance(card, WildRentCard):
        return True
    return color in (card.color1, card.color2)


@dataclass(frozen=True)
class PlayRent:
    """Play a rent card from hand and charge the victim for one of their property colors."""

    hand_index: int
    victim_idx: int
    charged_color: Color

    def validate(self, game: GameView) -> None:
        require_main_phase_hand_play(game, "play_rent")
        if self.victim_idx == game.current_player_idx:
            raise ValueError("Cannot charge rent from yourself")
        card = require_hand_rent_card(game, game.current_player_idx, self.hand_index)
        if not rent_card_allows_color(card, self.charged_color):
            raise ValueError("This rent card cannot charge the chosen color")
        amount_m = rent_m_due_for_color(game.current_player(), self.charged_color)
        if amount_m <= 0:
            raise ValueError("No rent due for that color on that player")

    def apply(self, game: GameView) -> None:
        self.validate(game)
        amount_m = rent_m_due_for_color(game.current_player(), self.charged_color)
        play_hand_card_to_discard(
            game, action_name="play_rent", hand_index=self.hand_index
        )
        open_payment(
            game,
            PaymentDue(
                creditor_idx=game.current_player_idx,
                debtor_idx=self.victim_idx,
                amount_m=amount_m,
            ),
        )
