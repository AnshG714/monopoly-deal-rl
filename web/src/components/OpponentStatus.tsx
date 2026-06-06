import { Layers } from "lucide-react";

import type { Player } from "@/api/types";
import { Flex } from "@/components/ui/flex";

interface OpponentStatusProps {
  player: Player;
}

export function OpponentStatus({ player }: OpponentStatusProps) {
  return (
    <Flex align="center" gap="sm" className="text-sm font-medium">
      <span>{player.name}</span>
      <Flex
        align="center"
        gap="xs"
        className="text-muted-foreground"
        title={`${player.hand.size} cards in hand`}
      >
        <Layers className="size-4" aria-hidden />
        <span>{player.hand.size}</span>
      </Flex>
    </Flex>
  );
}
