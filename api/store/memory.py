"""In-memory game session storage."""

from __future__ import annotations

import secrets
from dataclasses import dataclass

from models.game.game import Game


@dataclass
class GameSession:
    game_id: str
    game: Game
    human_player_idx: int
    mcts_iterations: int


class GameStore:
    def __init__(self) -> None:
        self._sessions: dict[str, GameSession] = {}

    def create(self, session: GameSession) -> GameSession:
        self._sessions[session.game_id] = session
        return session

    def get(self, game_id: str) -> GameSession | None:
        return self._sessions.get(game_id)

    @staticmethod
    def new_game_id() -> str:
        return secrets.token_urlsafe(12)


default_store = GameStore()
