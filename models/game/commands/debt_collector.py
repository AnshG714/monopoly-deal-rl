from __future__ import annotations

from dataclasses import dataclass

from ...cards.action import ActionCardType
from ..pending import PaymentDue
from .base import (
    GameView,
    open_payment,
    player_at,
    require_hand_action,
    require_main_phase_hand_play,
    spend_to_discard,
)

DEBT_COLLECTOR_PAYMENT_M = 5


@dataclass(frozen=True)
class PlayDebtCollector:
    hand_index: int
    target_player_idx: int

    def validate(self, game: GameView) -> None:
        require_main_phase_hand_play(game, "play_debt_collector")
        require_hand_action(
            game,
            game.current_player_idx,
            self.hand_index,
            ActionCardType.DEBT_COLLECTOR,
        )
        if self.target_player_idx == game.current_player_idx:
            raise ValueError("Cannot collect from yourself")
        player_at(game, self.target_player_idx)

    def apply(self, game: GameView) -> None:
        self.validate(game)
        spend_to_discard(
            game,
            "play_debt_collector",
            self.hand_index,
            action_type=ActionCardType.DEBT_COLLECTOR,
        )
        creditor = game.current_player_idx
        open_payment(
            game,
            PaymentDue(
                creditor_idx=creditor,
                debtor_idx=self.target_player_idx,
                amount_m=DEBT_COLLECTOR_PAYMENT_M,
            ),
        )
