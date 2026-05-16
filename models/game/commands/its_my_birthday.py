from __future__ import annotations

from dataclasses import dataclass

from ...cards.action import ActionCardType
from ..pending import PaymentDue
from .base import (
    GameView,
    open_payment,
    require_hand_action,
    require_main_phase_hand_play,
    spend_to_discard,
)

BIRTHDAY_GIFT_M = 2


@dataclass(frozen=True)
class PlayItsMyBirthday:
    """All other players owe you $2M each.

    With the current single ``PaymentDue`` model, only the first opponent's debt
    is opened here; multi-opponent birthday chains can be layered later.
    """

    hand_index: int

    def validate(self, game: GameView) -> None:
        require_main_phase_hand_play(game, "play_its_my_birthday")
        require_hand_action(
            game,
            game.current_player_idx,
            self.hand_index,
            ActionCardType.ITS_MY_BIRTHDAY,
        )
        others = [i for i in range(len(game.players)) if i != game.current_player_idx]
        if not others:
            raise ValueError("No opponents to charge")

    def apply(self, game: GameView) -> None:
        self.validate(game)
        spend_to_discard(
            game,
            "play_its_my_birthday",
            self.hand_index,
            action_type=ActionCardType.ITS_MY_BIRTHDAY,
        )
        others = [i for i in range(len(game.players)) if i != game.current_player_idx]

        # TODO: Handle multi-player birthday chains.
        debtor = others[0]
        open_payment(
            game,
            PaymentDue(
                creditor_idx=game.current_player_idx,
                debtor_idx=debtor,
                amount_m=BIRTHDAY_GIFT_M,
            ),
        )
