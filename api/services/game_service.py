"""Game orchestration: human moves, automatic AI replies."""

from __future__ import annotations

import random
import secrets

from mcts.consts import DEFAULT_ITERS
from mcts.move_prior import MovePrior
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
        self._value_evaluator = None
        self._policy_prior: MovePrior | None = None

    def create_game(
        self,
        *,
        seed: int | None = None,
        human_player_idx: int = 0,
        mcts_iterations: int | None = None,
        use_value_net: bool = False,
        use_policy_net: bool = False,
    ) -> dict:
        if human_player_idx not in (0, 1):
            raise ValueError("human_player_idx must be 0 or 1")

        rng_seed = seed if seed is not None else secrets.randbelow(2**31)
        game = Game(rng=random.Random(rng_seed))
        game.start_match()

        if use_value_net:
            self._get_value_evaluator()
        if use_policy_net:
            self._get_policy_prior()

        session = GameSession(
            game_id=GameStore.new_game_id(),
            game=game,
            human_player_idx=human_player_idx,
            mcts_iterations=mcts_iterations or self._default_mcts_iterations,
            use_value_net=use_value_net,
            use_policy_net=use_policy_net,
        )
        self._store.create(session)
        if game.acting_player_idx != human_player_idx:
            self._run_ai_until_human_or_over(session)
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

    def _get_value_evaluator(self):
        if self._value_evaluator is None:
            try:
                from value_net.infer import make_value_net_evaluator

                self._value_evaluator = make_value_net_evaluator()
            except ImportError as exc:
                raise ValueError(
                    "value_net is not installed in this environment. "
                    "Reinstall with `uv sync` from the repo root."
                ) from exc
            except (FileNotFoundError, OSError) as exc:
                raise ValueError(
                    "Value net checkpoint not found. Train or place "
                    "outputs/best_value_net.pth"
                ) from exc
        return self._value_evaluator

    def _get_policy_prior(self) -> MovePrior:
        if self._policy_prior is None:
            try:
                from policy_net.prior import make_policy_move_prior

                self._policy_prior = make_policy_move_prior()
            except ImportError as exc:
                raise ValueError(
                    "policy_net is not installed in this environment. "
                    "Reinstall with `uv sync` from the repo root."
                ) from exc
            except (FileNotFoundError, OSError) as exc:
                raise ValueError(
                    "Policy net checkpoint not found. Train or place "
                    "outputs/best_policy_net.pth"
                ) from exc
        return self._policy_prior

    def _make_solver(self, session: GameSession) -> ISMCTSSolver:
        return ISMCTSSolver(
            iterations=session.mcts_iterations,
            leaf_evaluator=(
                self._get_value_evaluator() if session.use_value_net else None
            ),
            move_prior=(
                self._get_policy_prior() if session.use_policy_net else None
            ),
        )

    def _run_ai_until_human_or_over(self, session: GameSession) -> None:
        game = session.game
        ai_idx = 1 - session.human_player_idx
        solver = self._make_solver(session)

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
            "use_value_net": session.use_value_net,
            "use_policy_net": session.use_policy_net,
        }
        if seed is not None:
            payload["seed"] = seed
        return payload
