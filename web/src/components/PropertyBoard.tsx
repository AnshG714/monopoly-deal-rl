import { useState } from "react";

import type { PropertySet } from "@/api/types";
import {
  CARD_DESIGN_HEIGHT_REM,
  CARD_DESIGN_WIDTH_REM,
  CARD_SIZES,
} from "@/components/card/constants";
import { PropertyPile } from "@/components/PropertyPile";
import { cn, Flex } from "@/components/ui";

interface PropertyBoardProps {
  propertySets: PropertySet[];
  interactive?: boolean;
  acceptsDrop?: boolean;
  onDrop?: () => void;
  canMoveWild?: (setIdx: number, cardIdx: number) => boolean;
  onMoveWild?: (setIdx: number, cardIdx: number) => void;
  className?: string;
}

const PILE_SIZE = "md" as const;

export function PropertyBoard({
  propertySets,
  interactive = false,
  acceptsDrop = false,
  onDrop,
  canMoveWild,
  onMoveWild,
  className,
}: PropertyBoardProps) {
  const [dragOver, setDragOver] = useState(false);
  const dropReady = interactive && acceptsDrop;
  const highlighted = dropReady && dragOver;

  return (
    <Flex
      align="end"
      justify="center"
      wrap="wrap"
      gap="md"
      className={cn(
        "min-h-[6rem] rounded-[14px] p-3 transition-colors duration-150",
        interactive && "border-2 border-dashed",
        interactive &&
          cn(
            "bg-white/40",
            dropReady && "monopoly-drop-aura",
            highlighted
              ? "border-[rgba(74,202,0,0.95)] bg-[rgba(74,202,0,0.08)]"
              : "border-[var(--color-border)]",
          ),
        className,
      )}
      onDragEnter={
        interactive
          ? (event) => {
              event.preventDefault();
              if (acceptsDrop) setDragOver(true);
            }
          : undefined
      }
      onDragOver={
        interactive
          ? (event) => {
              event.preventDefault();
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
              setDragOver(false);
              if (acceptsDrop) onDrop?.();
            }
          : undefined
      }
    >
      {propertySets.length === 0 && interactive ? (
        <span className="px-4 py-8 text-sm font-medium text-[var(--text-muted)]">
          Drop properties here
        </span>
      ) : (
        propertySets.map((pile, setIdx) => (
          <PropertyPile
            key={pile.color}
            pile={pile}
            setIdx={interactive ? setIdx : undefined}
            canMoveWild={interactive ? canMoveWild : undefined}
            onMoveWild={interactive ? onMoveWild : undefined}
          />
        ))
      )}
      {propertySets.length === 0 && !interactive && (
        <Flex
          align="center"
          justify="center"
          className="rounded-[10px] border border-dashed border-[var(--color-border)] text-sm text-[var(--text-muted)]"
          style={{
            width: CARD_SIZES[PILE_SIZE],
            aspectRatio: `${CARD_DESIGN_WIDTH_REM} / ${CARD_DESIGN_HEIGHT_REM}`,
          }}
        >
          No properties
        </Flex>
      )}
    </Flex>
  );
}
