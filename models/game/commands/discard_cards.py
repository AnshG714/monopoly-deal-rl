from __future__ import annotations

from dataclasses import dataclass

from .base import GameView, require_main_phase_hand_play


@dataclass(frozen=True)
class DiscardCards:
    hand_indices: list[int]

    def validate(self, game: GameView) -> None:
        require_main_phase_hand_play(game, "discard_cards")
        for hand_index in self.hand_indices:
            if hand_index < 0 or hand_index >= len(game.current_player().hand):
                raise IndexError("hand_index out of range")

        if len(self.hand_indices) > len(game.current_player().hand):
            raise ValueError("Cannot discard more cards than are in hand")

    def apply(self, game: GameView) -> None:
        self.validate(game)
        new_hand = []
        s = set(self.hand_indices)
        for index, card in enumerate(game.current_player().hand):
            if index in s:
                game.deck.append(card)
            else:
                new_hand.append(card)
        game.shuffle_deck()
        game.current_player().hand = new_hand
