from __future__ import annotations

from dataclasses import dataclass
from models.cards.base import Card
from models.cards.property import PropertySet
from models.game.commands import GameCommand
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
