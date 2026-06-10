import { useMemo } from "react";

import type { GameStateResponse } from "@/api/types";
import {
  canDiscard,
  findDiscardMove,
  findDiscardMoves,
  requiredDiscardCount,
} from "@/lib/discardCards";
import {
  canEndTurn,
  canMoveWild,
  canPlayAsMoney,
  canPlayProperty,
  canViewerAct,
  canAutoPlayActionPileMove,
  canPlayActionPileMove,
  findActionPileMoves,
  findAutoActionPileMove,
  findEndTurnMove,
  findMove,
  findMoves,
  findPlayMoneyMove,
  findMoveWildMoves,
  findPlayPropertyMove,
  findPlayPropertyMoves,
  validPropertyColors,
} from "@/lib/legalMoves";

export function useLegalMoves(game: GameStateResponse | null) {
  const legalMoves = game?.legal_moves ?? [];
  const canAct = game ? canViewerAct(game) : false;

  return useMemo(
    () => ({
      legalMoves,
      canAct,
      canPlayAsMoney: (handIndex: number) =>
        canAct && canPlayAsMoney(legalMoves, handIndex),
      playMoneyMove: (handIndex: number) =>
        findPlayMoneyMove(legalMoves, handIndex),
      canPlayProperty: (handIndex: number) =>
        canAct && canPlayProperty(legalMoves, handIndex),
      playPropertyMoves: (handIndex: number) =>
        findPlayPropertyMoves(legalMoves, handIndex),
      playPropertyMove: (handIndex: number, intoColor: string) =>
        findPlayPropertyMove(legalMoves, handIndex, intoColor),
      validPropertyColors: (handIndex: number) =>
        validPropertyColors(legalMoves, handIndex),
      canMoveWild: (fromSetIdx: number, cardIdx: number) =>
        canAct && canMoveWild(legalMoves, fromSetIdx, cardIdx),
      moveWildMoves: (fromSetIdx: number, cardIdx: number) =>
        findMoveWildMoves(legalMoves, fromSetIdx, cardIdx),
      canPlayAction: (handIndex: number) =>
        canAct && canPlayActionPileMove(legalMoves, handIndex),
      canAutoPlayAction: (handIndex: number) =>
        canAct && canAutoPlayActionPileMove(legalMoves, handIndex),
      actionPileMoves: (handIndex: number) =>
        findActionPileMoves(legalMoves, handIndex),
      autoActionMove: (handIndex: number) =>
        findAutoActionPileMove(legalMoves, handIndex),
      endTurnMove: () => findEndTurnMove(legalMoves),
      canEndTurn: () => canAct && canEndTurn(legalMoves),
      discardMoves: () => findDiscardMoves(legalMoves),
      canDiscard: () => canAct && canDiscard(legalMoves),
      requiredDiscardCount: () => requiredDiscardCount(legalMoves),
      findDiscardMove: (handIndices: number[]) =>
        findDiscardMove(legalMoves, handIndices),
      findMove: (kind: string, params?: Record<string, unknown>) =>
        findMove(legalMoves, kind, params),
      findMoves: (kind: string, params?: Record<string, unknown>) =>
        findMoves(legalMoves, kind, params),
    }),
    [canAct, legalMoves],
  );
}
