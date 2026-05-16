from __future__ import annotations

from dataclasses import dataclass

from ...cards.action import ActionCardType
from .base import (
    GameView,
    draw_for_current_player,
    play_action_to_discard,
    require_hand_action,
    require_main_phase_hand_play,
)

CARDS_DRAWN_BY_PASS_GO = 2


@dataclass(frozen=True)
class PlayPassGo:
    hand_index: int

    def validate(self, game: GameView) -> None:
        require_main_phase_hand_play(game, "pass_go")
        require_hand_action(
            game, game.current_player_idx, self.hand_index, ActionCardType.PASS_GO
        )

    def apply(self, game: GameView) -> None:
        self.validate(game)
        play_action_to_discard(
            game,
            action_name="pass_go",
            hand_index=self.hand_index,
            expected=ActionCardType.PASS_GO,
        )
        draw_for_current_player(game, CARDS_DRAWN_BY_PASS_GO)
