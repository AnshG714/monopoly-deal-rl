"""Static board evaluator for depth-limited MCTS rollouts."""

from __future__ import annotations

import math

from models.cards.action import ActionCard, ActionCardType
from models.cards.property import (
    CARDS_IN_SET_FOR_COLOR,
    MultiColorProperty,
    PropertyCard,
    PropertySet,
    WildColorProperty,
)
from models.cards.rent import RentCard, WildRentCard
from models.game.commands.rent import rent_m_due_for_color
from models.game.game import Game
from models.player import Player


def evaluate_reward(game: Game, player_idx: int) -> float:
    """Return a 0..1 estimate of ``player_idx`` winning from this state."""
    winner = game.winner_idx()
    if winner is not None:
        return 1.0 if winner == player_idx else 0.0

    opponent_idx = 1 - player_idx
    diff = _player_score(game, player_idx) - _player_score(game, opponent_idx)
    return _sigmoid(diff / 50)


def _sigmoid(x: float) -> float:
    return 1 / (1 + math.exp(-x))


def _player_score(game: Game, player_idx: int) -> float:
    player = game.players[player_idx]
    opponent = game.players[1 - player_idx]

    score = 0.0
    score += _board_score(player)
    score += _bank_score(player)
    score += _hand_score(game, player_idx)
    score += _attack_score(game, player_idx)
    score -= _threat_score(opponent)
    return score


def _board_score(player: Player) -> float:
    score = 0.0
    for pile in player.property_sets:
        cards_needed = _cards_needed(pile)
        card_count = len(pile.cards)
        score += card_count * 7
        score += sum(card.value for card in pile.cards) * 2

        if cards_needed == 0:
            score += 120
        elif cards_needed == 1:
            score += 45
        elif cards_needed == 2:
            score += 18

        if pile.has_house():
            score += 14
        if pile.has_hotel():
            score += 18

        for card in pile.cards:
            if isinstance(card, WildColorProperty):
                score += 10
            elif isinstance(card, MultiColorProperty):
                score += 6
    return score


def _bank_score(player: Player) -> float:
    bank_value = sum(card.value for card in player.money_pile)
    # Money is useful defense, but hoarding past common debt sizes is less decisive.
    return min(bank_value, 12) * 4 + max(bank_value - 12, 0) * 1.5


def _hand_score(game: Game, player_idx: int) -> float:
    player = game.players[player_idx]
    score = 0.0
    for card in player.hand:
        if isinstance(card, PropertyCard):
            score += 9 + card.value
            if isinstance(card, WildColorProperty):
                score += 8
            elif isinstance(card, MultiColorProperty):
                score += 4
        elif isinstance(card, WildRentCard):
            score += 7
        elif isinstance(card, RentCard):
            score += 4
        elif isinstance(card, ActionCard):
            score += _action_hand_score(card)
        else:
            score += card.value
    return score


def _action_hand_score(card: ActionCard) -> float:
    match card.action_type:
        case ActionCardType.DEAL_BREAKER:
            return 25
        case ActionCardType.JUST_SAY_NO:
            return 20
        case ActionCardType.PASS_GO:
            return 12
        case ActionCardType.SLY_DEAL:
            return 11
        case ActionCardType.FORCED_DEAL:
            return 9
        case ActionCardType.DEBT_COLLECTOR:
            return 8
        case ActionCardType.ITS_MY_BIRTHDAY:
            return 7
        case ActionCardType.HOUSE:
            return 6
        case ActionCardType.HOTEL:
            return 6
        case ActionCardType.DOUBLE_RENT:
            return 4


def _attack_score(game: Game, player_idx: int) -> float:
    player = game.players[player_idx]
    opponent = game.players[1 - player_idx]
    opponent_assets = min(opponent.asset_count(), 8)
    best_rent = 0
    for pile in player.property_sets:
        best_rent = max(best_rent, rent_m_due_for_color(player, pile.color))
    return best_rent * min(opponent_assets, 4)


def _threat_score(opponent: Player) -> float:
    score = opponent.complete_set_count() * 90
    for pile in opponent.property_sets:
        if _cards_needed(pile) == 1:
            score += 30
    return score


def _cards_needed(pile: PropertySet) -> int:
    return CARDS_IN_SET_FOR_COLOR[pile.color] - len(pile.cards)
