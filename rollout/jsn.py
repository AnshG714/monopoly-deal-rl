"""Just Say No chain outcomes (optimal play from JSN counts only)."""

from __future__ import annotations

from models.cards.action import ActionCard, ActionCardType
from models.player import Player


def count_jsns(player: Player) -> int:
    return sum(
        1
        for card in player.hand
        if isinstance(card, ActionCard) and card.action_type == ActionCardType.JUST_SAY_NO
    )


def debt_or_action_cancelled(
    defender_jsns: int,
    actor_jsns: int,
    responder: str,
    chain_started: bool,
) -> bool:
    """True if the debt/action is cancelled under optimal play from this state.

    Defender (debtor / steal victim) wants cancel; actor (creditor / attacker) wants proceed.
    """
    if responder == "defender":
        outcomes: list[bool] = []
        # Passing lets the action/debt proceed; JSN flips the chain to the actor.
        if not chain_started:
            outcomes.append(False)
        else:
            outcomes.append(False)
        if defender_jsns > 0:
            outcomes.append(
                debt_or_action_cancelled(
                    defender_jsns - 1, actor_jsns, "actor", True
                )
            )
        return max(outcomes)
    # Actor passing cancels; actor JSN-ing keeps the chain alive.
    outcomes = [True]
    if actor_jsns > 0:
        outcomes.append(
            debt_or_action_cancelled(
                defender_jsns, actor_jsns - 1, "defender", True
            )
        )
    return min(outcomes)


def side_wins_if_plays_jsn(
    defender_jsns: int,
    actor_jsns: int,
    responder: str,
    chain_started: bool,
    *,
    side: str,
) -> bool:
    """True if ``side`` ('defender' or 'actor') should play JSN now (optimal for that side)."""
    if side != responder:
        return False
    if side == "defender":
        if defender_jsns <= 0:
            return False
        return debt_or_action_cancelled(
            defender_jsns - 1, actor_jsns, "actor", True
        )
    if actor_jsns <= 0:
        return False
    return not debt_or_action_cancelled(
        defender_jsns, actor_jsns - 1, "defender", True
    )
