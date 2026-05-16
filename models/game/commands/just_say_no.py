from __future__ import annotations

from dataclasses import dataclass

from ...cards.action import ActionCardType
from ..pending import (
    JustSayNoNegotiation,
    PaymentDue,
    jsn_responder_player_idx,
)
from .base import (
    GameView,
    clear_pending_back_to_turn,
    jsn_flip_after_play,
    pop_hand_action,
    require_acting,
    require_deal_jsn_prompt,
    require_hand_action,
    require_interrupt,
    require_jsn_responder_matches_acting,
)
from .effects import resolve_deal_interrupt


def _pop_just_say_no_from_hand(
    game: GameView, player_idx: int, hand_index: int
) -> None:
    card = pop_hand_action(game, player_idx, hand_index, ActionCardType.JUST_SAY_NO)
    game.discard_pile.append(card)


@dataclass(frozen=True)
class PlayJustSayNo:
    hand_index: int

    def validate(self, game: GameView) -> None:
        pending = require_interrupt(game)
        if isinstance(pending, PaymentDue):
            if pending.jsn is None:
                require_acting(
                    game,
                    pending.debtor_idx,
                    "Only the debtor may play Just Say No on this debt",
                )
                require_hand_action(
                    game,
                    pending.debtor_idx,
                    self.hand_index,
                    ActionCardType.JUST_SAY_NO,
                )
                return
            responder_idx = require_jsn_responder_matches_acting(
                game,
                pending.jsn,
                message="It is not your turn to respond with Just Say No",
            )
            require_hand_action(
                game, responder_idx, self.hand_index, ActionCardType.JUST_SAY_NO
            )
            return

        _, jsn = require_deal_jsn_prompt(pending)
        responder_idx = require_jsn_responder_matches_acting(
            game, jsn, message="It is not your turn to respond with Just Say No"
        )
        require_hand_action(
            game, responder_idx, self.hand_index, ActionCardType.JUST_SAY_NO
        )

    def apply(self, game: GameView) -> None:
        self.validate(game)
        pending = require_interrupt(game)

        if isinstance(pending, PaymentDue):
            if pending.jsn is None:
                _pop_just_say_no_from_hand(game, pending.debtor_idx, self.hand_index)
                pending.jsn = JustSayNoNegotiation(
                    defender_idx=pending.debtor_idx,
                    actor_idx=pending.creditor_idx,
                    responder="actor",
                    chain_started=True,
                )
                game.acting_player_idx = pending.creditor_idx
                return

            responder_idx = jsn_responder_player_idx(pending.jsn)
            _pop_just_say_no_from_hand(game, responder_idx, self.hand_index)
            pending.jsn = jsn_flip_after_play(pending.jsn)
            game.acting_player_idx = jsn_responder_player_idx(pending.jsn)
            return

        deal_pending, jsn = require_deal_jsn_prompt(pending)
        responder_idx = jsn_responder_player_idx(jsn)
        _pop_just_say_no_from_hand(game, responder_idx, self.hand_index)
        deal_pending.jsn = jsn_flip_after_play(jsn)
        game.acting_player_idx = jsn_responder_player_idx(deal_pending.jsn)


@dataclass(frozen=True)
class PassJustSayNo:
    def validate(self, game: GameView) -> None:
        pending = require_interrupt(game)
        if isinstance(pending, PaymentDue):
            if pending.jsn is None:
                raise RuntimeError("No Just Say No chain is active for this payment")
            require_jsn_responder_matches_acting(
                game,
                pending.jsn,
                message="It is not your turn to pass on Just Say No",
            )
            return

        _, jsn = require_deal_jsn_prompt(pending)
        require_jsn_responder_matches_acting(
            game, jsn, message="It is not your turn to pass on Just Say No"
        )

    def apply(self, game: GameView) -> None:
        self.validate(game)
        pending = require_interrupt(game)

        if isinstance(pending, PaymentDue):
            jsn = pending.jsn
            if jsn is None:
                raise RuntimeError("No Just Say No chain is active for this payment")
            if jsn.responder == "actor":
                # Creditor declines to counter; debtor's JSN cancels the payment.
                clear_pending_back_to_turn(game)
                return
            pending.jsn = None
            game.acting_player_idx = pending.debtor_idx
            return

        deal_pending, jsn = require_deal_jsn_prompt(pending)
        if jsn.responder == "defender":
            resolve_deal_interrupt(game, deal_pending)
            clear_pending_back_to_turn(game)
            return

        # Actor declines to counter; defender's last JSN cancels the action.
        clear_pending_back_to_turn(game)
