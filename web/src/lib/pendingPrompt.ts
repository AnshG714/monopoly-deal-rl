import type { GameStateResponse } from "@/api/types";
import type { JustSayNoInterrupt } from "@/lib/interrupts";
import { viewerJustSayNoInterrupt } from "@/lib/interrupts";
import type { PaymentDuePending } from "@/lib/payDebt";
import { viewerMustPayDebt } from "@/lib/payDebt";

export type PendingPrompt =
  | {
      kind: "jsn";
      id: string;
      label: string;
      interrupt: JustSayNoInterrupt;
    }
  | {
      kind: "payment";
      id: string;
      label: string;
      payment: PaymentDuePending;
    };

function promptInstanceId(game: GameStateResponse, promptKey: string): string {
  return [
    game.game_id,
    promptKey,
    game.state.current_player_idx,
    game.state.acting_player_idx,
    game.state.plays_this_turn,
    game.state.discard_size,
  ].join(":");
}

export function selectPendingPrompt(
  game: GameStateResponse | null,
): PendingPrompt | null {
  if (!game) return null;

  const interrupt = viewerJustSayNoInterrupt(game, game.legal_moves);
  if (interrupt) {
    return {
      kind: "jsn",
      id: promptInstanceId(game, interrupt.key),
      label: `Respond: ${interrupt.title}`,
      interrupt,
    };
  }

  const payment = viewerMustPayDebt(game);
  if (payment) {
    const key = `PaymentDue:${payment.creditor_idx}:${payment.debtor_idx}:${payment.amount_m}`;
    return {
      kind: "payment",
      id: promptInstanceId(game, key),
      label: `Pay $${payment.amount_m}M`,
      payment,
    };
  }

  return null;
}
