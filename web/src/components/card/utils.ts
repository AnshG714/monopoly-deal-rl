import type { Card } from "@/api/types";

import { COLOR_MAP } from "./colors";
import {
  ACTION_ACCENTS,
  ACTION_CARD_PAPER,
  ACTION_THEMES,
  DEFAULT_CARD_PAPER,
  DEFAULT_CARD_SYMBOL,
  MONEY_ACCENTS,
  RAINBOW_COLORS,
} from "./constants";

export type VisualKind =
  | "money"
  | "action"
  | "rent"
  | "property-single"
  | "property-multi"
  | "property-wild"
  | string;

export function cardTitle(card: Card): string {
  if (card.display_name) return card.display_name;
  if (card.action_type) return card.action_type.replaceAll("_", " ");
  if (card.property_kind === "single" && card.name) return card.name;
  if (card.property_kind === "multi") return `${card.color1} / ${card.color2}`;
  if (card.property_kind === "wild") return "Wild property";
  if (card.type === "rent") return `Rent ${card.color1 ?? ""}`;
  if (card.type === "wild_rent") return "Wild rent";
  if (card.type === "money") return `$${card.value}M`;
  return card.type;
}

export function colorLabel(color: string): string {
  if (color === "blue" || color === "dark_blue") return "Dark Blue";
  return color
    .replaceAll("_", " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

export function valueText(card: Card): string {
  return `$${card.value}M`;
}

export function visualKind(card: Card): VisualKind {
  if (card.type === "money") return "money";
  if (card.action_type) return "action";
  if (card.type === "rent") return "rent";
  if (card.property_kind) return `property-${card.property_kind}`;
  return card.type;
}

export function cardThemeVars(card: Card): Record<string, string> {
  const accent = cardAccent(card);
  const secondaryAccent = cardSecondaryAccent(card);
  const actionTheme = card.action_type
    ? ACTION_THEMES[card.action_type]
    : undefined;

  const vars: Record<string, string> = {
    "--card-accent": accent ?? "#94a3b8",
    "--card-accent-2": secondaryAccent,
    "--card-paper":
      card.action_type && actionTheme
        ? actionTheme.paper
        : card.action_type
          ? ACTION_CARD_PAPER
          : DEFAULT_CARD_PAPER,
    "--card-symbol": actionTheme?.symbol ?? DEFAULT_CARD_SYMBOL,
  };

  return vars;
}

export function cardAccent(card: Card): string | undefined {
  if (card.color) return COLOR_MAP[card.color] ?? card.color;
  if (card.color1) return COLOR_MAP[card.color1] ?? card.color1;
  if (card.action_type) return ACTION_ACCENTS[card.action_type] ?? "#c4b5fd";
  if (card.property_kind === "wild") return COLOR_MAP.multicolor;
  if (card.type === "money") return MONEY_ACCENTS[card.value]?.[0] ?? "#d6b356";
  if (card.type === "rent") return "#d6b356";
  return undefined;
}

export function cardSecondaryAccent(card: Card): string {
  if (card.type === "money") return MONEY_ACCENTS[card.value]?.[1] ?? "#9a741a";
  if (card.color2) return COLOR_MAP[card.color2] ?? card.color2;
  return cardAccent(card) ?? "#94a3b8";
}

export function colorBandColors(card: Card): string[] {
  if (card.property_kind === "wild") {
    return RAINBOW_COLORS.map((color) => COLOR_MAP[color]);
  }
  if (card.color1 && card.color2) {
    return [card.color1, card.color2].map((color) => COLOR_MAP[color] ?? color);
  }
  if (card.color) return [COLOR_MAP[card.color] ?? card.color];
  return [cardAccent(card) ?? "#d6b356"];
}

export function cardTypeLabel(card: Card): string {
  if (card.type === "money") return "Money Card";
  if (card.action_type) return "Action Card";
  if (card.type === "rent") return "Rent Card";
  if (card.property_kind === "wild") return "Property Wild Card";
  if (card.property_kind === "multi") return "Property Wild Card";
  if (card.property_kind === "single") return "Property Card";
  return card.type.replaceAll("_", " ");
}

export function cornerKind(kind: VisualKind): "money" | "action" | "default" {
  if (kind === "money") return "money";
  if (kind === "action") return "action";
  return "default";
}

export function shellKind(
  kind: VisualKind,
):
  | "money"
  | "action"
  | "rent"
  | "property-single"
  | "property-multi"
  | "property-wild"
  | "default" {
  if (
    kind === "money" ||
    kind === "action" ||
    kind === "rent" ||
    kind === "property-single" ||
    kind === "property-multi" ||
    kind === "property-wild"
  ) {
    return kind;
  }
  return "default";
}
