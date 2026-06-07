import type { LegalMove, PropertySet } from "@/api/types";
import { cardTitle } from "@/components/card/utils";

import { MOVE_KINDS } from "./legalMoves";

export interface PropertyRef {
  setIdx: number;
  cardIdx: number;
}

function refKey(setIdx: number, cardIdx: number): string {
  return `${setIdx}:${cardIdx}`;
}

function uniqueRefs(refs: PropertyRef[]): PropertyRef[] {
  const seen = new Set<string>();
  return refs.filter((ref) => {
    const key = refKey(ref.setIdx, ref.cardIdx);
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

export function opponentIdxFromMoves(moves: LegalMove[]): number | undefined {
  const first = moves[0];
  if (!first) return undefined;
  return (first.params.target_player_idx ?? first.params.victim_idx) as
    | number
    | undefined;
}

export function slyDealTargetCards(moves: LegalMove[]): PropertyRef[] {
  return uniqueRefs(
    moves
      .filter((move) => move.kind === MOVE_KINDS.PlaySlyDeal)
      .map((move) => ({
        setIdx: move.params.target_set_idx as number,
        cardIdx: move.params.target_card_idx as number,
      })),
  );
}

export function slyDealIntoColors(
  moves: LegalMove[],
  setIdx: number,
  cardIdx: number,
): string[] {
  const colors = moves
    .filter(
      (move) =>
        move.kind === MOVE_KINDS.PlaySlyDeal &&
        move.params.target_set_idx === setIdx &&
        move.params.target_card_idx === cardIdx,
    )
    .map((move) => move.params.into_color as string);
  return [...new Set(colors)];
}

export function findSlyDealMove(
  moves: LegalMove[],
  setIdx: number,
  cardIdx: number,
  intoColor: string,
): LegalMove | undefined {
  return moves.find(
    (move) =>
      move.kind === MOVE_KINDS.PlaySlyDeal &&
      move.params.target_set_idx === setIdx &&
      move.params.target_card_idx === cardIdx &&
      move.params.into_color === intoColor,
  );
}

export function forcedDealMyCards(moves: LegalMove[]): PropertyRef[] {
  return uniqueRefs(
    moves
      .filter((move) => move.kind === MOVE_KINDS.PlayForcedDeal)
      .map((move) => ({
        setIdx: move.params.my_set_idx as number,
        cardIdx: move.params.my_card_idx as number,
      })),
  );
}

export function forcedDealTheirCards(
  moves: LegalMove[],
  mySetIdx: number,
  myCardIdx: number,
): PropertyRef[] {
  return uniqueRefs(
    moves
      .filter(
        (move) =>
          move.kind === MOVE_KINDS.PlayForcedDeal &&
          move.params.my_set_idx === mySetIdx &&
          move.params.my_card_idx === myCardIdx,
      )
      .map((move) => ({
        setIdx: move.params.their_set_idx as number,
        cardIdx: move.params.their_card_idx as number,
      })),
  );
}

export function findForcedDealMove(
  moves: LegalMove[],
  my: PropertyRef,
  their: PropertyRef,
): LegalMove | undefined {
  return moves.find(
    (move) =>
      move.kind === MOVE_KINDS.PlayForcedDeal &&
      move.params.my_set_idx === my.setIdx &&
      move.params.my_card_idx === my.cardIdx &&
      move.params.their_set_idx === their.setIdx &&
      move.params.their_card_idx === their.cardIdx,
  );
}

export function dealBreakerTargetSets(moves: LegalMove[]): number[] {
  const sets = moves
    .filter((move) => move.kind === MOVE_KINDS.PlayDealBreaker)
    .map((move) => move.params.victim_set_idx as number);
  return [...new Set(sets)];
}

export function findDealBreakerMove(
  moves: LegalMove[],
  victimSetIdx: number,
): LegalMove | undefined {
  return moves.find(
    (move) =>
      move.kind === MOVE_KINDS.PlayDealBreaker &&
      move.params.victim_set_idx === victimSetIdx,
  );
}

export function isSelectableTarget(
  refs: PropertyRef[],
  setIdx: number,
  cardIdx: number,
): boolean {
  return refs.some(
    (ref) => ref.setIdx === setIdx && ref.cardIdx === cardIdx,
  );
}

export function propertyRefLabel(
  propertySets: PropertySet[],
  ref: PropertyRef,
): string {
  const card = propertySets[ref.setIdx]?.cards[ref.cardIdx];
  return card ? cardTitle(card) : "property";
}
