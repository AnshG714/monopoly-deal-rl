export type DealActionKind = "sly_deal" | "forced_deal" | "deal_breaker";

export function dealActionKind(
  actionType: string | undefined,
): DealActionKind | null {
  if (
    actionType === "sly_deal" ||
    actionType === "forced_deal" ||
    actionType === "deal_breaker"
  ) {
    return actionType;
  }
  return null;
}
