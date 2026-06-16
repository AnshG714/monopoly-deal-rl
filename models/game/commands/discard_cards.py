from __future__ import annotations

from dataclasses import dataclass
from typing import Self

from ..combinatorics import combinations_of_indices
from .base import GameCommand, GameView, require_main_phase
from .end_turn import MAX_HAND_SIZE_AT_END_OF_TURN


@dataclass(frozen=True, eq=False)
class DiscardCards(GameCommand):
    """Discard exactly the excess cards over the end-of-turn hand limit (7)."""

    hand_indices: list[int]

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DiscardCards):
            return False
        return sorted(self.hand_indices) == sorted(other.hand_indices)

    def __hash__(self) -> int:
        return hash((DiscardCards, tuple(sorted(self.hand_indices))))

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

    @classmethod
    def enumerate(cls, game: GameView) -> list[Self]:
        hand_size = len(game.current_player().hand)
        excess = hand_size - MAX_HAND_SIZE_AT_END_OF_TURN
        if excess <= 0:
            return []
        return [
            cls(combination)
            for combination in combinations_of_indices(hand_size, excess)
        ]
