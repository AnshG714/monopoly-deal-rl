"""Game orchestration: human moves, automatic AI replies."""

from __future__ import annotations

import random
import secrets

from mcts.consts import DEFAULT_ITERS
from mcts.solver import ISMCTSSolver
from models.game.game import Game
from serialization.moves import encode_moves
from serialization.state import view_for_player

from ..store.memory import GameSession, GameStore, default_store


class GameNotFoundError(LookupError):
    pass


class NotHumanTurnError(RuntimeError):
    pass


class InvalidMoveError(ValueError):
    pass


class GameService:
    def __init__(
        self,
        store: GameStore | None = None,
        *,
        default_mcts_iterations: int = DEFAULT_ITERS,
    ) -> None:
        self._store = store or default_store
        self._default_mcts_iterations = default_mcts_iterations

    def create_game(
        self,
        *,
        seed: int | None = None,
        human_player_idx: int = 0,
        mcts_iterations: int | None = None,
    ) -> dict:
        if human_player_idx not in (0, 1):
            raise ValueError("human_player_idx must be 0 or 1")

        rng_seed = seed if seed is not None else secrets.randbelow(2**31)
        game = Game(rng=random.Random(rng_seed))
        game.start_match()

        session = GameSession(
            game_id=GameStore.new_game_id(),
            game=game,
            human_player_idx=human_player_idx,
            mcts_iterations=mcts_iterations or self._default_mcts_iterations,
        )
        self._store.create(session)
        return self._build_response(session, seed=rng_seed)

    def get_game(self, game_id: str) -> dict:
        session = self._require_session(game_id)
        return self._build_response(session)

    def apply_human_move(self, game_id: str, move_id: int) -> dict:
        session = self._require_session(game_id)
        game = session.game

        if game.is_over():
            raise InvalidMoveError("Game is already over")

        if game.acting_player_idx != session.human_player_idx:
            raise NotHumanTurnError("It is not the human player's turn")

        moves = game.legal_moves()
        if move_id < 0 or move_id >= len(moves):
            raise InvalidMoveError(
                f"move_id {move_id} out of range for {len(moves)} legal moves"
            )

        game.apply(moves[move_id])
        self._run_ai_until_human_or_over(session)
        return self._build_response(session)

    def _require_session(self, game_id: str) -> GameSession:
        session = self._store.get(game_id)
        if session is None:
            raise GameNotFoundError(f"Unknown game_id: {game_id}")
        return session

    def _run_ai_until_human_or_over(self, session: GameSession) -> None:
        game = session.game
        ai_idx = 1 - session.human_player_idx
        solver = ISMCTSSolver(iterations=session.mcts_iterations)

        while not game.is_over() and game.acting_player_idx == ai_idx:
            result = solver.search(game)
            move = result.move
            game.apply(move)

    def _build_response(self, session: GameSession, *, seed: int | None = None) -> dict:
        game = session.game
        viewer = session.human_player_idx
        legal_moves: list[dict] = []

        if not game.is_over() and game.acting_player_idx == viewer:
            legal_moves = encode_moves(game, game.legal_moves())

        payload = {
            "game_id": session.game_id,
            "viewer": viewer,
            "acting_player_idx": game.acting_player_idx,
            "current_player_idx": game.current_player_idx,
            "is_over": game.is_over(),
            "winner_idx": game.winner_idx(),
            "state": view_for_player(game, viewer),
            "legal_moves": legal_moves,
        }
        if seed is not None:
            payload["seed"] = seed
        return payload
