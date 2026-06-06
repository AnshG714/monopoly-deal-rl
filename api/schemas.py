from __future__ import annotations

from pydantic import BaseModel, Field


class CreateGameRequest(BaseModel):
    seed: int | None = None
    human_player_idx: int = 0
    mcts_iterations: int | None = Field(
        default=None,
        ge=1,
        description="ISMCTS iterations per AI decision (default: 500)",
    )


class ApplyMoveRequest(BaseModel):
    move_id: int = Field(ge=0)


class GameStateResponse(BaseModel):
    game_id: str
    viewer: int
    acting_player_idx: int
    current_player_idx: int
    is_over: bool
    winner_idx: int | None
    state: dict
    legal_moves: list[dict]
    seed: int | None = None


class DeckResponse(BaseModel):
    total: int
    cards: list[dict]
