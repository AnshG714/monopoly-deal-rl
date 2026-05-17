from __future__ import annotations

from dataclasses import dataclass

from .base import GameView, require_main_phase
from .end_turn import MAX_HAND_SIZE_AT_END_OF_TURN


@dataclass(frozen=True)
class DiscardCards:
    """Discard exactly the excess cards over the end-of-turn hand limit (7)."""

    hand_indices: list[int]

    def validate(self, game: GameView) -> None:
        require_main_phase(game, "discard_cards")
        hand = game.current_player().hand
        need = max(0, len(hand) - MAX_HAND_SIZE_AT_END_OF_TURN)
        if need == 0:
            raise RuntimeError(
                "Cannot discard: hand is already at or below the end-of-turn limit"
            )
        if len(self.hand_indices) != need:
            raise ValueError(
                f"Must discard exactly {need} card(s), got {len(self.hand_indices)}"
            )
        if len(set(self.hand_indices)) != len(self.hand_indices):
            raise ValueError("hand_indices must be distinct")

    def apply(self, game: GameView) -> None:
        self.validate(game)
        new_hand = []
        selected = set(self.hand_indices)
        for index, card in enumerate(game.current_player().hand):
            if index in selected:
                game.deck.append(card)
            else:
                new_hand.append(card)
        game.shuffle_deck()
        game.current_player().hand = new_hand
