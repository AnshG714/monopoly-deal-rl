import type { Card, GameStateResponse, LegalMove } from "@/api/types";

export const MOVE_KINDS = {
  PlayMoneyFromHand: "PlayMoneyFromHand",
  PlayPropertyFromHand: "PlayPropertyFromHand",
  PlayPassGo: "PlayPassGo",
  PlayHouse: "PlayHouse",
  PlayHotel: "PlayHotel",
  PlayDebtCollector: "PlayDebtCollector",
  PlayItsMyBirthday: "PlayItsMyBirthday",
  PlaySlyDeal: "PlaySlyDeal",
  PlayForcedDeal: "PlayForcedDeal",
  PlayDealBreaker: "PlayDealBreaker",
  PlayRent: "PlayRent",
  PlayDoubleRent: "PlayDoubleRent",
  PlayJustSayNo: "PlayJustSayNo",
  EndTurn: "EndTurn",
  DiscardCards: "DiscardCards",
} as const;

export type MoveKind = (typeof MOVE_KINDS)[keyof typeof MOVE_KINDS];

function paramsMatch(
  moveParams: Record<string, unknown>,
  partial: Record<string, unknown>,
): boolean {
  return Object.entries(partial).every(
    ([key, value]) => moveParams[key] === value,
  );
}

export function findMoves(
  legalMoves: LegalMove[],
  kind: string,
  params?: Record<string, unknown>,
): LegalMove[] {
  return legalMoves.filter(
    (move) =>
      move.kind === kind &&
      (params === undefined || paramsMatch(move.params, params)),
  );
}

export function findMove(
  legalMoves: LegalMove[],
  kind: string,
  params?: Record<string, unknown>,
): LegalMove | undefined {
  return findMoves(legalMoves, kind, params)[0];
}

export function findPlayMoneyMove(
  legalMoves: LegalMove[],
  handIndex: number,
): LegalMove | undefined {
  return findMove(legalMoves, MOVE_KINDS.PlayMoneyFromHand, {
    hand_index: handIndex,
  });
}

export function canPlayAsMoney(
  legalMoves: LegalMove[],
  handIndex: number,
): boolean {
  return findPlayMoneyMove(legalMoves, handIndex) !== undefined;
}

export function canViewerAct(game: GameStateResponse): boolean {
  return (
    !game.is_over && game.acting_player_idx === game.viewer
  );
}

export function isPropertyCard(card: Card): boolean {
  return card.type === "property" || Boolean(card.property_kind);
}

export function findPlayPropertyMoves(
  legalMoves: LegalMove[],
  handIndex: number,
): LegalMove[] {
  return findMoves(legalMoves, MOVE_KINDS.PlayPropertyFromHand, {
    hand_index: handIndex,
  });
}

export function findPlayPropertyMove(
  legalMoves: LegalMove[],
  handIndex: number,
  intoColor: string,
): LegalMove | undefined {
  return findMove(legalMoves, MOVE_KINDS.PlayPropertyFromHand, {
    hand_index: handIndex,
    into_color: intoColor,
  });
}

export function canPlayProperty(
  legalMoves: LegalMove[],
  handIndex: number,
): boolean {
  return findPlayPropertyMoves(legalMoves, handIndex).length > 0;
}

const ACTION_PILE_MOVE_KINDS = new Set<string>([
  MOVE_KINDS.PlayPassGo,
  MOVE_KINDS.PlayHouse,
  MOVE_KINDS.PlayHotel,
  MOVE_KINDS.PlayDebtCollector,
  MOVE_KINDS.PlayItsMyBirthday,
  MOVE_KINDS.PlaySlyDeal,
  MOVE_KINDS.PlayForcedDeal,
  MOVE_KINDS.PlayDealBreaker,
  MOVE_KINDS.PlayRent,
  MOVE_KINDS.PlayDoubleRent,
  MOVE_KINDS.PlayJustSayNo,
]);

function actionMoveUsesHandIndex(
  move: LegalMove,
  handIndex: number,
): boolean {
  return (
    move.params.hand_index === handIndex ||
    move.params.rent_hand_index === handIndex ||
    move.params.double_rent_hand_index === handIndex
  );
}

export function findActionPileMoves(
  legalMoves: LegalMove[],
  handIndex: number,
): LegalMove[] {
  return legalMoves.filter(
    (move) =>
      ACTION_PILE_MOVE_KINDS.has(move.kind) &&
      actionMoveUsesHandIndex(move, handIndex),
  );
}

export function findAutoActionPileMove(
  legalMoves: LegalMove[],
  handIndex: number,
): LegalMove | undefined {
  const moves = findActionPileMoves(legalMoves, handIndex);
  return moves.length === 1 ? moves[0] : undefined;
}

export function canAutoPlayActionPileMove(
  legalMoves: LegalMove[],
  handIndex: number,
): boolean {
  return findAutoActionPileMove(legalMoves, handIndex) !== undefined;
}

export function canPlayActionPileMove(
  legalMoves: LegalMove[],
  handIndex: number,
): boolean {
  return findActionPileMoves(legalMoves, handIndex).length > 0;
}

export function validPropertyColors(
  legalMoves: LegalMove[],
  handIndex: number,
): string[] {
  const colors = findPlayPropertyMoves(legalMoves, handIndex).map(
    (move) => move.params.into_color as string,
  );
  return [...new Set(colors)];
}

export function findEndTurnMove(
  legalMoves: LegalMove[],
): LegalMove | undefined {
  return findMove(legalMoves, MOVE_KINDS.EndTurn);
}

export function canEndTurn(legalMoves: LegalMove[]): boolean {
  return findEndTurnMove(legalMoves) !== undefined;
}
