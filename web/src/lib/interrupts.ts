import type {
  Card,
  GameStateResponse,
  LegalMove,
  PendingState,
  Player,
  PropertySet,
} from "@/api/types";

import { findMove, findMoves } from "./legalMoves";

export const INTERRUPT_MOVE_KINDS = {
  PassJustSayNo: "PassJustSayNo",
  PlayJustSayNo: "PlayJustSayNo",
} as const;

export interface JustSayNoInterrupt {
  key: string;
  title: string;
  description: string;
  allowLabel: string;
  actorName: string;
  targetCard?: Card;
  targetColor?: string;
  targetSet?: PropertySet;
  swapOfferCard?: Card;
  swapOfferColor?: string;
  stolenSet?: PropertySet;
}

function playerName(players: Player[], idx: number): string {
  return players.find((player) => player.idx === idx)?.name ?? "Player";
}

function canViewerAct(game: GameStateResponse): boolean {
  return !game.is_over && game.acting_player_idx === game.viewer;
}

export function findPassJustSayNoMove(
  legalMoves: LegalMove[],
): LegalMove | undefined {
  return findMove(legalMoves, INTERRUPT_MOVE_KINDS.PassJustSayNo);
}

export function findPlayJustSayNoMoves(
  legalMoves: LegalMove[],
): LegalMove[] {
  return findMoves(legalMoves, INTERRUPT_MOVE_KINDS.PlayJustSayNo);
}

export function findPlayJustSayNoMove(
  legalMoves: LegalMove[],
  handIndex: number,
): LegalMove | undefined {
  return findMove(legalMoves, INTERRUPT_MOVE_KINDS.PlayJustSayNo, {
    hand_index: handIndex,
  });
}

function stealInterrupt(
  game: GameStateResponse,
  pending: PendingState,
  kind: string,
): JustSayNoInterrupt | null {
  const players = game.state.players;
  const viewerIdx = game.viewer;
  const actorIdx = pending.actor_idx as number;
  const actorName = playerName(players, actorIdx);
  const viewerIsActor = viewerIdx === actorIdx;

  if (kind === "SlyDealPending") {
    const victimIdx = pending.victim_idx as number;
    const victimName = playerName(players, victimIdx);
    const setIdx = pending.target_set_idx as number;
    const cardIdx = pending.target_card_idx as number;
    const intoColor = pending.into_color as string;
    const pile = players.find((player) => player.idx === victimIdx)
      ?.property_sets[setIdx];
    const targetCard = pile?.cards[cardIdx];

    return {
      key: `${kind}:${actorIdx}:${setIdx}:${cardIdx}`,
      title: "Sly Deal",
      description: viewerIsActor
        ? `${victimName} played Just Say No on your Sly Deal. Counter or let the steal happen.`
        : `${actorName} is trying to steal a property from you.`,
      allowLabel: viewerIsActor ? "Cancel steal" : "Allow steal",
      actorName: viewerIsActor ? victimName : actorName,
      targetCard,
      targetColor: intoColor,
      targetSet: pile,
    };
  }

  if (kind === "ForcedDealPending") {
    const targetPlayerIdx = pending.target_player_idx as number;
    const targetName = playerName(players, targetPlayerIdx);
    const theirSetIdx = pending.their_set_idx as number;
    const theirCardIdx = pending.their_card_idx as number;
    const mySetIdx = pending.my_set_idx as number;
    const myCardIdx = pending.my_card_idx as number;
    const takeIntoColor = pending.take_into_color as string | undefined;
    const giveIntoColor = pending.give_into_color as string | undefined;
    const actor = players.find((player) => player.idx === actorIdx);
    const victim = players.find((player) => player.idx === targetPlayerIdx);
    const theirPile = victim?.property_sets[theirSetIdx];
    const myPile = actor?.property_sets[mySetIdx];
    const viewerIsTarget = viewerIdx === targetPlayerIdx;

    return {
      key: `${kind}:${actorIdx}:${theirSetIdx}:${theirCardIdx}:${mySetIdx}:${myCardIdx}`,
      title: "Forced Deal",
      description: viewerIsActor
        ? `${targetName} played Just Say No on your Forced Deal. Counter or let the swap happen.`
        : `${actorName} wants to swap one of your properties for one of theirs.`,
      allowLabel: viewerIsActor ? "Cancel swap" : "Allow swap",
      actorName: viewerIsActor ? targetName : actorName,
      targetCard: theirPile?.cards[theirCardIdx],
      targetSet: theirPile,
      targetColor: takeIntoColor ?? theirPile?.color,
      swapOfferCard: myPile?.cards[myCardIdx],
      swapOfferColor: giveIntoColor ?? myPile?.color,
      ...(viewerIsTarget
        ? {}
        : {
            targetCard: myPile?.cards[myCardIdx],
            targetSet: myPile,
            targetColor: giveIntoColor ?? myPile?.color,
            swapOfferCard: theirPile?.cards[theirCardIdx],
            swapOfferColor: takeIntoColor ?? theirPile?.color,
          }),
    };
  }

  if (kind === "DealBreakerPending") {
    const victimIdx = pending.victim_idx as number;
    const victimName = playerName(players, victimIdx);
    const setIdx = pending.victim_set_idx as number;
    const pile = players.find((player) => player.idx === victimIdx)
      ?.property_sets[setIdx];

    return {
      key: `${kind}:${actorIdx}:${setIdx}`,
      title: "Deal Breaker",
      description: viewerIsActor
        ? `${victimName} played Just Say No on your Deal Breaker. Counter or let the theft happen.`
        : `${actorName} is trying to steal your complete property set.`,
      allowLabel: viewerIsActor ? "Cancel theft" : "Allow theft",
      actorName: viewerIsActor ? victimName : actorName,
      stolenSet: pile,
      targetColor: pile?.color,
    };
  }

  return null;
}

function paymentJsnInterrupt(
  game: GameStateResponse,
  pending: PendingState,
): JustSayNoInterrupt | null {
  const players = game.state.players;
  const creditorIdx = pending.creditor_idx as number;
  const debtorIdx = pending.debtor_idx as number;
  const amount = pending.amount_m as number;
  const jsn = pending.jsn as
    | {
        defender_idx: number;
        actor_idx: number;
        responder: "defender" | "actor";
      }
    | undefined;

  if (!jsn) return null;

  const creditorName = playerName(players, creditorIdx);
  const debtorName = playerName(players, debtorIdx);
  const viewerIsCreditor = game.viewer === creditorIdx;
  const viewerIsDebtor = game.viewer === debtorIdx;

  if (viewerIsCreditor && jsn.responder === "actor") {
    return {
      key: `PaymentDue:jsn:${creditorIdx}:${debtorIdx}:${amount}`,
      title: "Just Say No",
      description: `${debtorName} played Just Say No on a $${amount}M payment. Counter or let it stand.`,
      allowLabel: "Accept (cancel payment)",
      actorName: debtorName,
    };
  }

  if (viewerIsDebtor && jsn.responder === "defender") {
    return {
      key: `PaymentDue:jsn:${creditorIdx}:${debtorIdx}:${amount}`,
      title: "Just Say No",
      description: `${creditorName} countered your Just Say No. Counter again or pay $${amount}M.`,
      allowLabel: "Stop chaining (pay now)",
      actorName: creditorName,
    };
  }

  return null;
}

export function viewerJustSayNoInterrupt(
  game: GameStateResponse,
  legalMoves: LegalMove[],
): JustSayNoInterrupt | null {
  if (!canViewerAct(game)) return null;

  const hasPass = findPassJustSayNoMove(legalMoves) !== undefined;
  const hasJsn = findPlayJustSayNoMoves(legalMoves).length > 0;
  if (!hasPass && !hasJsn) return null;

  const pending = game.state.pending;
  if (!pending) return null;

  if (
    pending.kind === "SlyDealPending" ||
    pending.kind === "ForcedDealPending" ||
    pending.kind === "DealBreakerPending"
  ) {
    return stealInterrupt(game, pending, pending.kind);
  }

  if (pending.kind === "PaymentDue") {
    return paymentJsnInterrupt(game, pending);
  }

  return null;
}
