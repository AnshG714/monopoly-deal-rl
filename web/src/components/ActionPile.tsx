import { Layers } from "lucide-react";
import { useState } from "react";

import type { Card as CardData } from "@/api/types";
import { Card } from "@/components/card";
import {
  CARD_DESIGN_HEIGHT_REM,
  CARD_DESIGN_WIDTH_REM,
  CARD_SIZES,
} from "@/components/card/constants";
import { cn, Flex } from "@/components/ui";

interface ActionPileProps {
  discardSize: number;
  topCard?: CardData | null;
  className?: string;
  acceptsDrop?: boolean;
  onDrop?: () => void;
}

const PILE_SIZE = "md" as const;

export function ActionPile({
  discardSize,
  topCard = null,
  className,
  acceptsDrop = false,
  onDrop,
}: ActionPileProps) {
  const [dragOver, setDragOver] = useState(false);
  const interactive = Boolean(onDrop);
  const dropReady = interactive && acceptsDrop;
  const highlighted = dropReady && dragOver;

  return (
    <Flex
      direction="column"
      align="center"
      justify="center"
      gap="xs"
      className={cn(
        "relative shrink-0 overflow-hidden rounded-[14px] border-2 text-[var(--text-muted)] shadow-sm transition-colors duration-150",
        dropReady && "monopoly-drop-aura",
        highlighted
          ? "border-[rgba(74,202,0,0.95)] bg-[rgba(74,202,0,0.08)]"
          : "border-[var(--color-border)] bg-white/70",
        className,
      )}
      style={{
        width: CARD_SIZES[PILE_SIZE],
        aspectRatio: `${CARD_DESIGN_WIDTH_REM} / ${CARD_DESIGN_HEIGHT_REM}`,
      }}
      onDragEnter={
        interactive
          ? (event) => {
              event.preventDefault();
              event.stopPropagation();
              if (acceptsDrop) setDragOver(true);
            }
          : undefined
      }
      onDragOver={
        interactive
          ? (event) => {
              event.preventDefault();
              event.stopPropagation();
              event.dataTransfer.dropEffect = acceptsDrop ? "move" : "none";
              if (acceptsDrop) setDragOver(true);
            }
          : undefined
      }
      onDragLeave={interactive ? () => setDragOver(false) : undefined}
      onDrop={
        interactive
          ? (event) => {
              event.preventDefault();
              event.stopPropagation();
              setDragOver(false);
              if (acceptsDrop) onDrop?.();
            }
          : undefined
      }
    >
      {topCard ? (
        <>
          <Card
            card={topCard}
            width="6.25rem"
            className="pointer-events-none"
          />
          <span className="sr-only">Action pile, {discardSize} discarded</span>
        </>
      ) : (
        <>
          <div className="absolute inset-2 rounded-[10px] border border-dashed border-[var(--color-border)]" />
          <span className="relative text-[0.65rem] font-semibold uppercase tracking-wide">
            Action pile
          </span>
          <Layers className="relative size-6" aria-hidden />
          <span className="relative text-sm font-semibold text-[var(--color-text)]">
            {discardSize}
          </span>
          <span className="relative text-[0.7rem]">discarded</span>
        </>
      )}
    </Flex>
  );
}
