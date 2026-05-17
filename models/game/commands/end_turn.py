from __future__ import annotations

from dataclasses import dataclass

from .base import (
    GameView,
    draw_for_current_player,
    require_main_phase,
    require_no_pending,
)

CARDS_DRAWN_AT_TURN_START = 2
INITIAL_HAND_SIZE = 5
MAX_HAND_SIZE_AT_END_OF_TURN = 7


def start_player_turn(game: GameView) -> None:
    """Draw at turn start and reset main-phase state for ``current_player_idx``."""
    require_no_pending(game, "Cannot begin turn while a prompt is pending")
    game.plays_this_turn = 0
    game.acting_player_idx = game.current_player_idx
    draw_for_current_player(game, CARDS_DRAWN_AT_TURN_START)


@dataclass(frozen=True)
class EndTurn:
    def validate(self, game: GameView) -> None:
        require_main_phase(game, "end_turn")
        if len(game.current_player().hand) > MAX_HAND_SIZE_AT_END_OF_TURN:
            raise ValueError(
                "Player has too many cards in hand at end of turn. Needs to discard some cards."
            )

    def apply(self, game: GameView) -> None:
        self.validate(game)

        if len(game.current_player().hand) == 0:
            for _ in range(INITIAL_HAND_SIZE):
                game.current_player().deal_to_hand(game.deck.pop())

        n = len(game.players)
        game.current_player_idx = (game.current_player_idx + 1) % n
        start_player_turn(game)
