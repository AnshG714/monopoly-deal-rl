import type { Card, LegalMove, Player, PropertySet } from "@/api/types";
import { cardTitle, colorLabel } from "@/components/card/utils";

import { MOVE_KINDS } from "./legalMoves";

export interface ActionMoveDescription {
  title: string;
  subtitle?: string;
  accentColor?: string;
}

export interface ActionDialogContext {
  title: string;
  description: string;
}

export function rentDueForColor(
  propertySets: PropertySet[],
  color: string,
): number {
  for (const pile of propertySets) {
    if (pile.color !== color || pile.cards.length === 0) continue;

    const count = pile.cards.length;
    let rents: number[] | undefined;

    for (const card of pile.cards) {
      if (card.color === color && card.rents) {
        rents = card.rents;
        break;
      }
      if (card.color1 === color && card.color1_rents) {
        rents = card.color1_rents;
        break;
      }
      if (card.color2 === color && card.color2_rents) {
        rents = card.color2_rents;
        break;
      }
    }

    if (!rents) return 0;

    const index = Math.min(count, rents.length) - 1;
    let total = rents[index] ?? 0;
    if (pile.has_house) total += 3;
    if (pile.has_hotel) total += 4;
    return total;
  }

  return 0;
}

function playerAt(players: Player[], idx: number): Player | undefined {
  return players.find((player) => player.idx === idx);
}

function playerName(players: Player[], idx: number): string {
  return playerAt(players, idx)?.name ?? "Opponent";
}

function propertyCard(
  player: Player | undefined,
  setIdx: number,
  cardIdx: number,
): Card | undefined {
  return player?.property_sets[setIdx]?.cards[cardIdx];
}

function propertyPile(
  player: Player | undefined,
  setIdx: number,
): PropertySet | undefined {
  return player?.property_sets[setIdx];
}

export function actionDialogContext(moves: LegalMove[]): ActionDialogContext {
  const kind = moves[0]?.kind;
  switch (kind) {
    case MOVE_KINDS.PlaySlyDeal:
      return {
        title: "Sly Deal",
        description: "Pick a property to steal from your opponent.",
      };
    case MOVE_KINDS.PlayForcedDeal:
      return {
        title: "Forced Deal",
        description: "Pick which properties to swap.",
      };
    case MOVE_KINDS.PlayDealBreaker:
      return {
        title: "Deal Breaker",
        description: "Pick a complete set to steal.",
      };
    case MOVE_KINDS.PlayRent:
    case MOVE_KINDS.PlayDoubleRent:
      return {
        title: "Charge rent",
        description: "Pick which color to charge for.",
      };
    case MOVE_KINDS.PlayDebtCollector:
      return {
        title: "Debt Collector",
        description: "Pick who must pay you $5M.",
      };
    case MOVE_KINDS.PlayHouse:
      return {
        title: "House",
        description: "Pick a complete set to add a house to.",
      };
    case MOVE_KINDS.PlayHotel:
      return {
        title: "Hotel",
        description: "Pick a set with a house to upgrade.",
      };
    default:
      return {
        title: "Choose how to play",
        description: "Pick one of the legal plays below.",
      };
  }
}

export function actionMoveDescription(
  move: LegalMove,
  players: Player[],
  actorPropertySets: PropertySet[],
): ActionMoveDescription {
  const targetPlayerIdx = move.params.target_player_idx as number | undefined;
  const victimIdx = (move.params.victim_idx ?? targetPlayerIdx) as
    | number
    | undefined;
  const chargedColor = move.params.charged_color as string | undefined;

  if (move.kind === MOVE_KINDS.PlayRent && chargedColor) {
    const amount = rentDueForColor(actorPropertySets, chargedColor);
    const victimName =
      victimIdx === undefined ? undefined : playerName(players, victimIdx);
    return {
      title: `${colorLabel(chargedColor)} · $${amount}M`,
      subtitle: victimName ? `Charge ${victimName}` : undefined,
      accentColor: chargedColor,
    };
  }

  if (move.kind === MOVE_KINDS.PlayDoubleRent && chargedColor) {
    const amount = rentDueForColor(actorPropertySets, chargedColor) * 2;
    const victimName =
      victimIdx === undefined ? undefined : playerName(players, victimIdx);
    return {
      title: `${colorLabel(chargedColor)} · $${amount}M (doubled)`,
      subtitle: victimName ? `Charge ${victimName}` : undefined,
      accentColor: chargedColor,
    };
  }

  if (move.kind === MOVE_KINDS.PlaySlyDeal && targetPlayerIdx !== undefined) {
    const setIdx = move.params.target_set_idx as number;
    const cardIdx = move.params.target_card_idx as number;
    const intoColor = move.params.into_color as string;
    const victim = playerAt(players, targetPlayerIdx);
    const pile = propertyPile(victim, setIdx);
    const card = propertyCard(victim, setIdx, cardIdx);
    const victimName = playerName(players, targetPlayerIdx);

    return {
      title: card ? `Steal ${cardTitle(card)}` : `Steal from ${victimName}`,
      subtitle: pile
        ? `${victimName}'s ${colorLabel(pile.color)} → your ${colorLabel(intoColor)}`
        : `Add to your ${colorLabel(intoColor)} set`,
      accentColor: pile?.color ?? intoColor,
    };
  }

  if (move.kind === MOVE_KINDS.PlayForcedDeal && targetPlayerIdx !== undefined) {
    const mySetIdx = move.params.my_set_idx as number;
    const myCardIdx = move.params.my_card_idx as number;
    const theirSetIdx = move.params.their_set_idx as number;
    const theirCardIdx = move.params.their_card_idx as number;
    const takeIntoColor = move.params.take_into_color as string | undefined;
    const giveIntoColor = move.params.give_into_color as string | undefined;
    const target = playerAt(players, targetPlayerIdx);
    const myPile = actorPropertySets[mySetIdx];
    const theirPile = propertyPile(target, theirSetIdx);
    const myCard = myPile?.cards[myCardIdx];
    const theirCard = propertyCard(target, theirSetIdx, theirCardIdx);
    const targetName = playerName(players, targetPlayerIdx);

    return {
      title:
        myCard && theirCard
          ? `Give ${cardTitle(myCard)} · Take ${cardTitle(theirCard)}`
          : `Swap with ${targetName}`,
      subtitle:
        takeIntoColor && giveIntoColor
          ? `Take into ${colorLabel(takeIntoColor)} · Give into ${targetName}'s ${colorLabel(giveIntoColor)}`
          : myPile && theirPile
            ? `Your ${colorLabel(myPile.color)} ↔ ${targetName}'s ${colorLabel(theirPile.color)}`
            : undefined,
      accentColor: takeIntoColor ?? theirPile?.color,
    };
  }

  if (move.kind === MOVE_KINDS.PlayDealBreaker && victimIdx !== undefined) {
    const setIdx = move.params.victim_set_idx as number;
    const victim = playerAt(players, victimIdx);
    const pile = propertyPile(victim, setIdx);
    const victimName = playerName(players, victimIdx);

    return {
      title: pile
        ? `Steal ${victimName}'s ${colorLabel(pile.color)} set`
        : `Steal from ${victimName}`,
      subtitle: pile ? `${pile.cards.length} cards · complete set` : undefined,
      accentColor: pile?.color,
    };
  }

  if (
    move.kind === MOVE_KINDS.PlayDebtCollector &&
    targetPlayerIdx !== undefined
  ) {
    return {
      title: `Collect $5M from ${playerName(players, targetPlayerIdx)}`,
    };
  }

  if (move.kind === MOVE_KINDS.PlayHouse || move.kind === MOVE_KINDS.PlayHotel) {
    const setIdx = move.params.target_set_idx as number;
    const pile = actorPropertySets[setIdx];
    const building = move.kind === MOVE_KINDS.PlayHouse ? "house" : "hotel";
    return {
      title: pile
        ? `Add ${building} to ${colorLabel(pile.color)}`
        : `Add ${building}`,
      subtitle: pile?.complete ? "Complete set" : undefined,
      accentColor: pile?.color,
    };
  }

  if (victimIdx !== undefined) {
    return {
      title: move.label,
      subtitle: `Target ${playerName(players, victimIdx)}`,
    };
  }

  return { title: move.label };
}
