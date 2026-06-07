import { useCallback, useMemo, useReducer } from "react";

import { applyMove, createGame } from "@/api/client";
import type { CreateGameOptions, GameStateResponse, LegalMove } from "@/api/types";
import type { DealActionKind } from "@/lib/dealActions";
import { selectPendingPrompt } from "@/lib/pendingPrompt";
import { getMockScenario, isMockGame, resolveMockMove } from "@/mocks";

export interface MovePickerState {
  handIndex: number;
  moves: LegalMove[];
}

export type GameOverlay =
  | { kind: "none" }
  | ({ kind: "wild-picker" } & MovePickerState)
  | ({ kind: "action-picker" } & MovePickerState)
  | ({ kind: "deal-action"; dealKind: DealActionKind } & MovePickerState);

interface GameUiState {
  game: GameStateResponse | null;
  loading: boolean;
  error: string | null;
  draggedHandIndex: number | null;
  overlay: GameOverlay;
  dismissedPromptId: string | null;
}

type GameUiEvent =
  | { type: "game/request-started" }
  | { type: "game/received"; game: GameStateResponse }
  | { type: "game/request-failed"; error: string }
  | { type: "game/ended" }
  | { type: "drag/started"; handIndex: number }
  | { type: "drag/ended" }
  | { type: "overlay/opened"; overlay: GameOverlay }
  | { type: "overlay/closed" }
  | { type: "prompt/dismissed"; promptId: string }
  | { type: "prompt/reopened" };

const NO_OVERLAY: GameOverlay = { kind: "none" };

const INITIAL_STATE: GameUiState = {
  game: null,
  loading: false,
  error: null,
  draggedHandIndex: null,
  overlay: NO_OVERLAY,
  dismissedPromptId: null,
};

function errorMessage(err: unknown, fallback: string): string {
  return err instanceof Error ? err.message : fallback;
}

function gameUiReducer(state: GameUiState, event: GameUiEvent): GameUiState {
  switch (event.type) {
    case "game/request-started":
      return { ...state, loading: true, error: null };

    case "game/received": {
      const previousPrompt = selectPendingPrompt(state.game);
      const nextPrompt = selectPendingPrompt(event.game);
      const keepDismissed =
        nextPrompt !== null &&
        previousPrompt?.id === nextPrompt.id &&
        state.dismissedPromptId === nextPrompt.id;

      return {
        ...state,
        game: event.game,
        loading: false,
        error: null,
        draggedHandIndex: null,
        overlay: NO_OVERLAY,
        dismissedPromptId: keepDismissed ? state.dismissedPromptId : null,
      };
    }

    case "game/request-failed":
      return { ...state, loading: false, error: event.error };

    case "game/ended":
      return INITIAL_STATE;

    case "drag/started":
      return { ...state, draggedHandIndex: event.handIndex };

    case "drag/ended":
      return { ...state, draggedHandIndex: null };

    case "overlay/opened":
      return { ...state, draggedHandIndex: null, overlay: event.overlay };

    case "overlay/closed":
      return { ...state, overlay: NO_OVERLAY };

    case "prompt/dismissed":
      return { ...state, dismissedPromptId: event.promptId };

    case "prompt/reopened":
      return { ...state, dismissedPromptId: null };
  }
}

export function useGame() {
  const [state, dispatch] = useReducer(gameUiReducer, INITIAL_STATE);

  const pendingPrompt = useMemo(
    () => selectPendingPrompt(state.game),
    [state.game],
  );
  const pendingPromptOpen =
    pendingPrompt !== null && state.dismissedPromptId !== pendingPrompt.id;

  const startGame = useCallback(async (options: CreateGameOptions = {}) => {
    dispatch({ type: "game/request-started" });
    try {
      const response = await createGame(options);
      dispatch({ type: "game/received", game: response });
    } catch (err) {
      dispatch({
        type: "game/request-failed",
        error: errorMessage(err, "Failed to start game"),
      });
    }
  }, []);

  const playMove = useCallback(
    async (moveId: number) => {
      const currentGame = state.game;
      if (!currentGame) return;

      dispatch({ type: "game/request-started" });
      try {
        const response = isMockGame(currentGame)
          ? resolveMockMove(currentGame, moveId)
          : await applyMove(currentGame.game_id, moveId);
        dispatch({ type: "game/received", game: response });
      } catch (err) {
        dispatch({
          type: "game/request-failed",
          error: errorMessage(err, "Move failed"),
        });
      }
    },
    [state.game],
  );

  const loadMockScenario = useCallback((scenarioId: string) => {
    dispatch({ type: "game/request-started" });
    try {
      dispatch({
        type: "game/received",
        game: getMockScenario(scenarioId),
      });
    } catch (err) {
      dispatch({
        type: "game/request-failed",
        error: errorMessage(err, "Failed to load mock"),
      });
    }
  }, []);

  const endGame = useCallback(() => {
    dispatch({ type: "game/ended" });
  }, []);

  const startDrag = useCallback((handIndex: number) => {
    dispatch({ type: "drag/started", handIndex });
  }, []);

  const endDrag = useCallback(() => {
    dispatch({ type: "drag/ended" });
  }, []);

  const openOverlay = useCallback((overlay: GameOverlay) => {
    dispatch({ type: "overlay/opened", overlay });
  }, []);

  const closeOverlay = useCallback(() => {
    dispatch({ type: "overlay/closed" });
  }, []);

  const dismissPrompt = useCallback((promptId: string) => {
    dispatch({ type: "prompt/dismissed", promptId });
  }, []);

  const reopenPrompt = useCallback(() => {
    dispatch({ type: "prompt/reopened" });
  }, []);

  return {
    ...state,
    pendingPrompt,
    pendingPromptOpen,
    isMock: isMockGame(state.game),
    startGame,
    endGame,
    playMove,
    loadMockScenario,
    startDrag,
    endDrag,
    openOverlay,
    closeOverlay,
    dismissPrompt,
    reopenPrompt,
  };
}
