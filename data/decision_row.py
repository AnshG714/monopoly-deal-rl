from __future__ import annotations

from dataclasses import dataclass

from models.cards.base import Card
from models.cards.property import PropertySet
from models.game.commands import EndTurn, GameCommand
from models.game.game import Game
from models.game.pending import Pending
from models.player import BankableCard


@dataclass(frozen=True)
class DecisionRow:
    seed: int
    step: int
    viewer_idx: int
    chosen_move: GameCommand
    legal_moves: list[GameCommand]
    visits: dict[GameCommand, float]

    viewer_property_piles: list[PropertySet]
    viewer_hand: list[Card]
    viewer_bank: list[BankableCard]
    opponent_property_piles: list[PropertySet]
    opponent_bank: list[BankableCard]
    opponent_hand_size: int
    plays_this_turn: int
    pending: Pending | None

    timed_out: bool
    viewer_won: bool


def game_to_decision_row(game: Game, viewer_idx: int) -> DecisionRow:
    """Snapshot from ``viewer_idx``'s perspective (for value/policy encoding)."""
    opponent_idx = 1 - viewer_idx
    viewer = game.players[viewer_idx]
    opponent = game.players[opponent_idx]
    return DecisionRow(
        seed=0,
        step=0,
        viewer_idx=viewer_idx,
        chosen_move=EndTurn(),
        legal_moves=[],
        visits={},
        viewer_property_piles=list(viewer.property_sets),
        viewer_hand=list(viewer.hand),
        viewer_bank=list(viewer.money_pile),
        opponent_property_piles=list(opponent.property_sets),
        opponent_bank=list(opponent.money_pile),
        opponent_hand_size=len(opponent.hand),
        plays_this_turn=game.plays_this_turn,
        pending=game.pending,
        timed_out=False,
        viewer_won=False,
    )
