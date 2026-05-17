from __future__ import annotations

from dataclasses import dataclass, field

from ...cards.property import PropertyCard
from ...player import Player
from ..pending import jsn_responder_player_idx
from .base import (
    GameCommand,
    GameView,
    clear_pending_back_to_turn,
    require_acting,
    require_main_phase_hand_play,
    require_pending_payment,
)


@dataclass(frozen=True)
class PlayMoneyFromHand(GameCommand):
    hand_index: int

    def validate(self, game: GameView) -> None:
        require_main_phase_hand_play(game, "play_money_from_hand")
        player = game.current_player()
        if self.hand_index < 0 or self.hand_index >= len(player.hand):
            raise IndexError("hand_index out of range")
        if isinstance(player.hand[self.hand_index], PropertyCard):
            raise TypeError("Property cards cannot be discarded as money.")

    def apply(self, game: GameView) -> None:
        self.validate(game)
        player = game.current_player()
        card = player.hand.pop(self.hand_index)
        player.money_pile.append(card)
        game.plays_this_turn += 1


@dataclass(frozen=True)
class PayDebt(GameCommand):
    money_pile_indices: list[int]
    property_card_indices: list[tuple[int, int]] = field(default_factory=list)

    def _selected_money_indices(self) -> list[int]:
        return sorted(set(self.money_pile_indices))

    def _selected_property_indices(self) -> list[tuple[int, int]]:
        return sorted(set(self.property_card_indices), reverse=True)

    def validate(self, game: GameView) -> None:
        due = require_pending_payment(game.pending)
        debtor = game.players[due.debtor_idx]
        require_acting(game, due.debtor_idx, "Only the debtor may submit payment")
        if due.jsn is not None and jsn_responder_player_idx(due.jsn) != due.debtor_idx:
            raise RuntimeError(
                "Cannot pay while the creditor must respond in a Just Say No chain"
            )

        money_idxs = self._selected_money_indices()
        property_idxs = self._selected_property_indices()
        if not money_idxs and not property_idxs and debtor.asset_count() > 0:
            raise ValueError("Select at least one asset to pay")

        total = 0
        for i in money_idxs:
            if i < 0 or i >= len(debtor.money_pile):
                raise IndexError("money_pile index out of range")
            total += debtor.money_pile[i].value

        for set_idx, card_idx in property_idxs:
            prop_set = debtor.pile_at(set_idx)
            if card_idx < 0 or card_idx >= len(prop_set.cards):
                raise IndexError("property card index out of range")
            total += prop_set.cards[card_idx].value

        if total < due.amount_m and not self._selected_all_assets(debtor):
            raise ValueError(
                f"Payment {total}M is less than amount owed {due.amount_m}M"
            )

    def apply(self, game: GameView) -> None:
        self.validate(game)
        due = require_pending_payment(game.pending)
        debtor = game.players[due.debtor_idx]
        creditor = game.players[due.creditor_idx]
        due.jsn = None

        for i in reversed(self._selected_money_indices()):
            card = debtor.money_pile.pop(i)
            creditor.money_pile.append(card)

        for set_idx, card_idx in self._selected_property_indices():
            pile = debtor.pile_at(set_idx)
            color = pile.color
            breaks_complete_set = pile.is_complete()
            card = debtor.take_property_card_at(set_idx, card_idx)
            if breaks_complete_set:
                hotel = pile.pop_hotel()
                house = pile.pop_house()
                if hotel is not None:
                    debtor.money_pile.append(hotel)
                if house is not None:
                    debtor.money_pile.append(house)
            creditor.add_property_to_board(card, color)
        clear_pending_back_to_turn(game)

    def _selected_all_assets(self, player: Player) -> bool:
        return (
            len(self._selected_money_indices()) == len(player.money_pile)
            and len(self._selected_property_indices()) == player.property_card_count()
        )
