import type {
  Card,
  GameStateResponse,
  LegalMove,
  PropertySet,
} from "@/api/types";

export interface PaymentDuePending {
  kind: "PaymentDue";
  creditor_idx: number;
  debtor_idx: number;
  amount_m: number;
}

export function viewerMustPayDebt(
  game: GameStateResponse,
): PaymentDuePending | null {
  const pending = game.state.pending;
  if (!pending || pending.kind !== "PaymentDue") return null;
  if (game.is_over) return null;
  if (game.acting_player_idx !== game.viewer) return null;
  if (pending.debtor_idx !== game.viewer) return null;
  return {
    kind: "PaymentDue",
    creditor_idx: pending.creditor_idx as number,
    debtor_idx: pending.debtor_idx as number,
    amount_m: pending.amount_m as number,
  };
}

export function sortMoneyIndices(indices: number[]): number[] {
  return [...new Set(indices)].sort((a, b) => a - b);
}

export function sortPropertyIndices(
  indices: [number, number][],
): [number, number][] {
  const unique = new Map<string, [number, number]>();
  for (const [setIdx, cardIdx] of indices) {
    unique.set(`${setIdx},${cardIdx}`, [setIdx, cardIdx]);
  }
  return [...unique.values()].sort((a, b) => b[0] - a[0] || b[1] - a[1]);
}

export function totalPropertyCards(propertySets: PropertySet[]): number {
  return propertySets.reduce((count, pile) => count + pile.cards.length, 0);
}

export function paymentSelectionTotal(
  moneyIndices: number[],
  propertyIndices: [number, number][],
  bank: Card[],
  propertySets: PropertySet[],
): number {
  let total = 0;
  for (const index of sortMoneyIndices(moneyIndices)) {
    total += bank[index]?.value ?? 0;
  }
  for (const [setIdx, cardIdx] of sortPropertyIndices(propertyIndices)) {
    total += propertySets[setIdx]?.cards[cardIdx]?.value ?? 0;
  }
  return total;
}

export function isValidPaymentSelection(
  moneyIndices: number[],
  propertyIndices: [number, number][],
  bank: Card[],
  propertySets: PropertySet[],
  amountOwed: number,
): boolean {
  const assetCount = bank.length + totalPropertyCards(propertySets);
  if (assetCount === 0) return true;

  if (moneyIndices.length === 0 && propertyIndices.length === 0) {
    return false;
  }

  const total = paymentSelectionTotal(
    moneyIndices,
    propertyIndices,
    bank,
    propertySets,
  );
  const allSelected =
    sortMoneyIndices(moneyIndices).length === bank.length &&
    sortPropertyIndices(propertyIndices).length ===
      totalPropertyCards(propertySets);

  return total >= amountOwed || allSelected;
}

function payDebtParamsMatch(
  move: LegalMove,
  moneyIndices: number[],
  propertyIndices: [number, number][],
): boolean {
  const money = sortMoneyIndices(moneyIndices);
  const properties = sortPropertyIndices(propertyIndices);
  const moveMoney = sortMoneyIndices(
    (move.params.money_pile_indices as number[] | undefined) ?? [],
  );
  const moveProperties = sortPropertyIndices(
    ((move.params.property_card_indices as number[][] | undefined) ?? []).map(
      ([setIdx, cardIdx]) => [setIdx, cardIdx] as [number, number],
    ),
  );

  return (
    JSON.stringify(money) === JSON.stringify(moveMoney) &&
    JSON.stringify(properties) === JSON.stringify(moveProperties)
  );
}

export function findPayDebtMove(
  legalMoves: LegalMove[],
  moneyIndices: number[],
  propertyIndices: [number, number][],
): LegalMove | undefined {
  return legalMoves
    .filter((move) => move.kind === "PayDebt")
    .find((move) => payDebtParamsMatch(move, moneyIndices, propertyIndices));
}
