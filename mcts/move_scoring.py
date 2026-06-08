"""Cheap command scoring for MCTS move pruning.

This module deliberately avoids copy/apply/evaluate. It ranks legal commands
from their fields and the current board so large move lists can be pruned
without spending more than the saved search work.
"""

from __future__ import annotations

from models.cards.action import ActionCard, ActionCardType
from models.cards.base import Card
from models.cards.money import MoneyCard
from models.cards.property import (
    CARDS_IN_SET_FOR_COLOR,
    Color,
    MultiColorProperty,
    PropertyCard,
    PropertySet,
    SingleColorProperty,
    WildColorProperty,
)
from models.cards.rent import RentCard, WildRentCard
from models.game.commands import (
    DiscardCards,
    EndTurn,
    GameCommand,
    MoveWildProperty,
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
from models.game.commands.debt_collector import DEBT_COLLECTOR_PAYMENT_M
from models.game.commands.its_my_birthday import BIRTHDAY_GIFT_M
from models.game.commands.rent import rent_m_due_for_color
from models.game.legal_moves import command_identity_key
from models.game.game import Game
from models.game.pending import (
    DealBreakerPending,
    ForcedDealPending,
    PaymentDue,
    SlyDealPending,
)
from models.player import Player

MoveBucket = str

BUCKET_ORDER: tuple[MoveBucket, ...] = (
    "complete",
    "charge",
    "draw",
    "property",
    "disrupt",
    "build",
    "bank",
    "other",
)

BUCKET_QUOTAS: dict[MoveBucket, int] = {
    "complete": 3,
    "charge": 2,
    "draw": 1,
    "property": 2,
    "disrupt": 2,
    "build": 1,
    "bank": 1,
    "other": 1,
}


def score_move(game: Game, move: GameCommand, root_player_idx: int) -> float:
    """Return a cheap, root-relative score for ranking legal commands."""
    acting_idx = game.acting_player_idx
    perspective = 1 if acting_idx == root_player_idx else -1
    actor = game.players[acting_idx]

    score = _score_move_for_actor(game, move, actor)
    return perspective * score


def select_top_moves(
    game: Game,
    moves: list[GameCommand],
    *,
    root_player_idx: int,
    max_moves: int,
    heuristic_move: GameCommand,
    strategy: str,
) -> list[GameCommand]:
    if len(moves) <= max_moves:
        return moves
    prefer_high_scores = game.acting_player_idx == root_player_idx
    if strategy == "global":
        return _select_global_top_moves(
            game,
            moves,
            root_player_idx=root_player_idx,
            max_moves=max_moves,
            heuristic_move=heuristic_move,
            prefer_high_scores=prefer_high_scores,
        )
    if strategy == "bucketed":
        return _select_bucketed_top_moves(
            game,
            moves,
            root_player_idx=root_player_idx,
            max_moves=max_moves,
            heuristic_move=heuristic_move,
            prefer_high_scores=prefer_high_scores,
        )
    raise ValueError(f"Unknown pruning strategy: {strategy}")


def select_interrupt_moves(
    game: Game,
    moves: list[GameCommand],
    *,
    root_player_idx: int,
    max_moves: int,
) -> list[GameCommand]:
    if len(moves) <= max_moves:
        return moves

    scored = _scored_moves(
        game,
        moves,
        root_player_idx,
        prefer_high_scores=game.acting_player_idx == root_player_idx,
    )
    return [move for _, _, move in scored[:max_moves]]


def _select_global_top_moves(
    game: Game,
    moves: list[GameCommand],
    *,
    root_player_idx: int,
    max_moves: int,
    heuristic_move: GameCommand,
    prefer_high_scores: bool,
) -> list[GameCommand]:
    scored = _scored_moves(
        game,
        moves,
        root_player_idx,
        prefer_high_scores=prefer_high_scores,
    )
    selected = [move for _, _, move in scored[:max_moves]]
    return _ensure_included(selected, heuristic_move)


def _select_bucketed_top_moves(
    game: Game,
    moves: list[GameCommand],
    *,
    root_player_idx: int,
    max_moves: int,
    heuristic_move: GameCommand,
    prefer_high_scores: bool,
) -> list[GameCommand]:
    scored = _scored_moves(
        game,
        moves,
        root_player_idx,
        prefer_high_scores=prefer_high_scores,
    )
    by_bucket: dict[MoveBucket, list[tuple[float, int, GameCommand]]] = {
        bucket: [] for bucket in BUCKET_ORDER
    }
    for item in scored:
        _, _, move = item
        by_bucket.setdefault(move_bucket(game, move), []).append(item)

    selected: list[GameCommand] = []
    selected_keys: set[object] = set()

    for bucket in BUCKET_ORDER:
        quota = BUCKET_QUOTAS[bucket]
        for _, _, move in by_bucket.get(bucket, [])[:quota]:
            if len(selected) >= max_moves:
                break
            _append_unique(selected, selected_keys, move)
        if len(selected) >= max_moves:
            break

    for _, _, move in scored:
        if len(selected) >= max_moves:
            break
        _append_unique(selected, selected_keys, move)

    return _ensure_included(selected, heuristic_move)


def _scored_moves(
    game: Game,
    moves: list[GameCommand],
    root_player_idx: int,
    *,
    prefer_high_scores: bool,
) -> list[tuple[float, int, GameCommand]]:
    scored = [
        (score_move(game, move, root_player_idx), idx, move)
        for idx, move in enumerate(moves)
    ]
    if prefer_high_scores:
        scored.sort(reverse=True, key=lambda item: (item[0], -item[1]))
    else:
        scored.sort(key=lambda item: (item[0], item[1]))
    return scored


def _append_unique(
    selected: list[GameCommand],
    selected_keys: set[object],
    move: GameCommand,
) -> None:
    key = command_identity_key(move)
    if key in selected_keys:
        return
    selected.append(move)
    selected_keys.add(key)


def _ensure_included(
    selected: list[GameCommand],
    move: GameCommand,
) -> list[GameCommand]:
    move_key = command_identity_key(move)
    if any(command_identity_key(existing) == move_key for existing in selected):
        return selected
    if not selected:
        return [move]
    selected[-1] = move
    return selected


def move_bucket(game: Game, move: GameCommand) -> MoveBucket:
    if _completes_set(game, move) or isinstance(move, PlayDealBreaker):
        return "complete"
    if isinstance(
        move,
        (PlayRent, PlayDoubleRent, PlayDebtCollector, PlayItsMyBirthday),
    ):
        return "charge"
    if isinstance(move, PlayPassGo):
        return "draw"
    if isinstance(move, (PlayPropertyFromHand, MoveWildProperty)):
        return "property"
    if isinstance(move, (PlaySlyDeal, PlayForcedDeal)):
        return "disrupt"
    if isinstance(move, (PlayHouse, PlayHotel)):
        return "build"
    if isinstance(move, PlayMoneyFromHand):
        return "bank"
    return "other"


def _score_move_for_actor(game: Game, move: GameCommand, actor: Player) -> float:
    if isinstance(move, PlayDealBreaker):
        victim = game.players[move.victim_idx]
        return 240 + _pile_score(victim.pile_at(move.victim_set_idx))

    if isinstance(move, PlaySlyDeal):
        victim = game.players[move.target_player_idx]
        card = victim.pile_at(move.target_set_idx).cards[move.target_card_idx]
        return 75 + _property_progress_gain(actor, card, move.into_color)

    if isinstance(move, PlayForcedDeal):
        target = game.players[move.target_player_idx]
        my_card = actor.pile_at(move.my_set_idx).cards[move.my_card_idx]
        their_card = target.pile_at(move.their_set_idx).cards[move.their_card_idx]
        gain = _property_progress_gain(actor, their_card, move.take_into_color)
        loss = _property_progress_gain(
            actor, my_card, actor.pile_at(move.my_set_idx).color
        )
        return 45 + gain - loss

    if isinstance(move, PlayPropertyFromHand):
        card = actor.hand[move.hand_index]
        if isinstance(card, PropertyCard):
            return 55 + _property_progress_gain(actor, card, move.into_color)

    if isinstance(move, MoveWildProperty):
        card = actor.pile_at(move.from_set_idx).cards[move.card_idx]
        source = actor.pile_at(move.from_set_idx)
        if isinstance(card, PropertyCard):
            gain = _property_progress_gain(actor, card, move.into_color)
            penalty = 45 if source.is_complete() else 8
            return 50 + gain - penalty

    if isinstance(move, PlayDoubleRent):
        amount = rent_m_due_for_color(actor, move.charged_color) * 2
        return 70 + _collectible_amount(game, move.victim_idx, amount) * 12

    if isinstance(move, PlayRent):
        amount = rent_m_due_for_color(actor, move.charged_color)
        return 60 + _collectible_amount(game, move.victim_idx, amount) * 12

    if isinstance(move, PlayDebtCollector):
        return (
            58
            + _collectible_amount(
                game,
                move.target_player_idx,
                DEBT_COLLECTOR_PAYMENT_M,
            )
            * 10
        )

    if isinstance(move, PlayItsMyBirthday):
        opponents = [
            i for i in range(len(game.players)) if game.players[i] is not actor
        ]
        collectible = sum(
            _collectible_amount(game, idx, BIRTHDAY_GIFT_M) for idx in opponents
        )
        return 52 + collectible * 10

    if isinstance(move, PlayPassGo):
        return 38

    if isinstance(move, PlayHouse):
        return 35 + _pile_score(actor.pile_at(move.target_set_idx)) * 0.1

    if isinstance(move, PlayHotel):
        return 40 + _pile_score(actor.pile_at(move.target_set_idx)) * 0.1

    if isinstance(move, PlayMoneyFromHand):
        card = actor.hand[move.hand_index]
        return _money_play_score(card)

    if isinstance(move, PlayJustSayNo):
        card = actor.hand[move.hand_index]
        return _interrupt_value(game) - _discard_cost(card)

    if isinstance(move, PassJustSayNo):
        return -_interrupt_value(game) * 0.5

    if isinstance(move, PayDebt):
        return -_payment_cost(game, actor, move)

    if isinstance(move, DiscardCards):
        return -sum(_discard_cost(actor.hand[index]) for index in move.hand_indices)

    if isinstance(move, EndTurn):
        return 0

    return 1


def _completes_set(game: Game, move: GameCommand) -> bool:
    actor = game.players[game.acting_player_idx]
    if isinstance(move, PlayPropertyFromHand):
        return _cards_needed_for_color(actor, move.into_color) == 1
    if isinstance(move, MoveWildProperty):
        source = actor.pile_at(move.from_set_idx)
        return (
            not source.is_complete()
            and _cards_needed_for_color(actor, move.into_color) == 1
        )
    if isinstance(move, PlaySlyDeal):
        return _cards_needed_for_color(actor, move.into_color) == 1
    if isinstance(move, PlayForcedDeal):
        return _cards_needed_for_color(actor, move.take_into_color) == 1
    return False


def _property_progress_gain(player: Player, card: PropertyCard, color: Color) -> float:
    cards_needed_before = _cards_needed_for_color(player, color)
    score = card.value * 3
    if cards_needed_before == 1:
        score += 120
    elif cards_needed_before == 2:
        score += 45
    else:
        score += 15

    if isinstance(card, WildColorProperty):
        score += 12
    elif isinstance(card, MultiColorProperty):
        score += 7
    elif isinstance(card, SingleColorProperty):
        score += 4
    return score


def _cards_needed_for_color(player: Player, color: Color) -> int:
    for pile in player.property_sets:
        if pile.color == color:
            return CARDS_IN_SET_FOR_COLOR[color] - len(pile.cards)
    return CARDS_IN_SET_FOR_COLOR[color]


def _pile_score(pile: PropertySet) -> float:
    score = sum(card.value for card in pile.cards) * 4 + len(pile.cards) * 12
    if pile.is_complete():
        score += 120
    elif _cards_needed(pile) == 1:
        score += 45
    if pile.has_house():
        score += 15
    if pile.has_hotel():
        score += 20
    return score


def _collectible_amount(game: Game, player_idx: int, amount: int) -> int:
    assets = game.players[player_idx].asset_count()
    if assets == 0:
        return 0
    total_value = sum(card.value for card in game.players[player_idx].money_pile)
    for pile in game.players[player_idx].property_sets:
        total_value += sum(card.value for card in pile.cards)
    return min(amount, total_value)


def _interrupt_value(game: Game) -> float:
    pending = game.pending
    if isinstance(pending, PaymentDue):
        collectible = _collectible_amount(
            game,
            pending.debtor_idx,
            pending.amount_m,
        )
        return 10 + collectible * 18

    if isinstance(pending, SlyDealPending):
        victim = game.players[pending.steal.victim_idx]
        card = victim.pile_at(pending.steal.target_set_idx).cards[
            pending.steal.target_card_idx
        ]
        actor = game.players[pending.actor_idx]
        return 75 + _property_progress_gain(actor, card, pending.steal.into_color)

    if isinstance(pending, ForcedDealPending):
        actor = game.players[pending.actor_idx]
        target = game.players[pending.swap.target_player_idx]
        my_card = actor.pile_at(pending.swap.my_set_idx).cards[pending.swap.my_card_idx]
        their_card = target.pile_at(pending.swap.their_set_idx).cards[
            pending.swap.their_card_idx
        ]
        gain = _property_progress_gain(actor, their_card, pending.swap.take_into_color)
        loss = _property_progress_gain(
            actor,
            my_card,
            actor.pile_at(pending.swap.my_set_idx).color,
        )
        return 45 + max(gain - loss, 0)

    if isinstance(pending, DealBreakerPending):
        victim = game.players[pending.theft.victim_idx]
        return 240 + _pile_score(victim.pile_at(pending.theft.victim_set_idx))

    return 0


def _money_play_score(card: Card) -> float:
    if isinstance(card, MoneyCard):
        return 24 + card.value * 2
    if isinstance(card, RentCard):
        return 10 + card.value
    if isinstance(card, WildRentCard):
        return 8 + card.value
    if isinstance(card, ActionCard):
        if card.action_type in (
            ActionCardType.JUST_SAY_NO,
            ActionCardType.DEAL_BREAKER,
        ):
            return -40
        return 6 + card.value
    return 0


def _payment_cost(game: Game, player: Player, move: PayDebt) -> float:
    cost = _money_payment_cost(player, move)
    for set_idx, card_idx in move._selected_property_indices():
        cost += _property_payment_cost(game, player, set_idx, card_idx)

    due = game.pending
    if isinstance(due, PaymentDue):
        overpay = max(0, _payment_value(player, move) - due.amount_m)
        cost += overpay * 5
    return cost


def _payment_value(player: Player, move: PayDebt) -> int:
    total = 0
    for index in move._selected_money_indices():
        total += player.money_pile[index].value
    for set_idx, card_idx in move._selected_property_indices():
        total += player.pile_at(set_idx).cards[card_idx].value
    return total


def _money_payment_cost(player: Player, move: PayDebt) -> float:
    selected_value = sum(
        player.money_pile[index].value for index in move._selected_money_indices()
    )
    bank_before = sum(card.value for card in player.money_pile)
    bank_after = bank_before - selected_value
    return selected_value * 3.5 + _bank_defense_loss(bank_before, bank_after)


def _bank_defense_loss(bank_before: int, bank_after: int) -> float:
    loss = 0.0
    for threshold, penalty in ((2, 8), (3, 8), (5, 12), (8, 10)):
        if bank_before >= threshold > bank_after:
            loss += penalty
    return loss


def _property_payment_cost(
    game: Game,
    player: Player,
    set_idx: int,
    card_idx: int,
) -> float:
    pile = player.pile_at(set_idx)
    card = pile.cards[card_idx]
    cost = 24 + card.value * 4
    cost += _set_damage_cost(player, pile)
    cost += rent_m_due_for_color(player, pile.color) * 7
    cost += _property_flex_cost(card)
    cost += _creditor_property_gain_cost(game, card, pile.color)
    return cost


def _set_damage_cost(player: Player, pile: PropertySet) -> float:
    cards_needed = _cards_needed(pile)
    if pile.is_complete():
        cost = 185
        if player.complete_set_count() >= 2:
            cost += 55
    elif cards_needed == 1:
        cost = 90
    elif cards_needed == 2:
        cost = 35
    else:
        cost = 16

    if len(pile.cards) == 1:
        cost += 18
    if pile.has_house():
        cost += 35
    if pile.has_hotel():
        cost += 45
    return cost


def _property_flex_cost(card: PropertyCard) -> float:
    if isinstance(card, WildColorProperty):
        return 45
    if isinstance(card, MultiColorProperty):
        return 22
    if isinstance(card, SingleColorProperty):
        return 5
    return 0


def _creditor_property_gain_cost(
    game: Game,
    card: PropertyCard,
    color: Color,
) -> float:
    pending = game.pending
    if not isinstance(pending, PaymentDue):
        return 0

    creditor = game.players[pending.creditor_idx]
    gain = _property_progress_gain(creditor, card, color) * 0.65
    if _cards_needed_for_color(creditor, color) == 1:
        gain += 65
        if creditor.complete_set_count() >= 2:
            gain += 90
    return gain


def _discard_cost(card: Card) -> float:
    if isinstance(card, MoneyCard):
        return card.value
    if isinstance(card, WildColorProperty):
        return 40
    if isinstance(card, PropertyCard):
        return 30 + card.value
    if isinstance(card, WildRentCard):
        return 15
    if isinstance(card, RentCard):
        return 10
    if isinstance(card, ActionCard):
        return {
            ActionCardType.DEAL_BREAKER: 50,
            ActionCardType.JUST_SAY_NO: 45,
            ActionCardType.PASS_GO: 25,
        }.get(card.action_type, 15 + card.value)
    return card.value


def _cards_needed(pile: PropertySet) -> int:
    return CARDS_IN_SET_FOR_COLOR[pile.color] - len(pile.cards)
