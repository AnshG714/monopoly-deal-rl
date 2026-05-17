"""Enumerate every legal ``GameCommand`` for ``game.acting_player_idx``."""

from __future__ import annotations

from ..cards.action import ActionCard, ActionCardType
from ..cards.property import Color, PropertyCard
from ..cards.rent import RentCard, WildRentCard
from ..player import Player
from .commands import (
    DiscardCards,
    EndTurn,
    GameCommand,
    GameView,
    MAX_HAND_SIZE_AT_END_OF_TURN,
    PassJustSayNo,
    PayDebt,
    PlayDealBreaker,
    PlayDebtCollector,
    PlayDoubleRent,
    PlayForcedDeal,
    PlayHotel,
    PlayHouse,
    PlayItsMyBirthday,
    PlayJustSayNo,
    PlayMoneyFromHand,
    PlayPassGo,
    PlayPropertyFromHand,
    PlayRent,
    PlaySlyDeal,
)
from .combinatorics import combinations_greater_than_amount
from .commands.base import require_pending_payment
from .commands.rent import rent_card_allows_color, rent_m_due_for_color
from .pending import (
    DealBreakerPending,
    ForcedDealPending,
    PaymentDue,
    SlyDealPending,
    jsn_responder_player_idx,
)

LEGAL_MOVE_ERRORS = (ValueError, TypeError, IndexError, RuntimeError)


def legal_moves(game: GameView) -> list[GameCommand]:
    """All legal commands for whoever must act (``game.acting_player_idx``)."""
    pending = game.pending
    if isinstance(pending, PaymentDue):
        return _legal_payment_moves(game, pending)
    if isinstance(pending, (SlyDealPending, ForcedDealPending, DealBreakerPending)):
        return _enumerate_jsn_interrupt(game)
    return _legal_main_phase_moves(game)


def _try_validate(cmd: GameCommand, game: GameView) -> bool:
    try:
        cmd.validate(game)
        return True
    except LEGAL_MOVE_ERRORS:
        return False


def _append_if_legal(
    moves: list[GameCommand], cmd: GameCommand, game: GameView
) -> None:
    if _try_validate(cmd, game):
        moves.append(cmd)


def _command_dedupe_key(cmd: GameCommand) -> object:
    if isinstance(cmd, PayDebt):
        return (
            PayDebt,
            tuple(cmd._selected_money_indices()),
            tuple(cmd._selected_property_indices()),
        )
    if isinstance(cmd, DiscardCards):
        return (DiscardCards, tuple(sorted(cmd.hand_indices)))
    return cmd


def _dedupe_commands(moves: list[GameCommand]) -> list[GameCommand]:
    seen: set[object] = set()
    unique: list[GameCommand] = []
    for cmd in moves:
        key = _command_dedupe_key(cmd)
        if key in seen:
            continue
        seen.add(key)
        unique.append(cmd)
    return unique


def _must_discard_to_end_turn(game: GameView) -> bool:
    return (
        game.pending is None
        and game.acting_player_idx == game.current_player_idx
        and len(game.current_player().hand) > MAX_HAND_SIZE_AT_END_OF_TURN
    )


def _legal_main_phase_moves(game: GameView) -> list[GameCommand]:
    if game.acting_player_idx != game.current_player_idx:
        return []
    if _must_discard_to_end_turn(game):
        return _validated(DiscardCards.enumerate(game), game)
    moves: list[GameCommand] = []
    _append_if_legal(moves, EndTurn(), game)
    moves.extend(_enumerate_main_phase_hand_plays(game))
    return _dedupe_commands(moves)


def _validated(candidates: list[GameCommand], game: GameView) -> list[GameCommand]:
    return [cmd for cmd in candidates if _try_validate(cmd, game)]


def _enumerate_main_phase_hand_plays(game: GameView) -> list[GameCommand]:
    moves: list[GameCommand] = []
    hand = game.current_player().hand
    for hand_index, card in enumerate(hand):
        if not isinstance(card, PropertyCard):
            _append_if_legal(moves, PlayMoneyFromHand(hand_index), game)
        if isinstance(card, PropertyCard):
            for color in Color:
                _append_if_legal(moves, PlayPropertyFromHand(hand_index, color), game)
        elif isinstance(card, ActionCard):
            moves.extend(_enumerate_action_card(game, hand_index, card))
        elif isinstance(card, (RentCard, WildRentCard)):
            moves.extend(_enumerate_rent_for_hand_index(game, hand_index))
    moves.extend(_enumerate_double_rent(game))
    return moves


def _enumerate_action_card(
    game: GameView, hand_index: int, card: ActionCard
) -> list[GameCommand]:
    moves: list[GameCommand] = []
    match card.action_type:
        case ActionCardType.PASS_GO:
            _append_if_legal(moves, PlayPassGo(hand_index), game)
        case ActionCardType.HOUSE:
            moves.extend(_enumerate_house(game, hand_index))
        case ActionCardType.HOTEL:
            moves.extend(_enumerate_hotel(game, hand_index))
        case ActionCardType.DEBT_COLLECTOR:
            moves.extend(_enumerate_debt_collector(game, hand_index))
        case ActionCardType.ITS_MY_BIRTHDAY:
            _append_if_legal(moves, PlayItsMyBirthday(hand_index), game)
        case ActionCardType.SLY_DEAL:
            moves.extend(_enumerate_sly_deal(game, hand_index))
        case ActionCardType.FORCED_DEAL:
            moves.extend(_enumerate_forced_deal(game, hand_index))
        case ActionCardType.DEAL_BREAKER:
            moves.extend(_enumerate_deal_breaker(game, hand_index))
        case ActionCardType.DOUBLE_RENT:
            pass  # handled in _enumerate_double_rent
    return moves


def _enumerate_house(game: GameView, hand_index: int) -> list[GameCommand]:
    moves: list[GameCommand] = []
    for target_set_idx in range(len(game.current_player().property_sets)):
        _append_if_legal(moves, PlayHouse(hand_index, target_set_idx), game)
    return moves


def _enumerate_hotel(game: GameView, hand_index: int) -> list[GameCommand]:
    moves: list[GameCommand] = []
    for target_set_idx in range(len(game.current_player().property_sets)):
        _append_if_legal(moves, PlayHotel(hand_index, target_set_idx), game)
    return moves


def _enumerate_debt_collector(game: GameView, hand_index: int) -> list[GameCommand]:
    moves: list[GameCommand] = []
    current = game.current_player_idx
    for target_player_idx in range(len(game.players)):
        if target_player_idx == current:
            continue
        _append_if_legal(moves, PlayDebtCollector(hand_index, target_player_idx), game)
    return moves


def _enumerate_sly_deal(game: GameView, hand_index: int) -> list[GameCommand]:
    moves: list[GameCommand] = []
    current = game.current_player_idx
    for target_player_idx in range(len(game.players)):
        if target_player_idx == current:
            continue
        victim = game.players[target_player_idx]
        for target_set_idx, pile in enumerate(victim.property_sets):
            if pile.is_complete():
                continue
            for target_card_idx in range(len(pile.cards)):
                for into_color in Color:
                    _append_if_legal(
                        moves,
                        PlaySlyDeal(
                            hand_index,
                            target_player_idx,
                            target_set_idx,
                            target_card_idx,
                            into_color,
                        ),
                        game,
                    )
    return moves


def _enumerate_forced_deal(game: GameView, hand_index: int) -> list[GameCommand]:
    moves: list[GameCommand] = []
    actor = game.current_player()
    current = game.current_player_idx
    for target_player_idx in range(len(game.players)):
        if target_player_idx == current:
            continue
        target = game.players[target_player_idx]
        for my_set_idx, my_pile in enumerate(actor.property_sets):
            if my_pile.is_complete():
                continue
            for my_card_idx in range(len(my_pile.cards)):
                for their_set_idx, their_pile in enumerate(target.property_sets):
                    if their_pile.is_complete():
                        continue
                    for their_card_idx in range(len(their_pile.cards)):
                        _append_if_legal(
                            moves,
                            PlayForcedDeal(
                                hand_index,
                                target_player_idx,
                                my_set_idx,
                                my_card_idx,
                                their_set_idx,
                                their_card_idx,
                            ),
                            game,
                        )
    return moves


def _enumerate_deal_breaker(game: GameView, hand_index: int) -> list[GameCommand]:
    moves: list[GameCommand] = []
    current = game.current_player_idx
    for victim_idx in range(len(game.players)):
        if victim_idx == current:
            continue
        victim = game.players[victim_idx]
        for victim_set_idx, pile in enumerate(victim.property_sets):
            if not pile.is_complete():
                continue
            _append_if_legal(
                moves, PlayDealBreaker(hand_index, victim_idx, victim_set_idx), game
            )
    return moves


def _rent_colors_for_card(card: RentCard | WildRentCard) -> list[Color]:
    if isinstance(card, WildRentCard):
        return list(Color)
    return [card.color1, card.color2]


def _enumerate_rent_for_hand_index(
    game: GameView, rent_hand_index: int
) -> list[GameCommand]:
    moves: list[GameCommand] = []
    hand = game.current_player().hand
    if rent_hand_index < 0 or rent_hand_index >= len(hand):
        return moves
    card = hand[rent_hand_index]
    if not isinstance(card, (RentCard, WildRentCard)):
        return moves

    creditor = game.current_player()
    current = game.current_player_idx
    for victim_idx in range(len(game.players)):
        if victim_idx == current:
            continue
        for charged_color in _rent_colors_for_card(card):
            if not rent_card_allows_color(card, charged_color):
                continue
            if rent_m_due_for_color(creditor, charged_color) <= 0:
                continue
            _append_if_legal(
                moves, PlayRent(rent_hand_index, victim_idx, charged_color), game
            )
    return moves


def _enumerate_double_rent(game: GameView) -> list[GameCommand]:
    moves: list[GameCommand] = []
    hand = game.current_player().hand
    double_indices = [
        i
        for i, card in enumerate(hand)
        if isinstance(card, ActionCard)
        and card.action_type == ActionCardType.DOUBLE_RENT
    ]
    rent_indices = [
        i for i, card in enumerate(hand) if isinstance(card, (RentCard, WildRentCard))
    ]
    current = game.current_player_idx
    creditor = game.current_player()

    for double_rent_hand_index in double_indices:
        for rent_hand_index in rent_indices:
            if double_rent_hand_index == rent_hand_index:
                continue
            rent_card = hand[rent_hand_index]
            if not isinstance(rent_card, (RentCard, WildRentCard)):
                continue
            for victim_idx in range(len(game.players)):
                if victim_idx == current:
                    continue
                for charged_color in _rent_colors_for_card(rent_card):
                    if not rent_card_allows_color(rent_card, charged_color):
                        continue
                    if rent_m_due_for_color(creditor, charged_color) <= 0:
                        continue
                    _append_if_legal(
                        moves,
                        PlayDoubleRent(
                            double_rent_hand_index,
                            rent_hand_index,
                            victim_idx,
                            charged_color,
                        ),
                        game,
                    )
    return moves


def _legal_payment_moves(game: GameView, due: PaymentDue) -> list[GameCommand]:
    moves: list[GameCommand] = []
    if game.acting_player_idx == due.debtor_idx:
        if due.jsn is None or jsn_responder_player_idx(due.jsn) == due.debtor_idx:
            moves.extend(_enumerate_pay_debt(game))
    moves.extend(_enumerate_jsn_interrupt(game))
    return _dedupe_commands(moves)


def _enumerate_jsn_interrupt(game: GameView) -> list[GameCommand]:
    moves: list[GameCommand] = []
    _append_if_legal(moves, PassJustSayNo(), game)
    actor = game.players[game.acting_player_idx]
    for hand_index in range(len(actor.hand)):
        _append_if_legal(moves, PlayJustSayNo(hand_index), game)
    return moves


def _pay_debt_from_asset_indices(
    asset_entries: list[tuple[str, int | tuple[int, int]]],
    selected_indices: list[int],
) -> PayDebt:
    money_indices: list[int] = []
    property_indices: list[tuple[int, int]] = []
    for asset_index in selected_indices:
        kind, index = asset_entries[asset_index]
        if kind == "m":
            money_indices.append(index)  # type: ignore[arg-type]
        else:
            property_indices.append(index)  # type: ignore[arg-type]
    return PayDebt(money_indices, property_indices)


def _enumerate_pay_debt(game: GameView) -> list[PayDebt]:
    due = require_pending_payment(game.pending)
    debtor: Player = game.players[due.debtor_idx]

    asset_entries: list[tuple[str, int | tuple[int, int]]] = []
    asset_values: list[int] = []
    for money_index, card in enumerate(debtor.money_pile):
        asset_entries.append(("m", money_index))
        asset_values.append(card.value)
    for set_idx, pile in enumerate(debtor.property_sets):
        for card_idx, card in enumerate(pile.cards):
            asset_entries.append(("p", (set_idx, card_idx)))
            asset_values.append(card.value)

    moves: list[PayDebt] = []
    asset_count = len(asset_entries)

    if asset_count == 0:
        cmd = PayDebt([], [])
        if _try_validate(cmd, game):
            return [cmd]
        return []

    candidate_indices: list[list[int]] = list(
        combinations_greater_than_amount(asset_values, due.amount_m)
    )
    if sum(asset_values) < due.amount_m:
        candidate_indices.append(list(range(asset_count)))

    seen: set[tuple[tuple[int, ...], tuple[tuple[int, int], ...]]] = set()
    for selected_indices in candidate_indices:
        cmd = _pay_debt_from_asset_indices(asset_entries, selected_indices)
        key = (
            tuple(cmd._selected_money_indices()),
            tuple(cmd._selected_property_indices()),
        )
        if key in seen:
            continue
        seen.add(key)
        if _try_validate(cmd, game):
            moves.append(cmd)
    return moves
