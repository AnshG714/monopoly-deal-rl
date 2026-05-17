from __future__ import annotations

import random

from ..cards.base import Card
from ..cards.property import Color
from ..cards.registry import build_full_deck
from ..player import Player
from .commands import (
    EndTurn,
    GameCommand,
    GameView,
    INITIAL_HAND_SIZE,
    MAX_PLAYS_PER_TURN,
    DiscardCards,
    PassJustSayNo,
    PayDebt,
    PlayDealBreaker,
    PlayDebtCollector,
    PlayForcedDeal,
    PlayHotel,
    PlayHouse,
    PlayItsMyBirthday,
    PlayJustSayNo,
    PlayMoneyFromHand,
    PlayPassGo,
    PlayPropertyFromHand,
    PlayDoubleRent,
    PlayRent,
    PlaySlyDeal,
    start_player_turn,
)
from .legal_moves import legal_moves
from .pending import Pending


class Game(GameView):
    """
    Turn flow (main phase):
      - ``begin_turn()`` draws two cards for the current player (not an agent action).
      - The current player may play up to ``MAX_PLAYS_PER_TURN`` cards from hand, then ``EndTurn``.

    Interrupts:
      - ``pending`` holds who must respond (e.g. pay rent, Just Say No window).
      - ``acting_player_idx`` follows the actor for that prompt (including out-of-turn JSN).
    """

    def __init__(self, rng: random.Random | None = None) -> None:
        self._rng = rng or random.Random()
        self.deck: list[Card] = build_full_deck()
        self.players: list[Player] = [Player("Player 1"), Player("Player 2")]
        self.discard_pile: list[Card] = []
        self.current_player_idx: int = 0
        self.acting_player_idx: int = 0
        self.pending: Pending | None = None
        self.plays_this_turn: int = 0

    def shuffle_deck(self) -> None:
        self._rng.shuffle(self.deck)

    def deal_cards(self) -> None:
        num_players = len(self.players)
        need = num_players * INITIAL_HAND_SIZE
        if len(self.deck) < need:
            raise ValueError("Not enough cards to deal")
        for player in self.players:
            for _ in range(INITIAL_HAND_SIZE):
                player.deal_to_hand(self.deck.pop())

    def start_match(self) -> None:
        """Shuffle, deal opening hands, then start the first player's turn (including draw-2)."""
        self.shuffle_deck()
        self.deal_cards()
        self.begin_turn()

    def begin_turn(self) -> None:
        start_player_turn(self)

    def end_turn(self) -> None:
        """End the current player's turn and start the next player's turn."""
        self.apply(EndTurn())

    def apply(self, command: GameCommand) -> None:
        """Apply a player-facing command after its own legality check."""
        command.apply(self)

    def play_money_from_hand(self, hand_index: int) -> None:
        """Play a money/action/rent card from hand into your bank."""
        self.apply(PlayMoneyFromHand(hand_index))

    def play_pass_go(self, hand_index: int) -> None:
        """Play Pass Go from hand."""
        self.apply(PlayPassGo(hand_index))

    def play_property_from_hand(self, hand_index: int, into_color: Color) -> None:
        """Play a property or property-wild from hand into a pile for ``into_color``."""
        self.apply(PlayPropertyFromHand(hand_index, into_color))

    def play_house(self, hand_index: int, target_set_idx: int) -> None:
        """Play House from hand onto one of your complete non-utility/non-railroad sets."""
        self.apply(PlayHouse(hand_index, target_set_idx))

    def play_hotel(self, hand_index: int, target_set_idx: int) -> None:
        """Play Hotel from hand onto one of your complete sets with an existing house."""
        self.apply(PlayHotel(hand_index, target_set_idx))

    def play_debt_collector(self, hand_index: int, target_player_idx: int) -> None:
        """Force another player to pay you $5M (they may Just Say No)."""
        self.apply(PlayDebtCollector(hand_index, target_player_idx))

    def play_its_my_birthday(self, hand_index: int) -> None:
        """All other players owe you $2M each; opens the first debt (multi-player chaining TBD)."""
        self.apply(PlayItsMyBirthday(hand_index))

    def play_rent(self, hand_index: int, victim_idx: int, charged_color: Color) -> None:
        """Play a rent card from hand and charge the victim for ``charged_color`` on their board."""
        self.apply(PlayRent(hand_index, victim_idx, charged_color))

    def play_double_rent(
        self,
        double_rent_hand_index: int,
        rent_hand_index: int,
        victim_idx: int,
        charged_color: Color,
    ) -> None:
        """Play Double the Rent and a rent card (two plays); charge double the normal rent."""
        self.apply(
            PlayDoubleRent(
                double_rent_hand_index, rent_hand_index, victim_idx, charged_color
            )
        )

    def pay_debt(
        self,
        money_pile_indices: list[int],
        property_card_indices: list[tuple[int, int]] | None = None,
    ) -> None:
        """Debtor pays by moving chosen bank/property cards to the creditor.

        If no JSN chain is open, paying alone resolves the debt. If a chain is active
        and it is the debtor's turn to respond, paying counts as conceding the JSN duel
        (same outcome as ``pass_just_say_no`` then pay).
        """
        self.apply(PayDebt(money_pile_indices, property_card_indices or []))

    def play_just_say_no(self, hand_index: int) -> None:
        """Play Just Say No from hand (out-of-turn during an interrupt). Chains alternate actor/defender."""
        self.apply(PlayJustSayNo(hand_index))

    def pass_just_say_no(self) -> None:
        """Decline to play another Just Say No; resolves the interrupt per chain rules."""
        self.apply(PassJustSayNo())

    def play_sly_deal(
        self,
        hand_index: int,
        target_player_idx: int,
        target_set_idx: int,
        target_card_idx: int,
        into_color: Color,
    ) -> None:
        """Play Sly Deal with a concrete steal target; victim may Just Say No."""
        self.apply(
            PlaySlyDeal(
                hand_index=hand_index,
                target_player_idx=target_player_idx,
                target_set_idx=target_set_idx,
                target_card_idx=target_card_idx,
                into_color=into_color,
            )
        )

    def play_forced_deal(
        self,
        hand_index: int,
        target_player_idx: int,
        my_set_idx: int,
        my_card_idx: int,
        their_set_idx: int,
        their_card_idx: int,
    ) -> None:
        """Play Forced Deal with a concrete swap target; target may Just Say No."""
        self.apply(
            PlayForcedDeal(
                hand_index=hand_index,
                target_player_idx=target_player_idx,
                my_set_idx=my_set_idx,
                my_card_idx=my_card_idx,
                their_set_idx=their_set_idx,
                their_card_idx=their_card_idx,
            )
        )

    def play_deal_breaker(
        self, hand_index: int, victim_idx: int, victim_set_idx: int
    ) -> None:
        """Play Deal Breaker against a concrete complete set; victim may Just Say No."""
        self.apply(PlayDealBreaker(hand_index, victim_idx, victim_set_idx))

    def discard_cards(self, hand_indices: list[int]) -> None:
        """Discard excess cards (down to 7) at end of turn; does not use a play."""
        self.apply(DiscardCards(hand_indices))

    def current_player(self) -> Player:
        return self.players[self.current_player_idx]

    def legal_moves(self) -> list[GameCommand]:
        """All legal commands for ``acting_player_idx`` (whoever must act now)."""
        return legal_moves(self)
