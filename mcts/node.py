from __future__ import annotations

import math

from models.game.commands import GameCommand
from mcts.consts import C_UCT


def _keys_for_moves(moves: list[GameCommand]) -> set[GameCommand]:
    return set(moves)


class ISMCTSNode:
    def __init__(
        self, move: GameCommand | None = None, parent: ISMCTSNode | None = None
    ):
        # The move that led to this node. Roots don't have this set.
        self.move = move
        self.parent = parent
        self.children: list[ISMCTSNode] = []
        self.wins = 0.0
        self.visits = 0

        # For tracking how many times each move was an option inside a determinization.
        self.availability_counts: dict[GameCommand, int] = {}

    def get_legal_children(self, legal_moves: list[GameCommand]) -> list[ISMCTSNode]:
        legal_keys = _keys_for_moves(legal_moves)
        return [
            child
            for child in self.children
            if child.move is not None and child.move in legal_keys
        ]

    def get_unexpanded_moves(self, legal_moves: list[GameCommand]) -> list[GameCommand]:
        expanded_keys = {
            child.move for child in self.children if child.move is not None
        }
        return [move for move in legal_moves if move not in expanded_keys]

    def choose_child_uct(
        self,
        legal_moves: list[GameCommand],
        *,
        maximize: bool = True,
    ) -> ISMCTSNode | None:
        legal_children = self.get_legal_children(legal_moves)
        best_score = -math.inf
        best_child = None

        for child in legal_children:
            assert child.move is not None
            move = child.move
            self.availability_counts[move] = self.availability_counts.get(move, 0) + 1

            if child.visits == 0:
                # If the child has never been visited, it is unexplored and should be chosen.
                return child

            move_availability = self.availability_counts[move]

            win_rate = child.wins / child.visits
            exploitation = win_rate if maximize else 1 - win_rate

            # Compute the UCT score for the child.
            uct_score = exploitation + C_UCT * math.sqrt(
                math.log(move_availability) / child.visits
            )

            if uct_score > best_score:
                best_score = uct_score
                best_child = child

        return best_child

    def best_child(self) -> ISMCTSNode:
        return max(self.children, key=lambda child: child.visits)

    def normalized_visits(self) -> dict[GameCommand, float]:
        total_visits = sum(child.visits for child in self.children)
        return {
            child.move: child.visits / total_visits
            for child in self.children
            if child.move is not None
        }

    def backpropagate(self, result: float) -> None:
        self.visits += 1
        self.wins += result

        if self.parent is not None:
            self.parent.backpropagate(result)
