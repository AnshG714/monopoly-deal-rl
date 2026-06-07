from __future__ import annotations

import random

from ..cards.base import Card
from ..cards.registry import build_full_deck
from ..player import Player
from .commands import (
    EndTurn,
    GameCommand,
    GameView,
    INITIAL_HAND_SIZE,
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

    def current_player(self) -> Player:
        return self.players[self.current_player_idx]

    def legal_moves(self) -> list[GameCommand]:
        """All legal commands for ``acting_player_idx`` (whoever must act now)."""
        return legal_moves(self)

    def is_over(self) -> bool:
        return self.winner_idx() is not None

    def winner_idx(self) -> int | None:
        for i, player in enumerate(self.players):
            if player.did_win():
                return i
        return None
