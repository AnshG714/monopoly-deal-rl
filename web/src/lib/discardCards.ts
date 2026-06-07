import type { LegalMove } from "@/api/types";
import { MOVE_KINDS, findMoves } from "@/lib/legalMoves";

export function findDiscardMoves(legalMoves: LegalMove[]): LegalMove[] {
  return findMoves(legalMoves, MOVE_KINDS.DiscardCards);
}

export function canDiscard(legalMoves: LegalMove[]): boolean {
  return findDiscardMoves(legalMoves).length > 0;
}

export function sortHandIndices(indices: number[]): number[] {
  return [...new Set(indices)].sort((a, b) => a - b);
}

export function requiredDiscardCount(legalMoves: LegalMove[]): number {
  const moves = findDiscardMoves(legalMoves);
  if (moves.length === 0) return 0;
  const handIndices = moves[0].params.hand_indices as number[] | undefined;
  return handIndices?.length ?? 0;
}

export function findDiscardMove(
  legalMoves: LegalMove[],
  handIndices: number[],
): LegalMove | undefined {
  const sorted = sortHandIndices(handIndices);
  return findDiscardMoves(legalMoves).find((move) => {
    const moveIndices = sortHandIndices(
      (move.params.hand_indices as number[]) ?? [],
    );
    return JSON.stringify(sorted) === JSON.stringify(moveIndices);
  });
}
