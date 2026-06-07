import type { Card, HandCard } from "@/api/types";

export function money(value: number): Card {
  return { type: "money", value, display_name: `$${value}M` };
}

export function justSayNo(): Card {
  return {
    type: "action",
    value: 4,
    display_name: "Just Say No",
    action_type: "just_say_no",
  };
}

export function slyDeal(): Card {
  return {
    type: "action",
    value: 3,
    display_name: "Sly Deal",
    action_type: "sly_deal",
  };
}

export function forcedDeal(): Card {
  return {
    type: "action",
    value: 3,
    display_name: "Forced Deal",
    action_type: "forced_deal",
  };
}

export function dealBreaker(): Card {
  return {
    type: "action",
    value: 5,
    display_name: "Deal Breaker",
    action_type: "deal_breaker",
  };
}

export function wildProperty(): Card {
  return {
    type: "property",
    value: 2,
    display_name: "Property Wild",
    property_kind: "wild",
  };
}

export function property(
  name: string,
  color: string,
  value: number,
  rents: number[],
): Card {
  return {
    type: "property",
    value,
    display_name: name,
    property_kind: "single",
    color,
    name,
    rents,
  };
}

export function handCard(card: Card, index: number): HandCard {
  return { ...card, index };
}
