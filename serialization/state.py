"""Player point-of-view snapshots of a game."""

from __future__ import annotations

from models.cards.property import Color
from models.game.game import Game
from models.game.pending import (
    DealBreakerPending,
    DealBreakerTheftIntent,
    ForcedDealPending,
    ForcedDealSwapIntent,
    JustSayNoNegotiation,
    PaymentDue,
    Pending,
    SlyDealPending,
    SlyDealStealIntent,
)

from .cards import serialize_card, serialize_property_set


def serialize_pending(pending: Pending | None) -> dict | None:
    if pending is None:
        return None

    if isinstance(pending, PaymentDue):
        payload: dict = {
            "kind": "PaymentDue",
            "creditor_idx": pending.creditor_idx,
            "debtor_idx": pending.debtor_idx,
            "amount_m": pending.amount_m,
        }
        if pending.jsn is not None:
            payload["jsn"] = {
                "defender_idx": pending.jsn.defender_idx,
                "actor_idx": pending.jsn.actor_idx,
                "responder": pending.jsn.responder,
                "chain_started": pending.jsn.chain_started,
            }
        return payload

    if isinstance(pending, SlyDealPending):
        return {
            "kind": "SlyDealPending",
            "actor_idx": pending.actor_idx,
            "victim_idx": pending.steal.victim_idx,
            "target_set_idx": pending.steal.target_set_idx,
            "target_card_idx": pending.steal.target_card_idx,
            "into_color": pending.steal.into_color.value,
        }

    if isinstance(pending, ForcedDealPending):
        swap = pending.swap
        return {
            "kind": "ForcedDealPending",
            "actor_idx": pending.actor_idx,
            "target_player_idx": swap.target_player_idx,
            "my_set_idx": swap.my_set_idx,
            "my_card_idx": swap.my_card_idx,
            "their_set_idx": swap.their_set_idx,
            "their_card_idx": swap.their_card_idx,
            "take_into_color": swap.take_into_color.value,
            "give_into_color": swap.give_into_color.value,
        }

    if isinstance(pending, DealBreakerPending):
        return {
            "kind": "DealBreakerPending",
            "actor_idx": pending.actor_idx,
            "victim_idx": pending.theft.victim_idx,
            "victim_set_idx": pending.theft.victim_set_idx,
        }

    return {"kind": type(pending).__name__}


def _deserialize_jsn(payload: dict | None) -> JustSayNoNegotiation | None:
    if payload is None:
        return None
    return JustSayNoNegotiation(
        defender_idx=payload["defender_idx"],
        actor_idx=payload["actor_idx"],
        responder=payload["responder"],
        chain_started=payload["chain_started"],
    )


def deserialize_pending(payload: dict | None) -> Pending | None:
    """Rebuild pending state from ``serialize_pending`` output."""
    if payload is None:
        return None

    kind = payload["kind"]
    if kind == "PaymentDue":
        return PaymentDue(
            creditor_idx=payload["creditor_idx"],
            debtor_idx=payload["debtor_idx"],
            amount_m=payload["amount_m"],
            jsn=_deserialize_jsn(payload.get("jsn")),
        )

    if kind == "SlyDealPending":
        actor_idx = payload["actor_idx"]
        victim_idx = payload["victim_idx"]
        steal = SlyDealStealIntent(
            victim_idx=victim_idx,
            target_set_idx=payload["target_set_idx"],
            target_card_idx=payload["target_card_idx"],
            into_color=Color(payload["into_color"]),
        )
        jsn = _deserialize_jsn(payload.get("jsn")) or JustSayNoNegotiation.open_negotiation(
            victim_idx, actor_idx
        )
        return SlyDealPending(actor_idx=actor_idx, steal=steal, jsn=jsn)

    if kind == "ForcedDealPending":
        actor_idx = payload["actor_idx"]
        target_player_idx = payload["target_player_idx"]
        swap = ForcedDealSwapIntent(
            target_player_idx=target_player_idx,
            my_set_idx=payload["my_set_idx"],
            my_card_idx=payload["my_card_idx"],
            their_set_idx=payload["their_set_idx"],
            their_card_idx=payload["their_card_idx"],
            take_into_color=Color(payload["take_into_color"]),
            give_into_color=Color(payload["give_into_color"]),
        )
        jsn = _deserialize_jsn(payload.get("jsn")) or JustSayNoNegotiation.open_negotiation(
            target_player_idx, actor_idx
        )
        return ForcedDealPending(actor_idx=actor_idx, swap=swap, jsn=jsn)

    if kind == "DealBreakerPending":
        actor_idx = payload["actor_idx"]
        victim_idx = payload["victim_idx"]
        theft = DealBreakerTheftIntent(
            victim_idx=victim_idx,
            victim_set_idx=payload["victim_set_idx"],
        )
        jsn = _deserialize_jsn(payload.get("jsn")) or JustSayNoNegotiation.open_negotiation(
            victim_idx, actor_idx
        )
        return DealBreakerPending(actor_idx=actor_idx, theft=theft, jsn=jsn)

    raise ValueError(f"unknown pending kind: {kind!r}")


def _serialize_player(game: Game, player_idx: int, *, viewer_idx: int) -> dict:
    player = game.players[player_idx]
    hide_hand = player_idx != viewer_idx
    hand_cards = None
    if not hide_hand:
        hand_cards = [
            {"index": index, **serialize_card(card)}
            for index, card in enumerate(player.hand)
        ]

    return {
        "idx": player_idx,
        "name": player.name,
        "complete_sets": player.complete_set_count(),
        "hand": {
            "size": len(player.hand),
            "cards": hand_cards,
        },
        "bank": [serialize_card(card) for card in player.money_pile],
        "property_sets": [
            serialize_property_set(pile) for pile in player.property_sets
        ],
    }


def view_for_player(game: Game, viewer_idx: int) -> dict:
    """Return a JSON-safe snapshot from ``viewer_idx``'s perspective."""
    return {
        "viewer_idx": viewer_idx,
        "current_player_idx": game.current_player_idx,
        "acting_player_idx": game.acting_player_idx,
        "plays_this_turn": game.plays_this_turn,
        "deck_size": len(game.deck),
        "discard_size": len(game.discard_pile),
        "discard_top": (
            serialize_card(game.discard_pile[-1]) if game.discard_pile else None
        ),
        "pending": serialize_pending(game.pending),
        "players": [
            _serialize_player(game, player_idx, viewer_idx=viewer_idx)
            for player_idx in range(len(game.players))
        ],
    }
