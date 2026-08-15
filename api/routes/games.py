from __future__ import annotations

from fastapi import APIRouter, HTTPException

from models.cards.registry import build_full_deck
from serialization.cards import serialize_card

from ..schemas import (
    ApplyMoveRequest,
    CreateGameRequest,
    DeckResponse,
    GameStateResponse,
)
from ..services.game_service import (
    GameNotFoundError,
    GameService,
    InvalidMoveError,
    NotHumanTurnError,
)

router = APIRouter(tags=["games"])
game_service = GameService()


@router.get("/api/deck", response_model=DeckResponse)
def get_deck() -> DeckResponse:
    cards = [serialize_card(card) for card in build_full_deck()]
    return DeckResponse(total=len(cards), cards=cards)


@router.post("/api/games", response_model=GameStateResponse)
def create_game(body: CreateGameRequest | None = None) -> GameStateResponse:
    request = body or CreateGameRequest()
    try:
        payload = game_service.create_game(
            seed=request.seed,
            human_player_idx=request.human_player_idx,
            mcts_iterations=request.mcts_iterations,
            use_value_net=request.use_value_net,
            use_policy_net=request.use_policy_net,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return GameStateResponse(**payload)


@router.get("/api/games/{game_id}", response_model=GameStateResponse)
def get_game(game_id: str) -> GameStateResponse:
    try:
        payload = game_service.get_game(game_id)
    except GameNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return GameStateResponse(**payload)


@router.post("/api/games/{game_id}/moves", response_model=GameStateResponse)
def apply_move(game_id: str, body: ApplyMoveRequest) -> GameStateResponse:
    try:
        payload = game_service.apply_human_move(game_id, body.move_id)
    except GameNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except NotHumanTurnError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except InvalidMoveError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return GameStateResponse(**payload)
