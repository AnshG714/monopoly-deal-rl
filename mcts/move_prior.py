"""Move priors for MCTS candidate pruning and expansion ordering.

Neural priors (``PolicyMovePrior``) live in ``policy_net.prior`` so ``mcts``
does not depend on the ML stack.
"""

from __future__ import annotations

from typing import Protocol

from mcts.consts import DEFAULT_PRUNING_STRATEGY
from mcts.move_scoring import score_move, select_top_moves
from models.game.commands import GameCommand
from models.game.game import Game


class MovePrior(Protocol):
    """Ranks legal moves for pruning (select_candidates) and expansion (score)."""

    def score(
        self, game: Game, move: GameCommand, root_player_idx: int
    ) -> float: ...

    def select_candidates(
        self,
        game: Game,
        moves: list[GameCommand],
        *,
        root_player_idx: int,
        max_moves: int,
        heuristic_move: GameCommand,
    ) -> list[GameCommand]: ...


class HeuristicMovePrior:
    """Handcrafted ``score_move`` prior with global/bucketed candidate selection."""

    def __init__(self, strategy: str = DEFAULT_PRUNING_STRATEGY):
        if strategy not in ("global", "bucketed"):
            raise ValueError("pruning strategy must be 'global' or 'bucketed'")
        self.strategy = strategy

    def score(self, game: Game, move: GameCommand, root_player_idx: int) -> float:
        return score_move(game, move, root_player_idx)

    def select_candidates(
        self,
        game: Game,
        moves: list[GameCommand],
        *,
        root_player_idx: int,
        max_moves: int,
        heuristic_move: GameCommand,
    ) -> list[GameCommand]:
        return select_top_moves(
            game,
            moves,
            root_player_idx=root_player_idx,
            max_moves=max_moves,
            heuristic_move=heuristic_move,
            strategy=self.strategy,
        )
