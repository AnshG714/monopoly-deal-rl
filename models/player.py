from .cards.action import ActionCard
from .cards.base import Card
from .cards.money import MoneyCard
from .cards.property import Color, PropertyCard, PropertySet
from .cards.rent import RentCard, WildRentCard

BankableCard = MoneyCard | RentCard | WildRentCard | ActionCard


SETS_TO_WIN = 3


class Player:
    def __init__(self, name: str):
        self.name = name
        self.hand: list[Card] = []
        self.money_pile: list[BankableCard] = []
        self.property_sets: list[PropertySet] = []

    def deal_to_hand(self, card: Card):
        self.hand.append(card)

    def pile_at(self, set_idx: int) -> PropertySet:
        """Return a board pile by index."""
        if set_idx < 0 or set_idx >= len(self.property_sets):
            raise IndexError("property_set_idx out of range")
        return self.property_sets[set_idx]

    def add_property_to_board(self, card: PropertyCard, color: Color) -> None:
        """Place a property card onto (or into a new) pile for ``color``."""
        for prop_set in self.property_sets:
            if prop_set.color == color:
                prop_set.add(card)
                return
        pile = PropertySet(color)
        pile.add(card)
        self.property_sets.append(pile)

    def merge_property_set(self, prop_set: PropertySet) -> None:
        """Attach every card from ``prop_set`` onto the board, merging by pile color."""
        target: PropertySet | None = None
        for pile in self.property_sets:
            if pile.color == prop_set.color:
                target = pile
                break
        if target is None:
            target = PropertySet(prop_set.color)
            self.property_sets.append(target)

        for card in list(prop_set.cards):
            target.add(card)
        if prop_set.house is not None:
            if target.has_house():
                self.money_pile.append(prop_set.house)
            else:
                target.attach_house(prop_set.house)
        if prop_set.hotel is not None:
            if target.has_hotel():
                self.money_pile.append(prop_set.hotel)
            else:
                target.attach_hotel(prop_set.hotel)

    def play_property(self, card: PropertyCard, color: Color) -> None:
        """Play a property card from hand to a set of the given color."""
        self.hand.remove(card)
        self.add_property_to_board(card, color)

    def take_property_card_at(self, set_idx: int, card_idx: int) -> PropertyCard:
        """Remove one card from a table pile by index; drops empty piles."""
        pile = self.pile_at(set_idx)
        card = pile.pop_card_at(card_idx)
        self._drop_empty_pile_at(set_idx)
        return card

    def take_property_set(self, set_idx: int) -> PropertySet:
        """Remove a whole property pile by index."""
        return self.property_sets.pop(set_idx)

    def give_property_card_to(
        self,
        recipient: "Player",
        set_idx: int,
        card_idx: int,
        into_color: Color,
    ) -> None:
        """Remove one board card and place it on ``recipient``'s board in ``into_color``."""
        card = self.take_property_card_at(set_idx, card_idx)
        recipient.add_property_to_board(card, into_color)

    def swap_property_cards_with(
        self,
        other: "Player",
        my_set_idx: int,
        my_card_idx: int,
        their_set_idx: int,
        their_card_idx: int,
    ) -> None:
        """Swap one card on each player's board (indices are per-player)."""
        my_pile = self.pile_at(my_set_idx)
        their_pile = other.pile_at(their_set_idx)
        my_card = my_pile.pop_card_at(my_card_idx)
        their_card = their_pile.pop_card_at(their_card_idx)
        my_pile.add(their_card)
        their_pile.add(my_card)
        self._drop_empty_pile_at(my_set_idx)
        other._drop_empty_pile_at(their_set_idx)

    def play_money(self, card: BankableCard):
        self.hand.remove(card)
        self.money_pile.append(card)

    def property_card_count(self) -> int:
        return sum(len(prop_set.cards) for prop_set in self.property_sets)

    def asset_count(self) -> int:
        return len(self.money_pile) + self.property_card_count()

    def complete_set_count(self) -> int:
        return sum(1 for pile in self.property_sets if pile.is_complete())

    def did_win(self) -> bool:
        return self.complete_set_count() >= SETS_TO_WIN

    def move_buildings_to_money_pile(self, set_idx: int) -> None:
        """Move attached house/hotel from a set into this player's money pile."""
        pile = self.pile_at(set_idx)
        hotel = pile.pop_hotel()
        house = pile.pop_house()
        if hotel is not None:
            self.money_pile.append(hotel)
        if house is not None:
            self.money_pile.append(house)

    def _drop_empty_pile_at(self, set_idx: int) -> None:
        if set_idx < len(self.property_sets) and not self.property_sets[set_idx].cards:
            self.property_sets.pop(set_idx)
