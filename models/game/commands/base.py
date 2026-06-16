"""Shared command protocols and validation helpers.

Command validation usually checks the broad game phase first, then the exact
card being played, then command-specific target legality:

    def validate(self, game: GameView) -> None:
        require_main_phase_hand_play(game, "play_sly_deal")
        require_hand_action(
            game, game.current_player_idx, self.hand_index, ActionCardType.SLY_DEAL
        )
        self._build_intent(game)
"""

from __future__ import annotations

import random
from typing import Hashable, Protocol

from ...cards.action import ActionCard, ActionCardType
from ...cards.base import Card, CardType
from ...player import Player
from ..pending import (
    DealBreakerPending,
    ForcedDealPending,
    JustSayNoNegotiation,
    PaymentDue,
    Pending,
    SlyDealPending,
    jsn_responder_player_idx,
)

DealInterrupt = SlyDealPending | ForcedDealPending | DealBreakerPending

MAX_PLAYS_PER_TURN = 3


class GameView(Protocol):
    """Minimum mutable game surface required by commands."""

    _rng: random.Random
    players: list[Player]
    deck: list[Card]
    discard_pile: list[Card]
    current_player_idx: int
    acting_player_idx: int
    pending: Pending | None
    plays_this_turn: int

    def current_player(self) -> Player: ...
    def shuffle_deck(self) -> None: ...


class GameCommand(Hashable, Protocol):
    """A legal game move candidate."""

    def validate(self, game: GameView) -> None:
        """Raise if this move is not currently legal."""

    def apply(self, game: GameView) -> None:
        """Apply this move, raising if it is not legal."""


def require_acting(game: GameView, player_idx: int, message: str) -> None:
    """Require the prompt actor to be ``player_idx``.

    ``acting_player_idx`` is the player who may respond to the current prompt.
    It can differ from ``current_player_idx`` during payments and Just Say No
    windows. Raises ``RuntimeError(message)`` when another player is acting.
    """
    if game.acting_player_idx != player_idx:
        raise RuntimeError(message)


def require_main_phase(game: GameView, action: str) -> None:
    """Require a normal current-player action during the main phase.

    Main-phase actions are blocked while a prompt is pending, and they must be
    taken by ``current_player_idx`` rather than an out-of-turn responder.
    """
    if game.pending is not None:
        raise RuntimeError(f"{action} is illegal during a pending prompt")
    if game.acting_player_idx != game.current_player_idx:
        raise RuntimeError(f"{action} only for the current turn player")


def require_main_phase_hand_play(game: GameView, action: str) -> None:
    """Require a main-phase hand play with plays remaining this turn."""
    require_main_phase_hand_plays(game, action, 1)


def require_main_phase_hand_plays(game: GameView, action: str, plays: int) -> None:
    """Require enough main-phase play budget for ``plays`` cards from hand."""
    require_main_phase(game, action)
    if plays < 1:
        raise ValueError("plays must be at least 1")
    if game.plays_this_turn + plays > MAX_PLAYS_PER_TURN:
        raise RuntimeError("Already played max cards this turn")


def require_interrupt(game: GameView) -> Pending:
    """Return the active prompt, or raise if no interruption is pending.

    Use this at the start of commands that only make sense while ``game.pending``
    is set, such as paying debt or responding with Just Say No.
    """
    pending = game.pending
    if pending is None:
        raise RuntimeError("No interrupt is pending")
    return pending


def require_pending_payment(pending: Pending | None) -> PaymentDue:
    """Return the active ``PaymentDue`` prompt, or raise if none is pending."""
    if not isinstance(pending, PaymentDue):
        raise RuntimeError("No payment is pending")
    return pending


def require_no_pending(game: GameView, message: str) -> None:
    """Raise if a payment or other interrupt prompt is already active."""
    if game.pending is not None:
        raise RuntimeError(message)


def open_interrupt(
    game: GameView,
    pending: Pending,
    *,
    acting_player_idx: int,
) -> None:
    """Attach a prompt and set who must respond next."""
    require_no_pending(game, "A prompt is already pending")
    game.pending = pending
    game.acting_player_idx = acting_player_idx


def open_payment(game: GameView, due: PaymentDue) -> None:
    """Open a payment prompt; the debtor must pay or Just Say No."""
    if due.amount_m <= 0:
        raise ValueError("amount_m must be positive")
    open_interrupt(game, due, acting_player_idx=due.debtor_idx)


def require_deal_jsn_prompt(
    pending: Pending,
) -> tuple[DealInterrupt, JustSayNoNegotiation]:
    """Return a targeted deal prompt and its Just Say No negotiation.

    This applies to Sly Deal, Forced Deal, and Deal Breaker prompts after the
    action has been declared. Payment-specific JSN handling stays separate
    because payments resolve differently from targeted deal actions.
    """
    if not isinstance(pending, (SlyDealPending, ForcedDealPending, DealBreakerPending)):
        raise RuntimeError("Just Say No does not apply to this prompt")
    return pending, pending.jsn


def jsn_flip_after_play(jsn: JustSayNoNegotiation) -> JustSayNoNegotiation:
    """Next responder after someone plays Just Say No."""
    if jsn.responder == "defender":
        return JustSayNoNegotiation(
            defender_idx=jsn.defender_idx,
            actor_idx=jsn.actor_idx,
            responder="actor",
            chain_started=True,
        )
    return JustSayNoNegotiation(
        defender_idx=jsn.defender_idx,
        actor_idx=jsn.actor_idx,
        responder="defender",
        chain_started=True,
    )


def require_jsn_responder_matches_acting(
    game: GameView, jsn: JustSayNoNegotiation, *, message: str
) -> int:
    """Require the current JSN responder to be the acting player.

    Returns the responder index for follow-up hand checks. Raises
    ``RuntimeError(message)`` if another player is acting.
    """
    responder_idx = jsn_responder_player_idx(jsn)
    require_acting(game, responder_idx, message)
    return responder_idx


def require_hand_card(
    game: GameView,
    player_idx: int,
    hand_index: int,
    *,
    action_type: ActionCardType | None = None,
    card_type: CardType | None = None,
) -> Card:
    """Return a hand card, optionally constrained by action or card type."""
    player = game.players[player_idx]
    if hand_index < 0 or hand_index >= len(player.hand):
        raise IndexError("hand_index out of range")
    card = player.hand[hand_index]
    if card_type is not None and card.type != card_type:
        raise TypeError(f"Card must be a {card_type.value} card")
    if action_type is not None:
        if not isinstance(card, ActionCard) or card.action_type != action_type:
            raise TypeError(f"Card must be a {action_type.value} action card")
    return card


def require_hand_action(
    game: GameView, player_idx: int, hand_index: int, expected: ActionCardType
) -> ActionCard:
    """Return the expected action card from a player's hand."""
    card = require_hand_card(game, player_idx, hand_index, action_type=expected)
    return card  # narrowed by action_type check


def player_at(game: GameView, idx: int) -> Player:
    """Return a player by index, or raise if the index is invalid."""
    if idx < 0 or idx >= len(game.players):
        raise IndexError("player index out of range")
    return game.players[idx]


def pop_from_hand(
    game: GameView,
    player_idx: int,
    hand_index: int,
    *,
    action_type: ActionCardType | None = None,
    card_type: CardType | None = None,
) -> Card:
    """Remove and return a card from hand, with optional type checks."""
    card = require_hand_card(
        game, player_idx, hand_index, action_type=action_type, card_type=card_type
    )
    game.players[player_idx].hand.pop(hand_index)
    return card


def discard_from_hand(
    game: GameView,
    player_idx: int,
    hand_index: int,
    *,
    action_type: ActionCardType | None = None,
    card_type: CardType | None = None,
) -> Card:
    """Remove a card from hand and move it to the discard pile."""
    card = pop_from_hand(
        game,
        player_idx,
        hand_index,
        action_type=action_type,
        card_type=card_type,
    )
    game.discard_pile.append(card)
    return card


def discard_from_hand_indices(
    game: GameView, player_idx: int, *hand_indices: int
) -> tuple[Card, ...]:
    """Remove several hand cards (by index) and discard them.

    Indices must be distinct. Cards are returned in the same order as
    ``hand_indices``. Pops higher indices first so lower indices stay valid.
    """
    if len(hand_indices) < 1:
        raise ValueError("hand_indices must not be empty")
    if len(set(hand_indices)) != len(hand_indices):
        raise ValueError("hand_indices must be distinct")
    player = game.players[player_idx]
    if max(hand_indices) >= len(player.hand) or min(hand_indices) < 0:
        raise IndexError("hand_index out of range")
    order = sorted(hand_indices, reverse=True)
    popped: dict[int, Card] = {}
    for idx in order:
        popped[idx] = player.hand.pop(idx)
        game.discard_pile.append(popped[idx])
    return tuple(popped[i] for i in hand_indices)


def record_hand_plays(game: GameView, plays: int) -> None:
    """Increment the current turn's play count after card(s) left hand."""
    game.plays_this_turn += plays


def clear_pending_back_to_turn(game: GameView) -> None:
    """Clear a prompt and return action to the current turn player."""
    game.pending = None
    game.acting_player_idx = game.current_player_idx


def reshuffle_discard_into_deck_if_empty(game: GameView) -> None:
    """Refill the deck from discard when the draw pile is empty."""
    if game.deck:
        return
    if not game.discard_pile:
        return
    game._rng.shuffle(game.discard_pile)
    game.deck = game.discard_pile
    game.discard_pile = []


def draw_for_player(game: GameView, player_idx: int, n: int) -> int:
    """Draw up to ``n`` cards into a player's hand. Returns cards drawn."""
    drawn = 0
    player = player_at(game, player_idx)
    for _ in range(n):
        reshuffle_discard_into_deck_if_empty(game)
        if not game.deck:
            break
        player.deal_to_hand(game.deck.pop())
        drawn += 1
    return drawn


def draw_for_current_player(game: GameView, n: int) -> int:
    """Draw up to ``n`` cards into the current player's hand."""
    return draw_for_player(game, game.current_player_idx, n)


def spend_to_discard(
    game: GameView,
    action_name: str,
    hand_index: int,
    *,
    plays: int = 1,
    action_type: ActionCardType | None = None,
    card_type: CardType | None = None,
) -> Card:
    """Spend main-phase play budget, discard one card from the current player's hand."""
    require_main_phase_hand_plays(game, action_name, plays)
    card = discard_from_hand(
        game,
        game.current_player_idx,
        hand_index,
        action_type=action_type,
        card_type=card_type,
    )
    record_hand_plays(game, plays)
    return card


def spend_to_discard_indices(
    game: GameView,
    action_name: str,
    hand_indices: tuple[int, ...],
    *,
    plays: int,
) -> tuple[Card, ...]:
    """Spend play budget and discard several cards from the current player's hand."""
    require_main_phase_hand_plays(game, action_name, plays)
    cards = discard_from_hand_indices(game, game.current_player_idx, *hand_indices)
    record_hand_plays(game, plays)
    return cards


def spend_to_discard_and_interrupt(
    game: GameView,
    *,
    action_name: str,
    hand_index: int,
    action_type: ActionCardType,
    pending: Pending,
    acting_player_idx: int,
    plays: int = 1,
) -> Card:
    """Discard an action card from hand, count play(s), and open an interrupt."""
    card = spend_to_discard(
        game,
        action_name,
        hand_index,
        plays=plays,
        action_type=action_type,
    )
    open_interrupt(game, pending, acting_player_idx=acting_player_idx)
    return card
