import type { Card } from "@/api/types";

/** Stable identity for one card design in the full deck (ignores duplicate copies). */
export function cardIdentity(card: Card): string {
  if (card.type === "money") return `money:${card.value}`;
  if (card.action_type) return `action:${card.action_type}`;
  if (card.type === "rent") return `rent:${card.color1}:${card.color2}`;
  if (card.type === "wild_rent") return "wild_rent";
  if (card.property_kind === "single")
    return `single:${card.color}:${card.name}`;
  if (card.property_kind === "multi")
    return `multi:${card.color1}:${card.color2}`;
  if (card.property_kind === "wild") return "wild_property";
  return `${card.type}:${card.display_name ?? card.name ?? "unknown"}`;
}

export function groupLabel(card: Card): string {
  if (card.property_kind === "single") return "Properties";
  if (card.property_kind === "multi" || card.property_kind === "wild") {
    return "Property Wilds";
  }
  if (card.type === "rent" || card.type === "wild_rent") return "Rent Cards";
  if (card.type === "money") return "Money";
  if (card.action_type) return "Actions";
  return "Other";
}

const GROUP_ORDER = [
  "Properties",
  "Property Wilds",
  "Actions",
  "Rent Cards",
  "Money",
  "Other",
];

export interface DeckGroup {
  label: string;
  cards: Card[];
}

export function uniqueCardsByGroup(cards: Card[]): DeckGroup[] {
  const seen = new Set<string>();
  const groups = new Map<string, Card[]>();

  for (const card of cards) {
    const key = cardIdentity(card);
    if (seen.has(key)) continue;
    seen.add(key);

    const label = groupLabel(card);
    const bucket = groups.get(label) ?? [];
    bucket.push(card);
    groups.set(label, bucket);
  }

  return GROUP_ORDER.filter((label) => groups.has(label)).map((label) => ({
    label,
    cards: groups.get(label) ?? [],
  }));
}
