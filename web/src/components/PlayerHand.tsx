import { useState } from "react";

import type { HandCard } from "@/api/types";
import { Card } from "@/components/card";
import type { CardSize } from "@/components/card/constants";
import { cardTitle } from "@/components/card/utils";
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";
import { cn, Flex } from "@/components/ui";

interface PlayerHandProps {
  cards: HandCard[];
  size?: CardSize;
  className?: string;
  canPlayAsMoney?: (handIndex: number) => boolean;
  canPlayAsProperty?: (handIndex: number) => boolean;
  canPlayAsAction?: (handIndex: number) => boolean;
  onDragStart?: (handIndex: number) => void;
  onDragEnd?: () => void;
}

function fanRotation(index: number, total: number, spreadDeg: number): number {
  if (total <= 1) return 0;
  const center = (total - 1) / 2;
  return ((index - center) / center) * spreadDeg;
}

function cardZIndex(index: number, hoveredIndex: number | null, total: number) {
  return hoveredIndex === index ? total : index;
}

const COLLAPSED_SPREAD = 8;
const EXPANDED_SPREAD = 14;
const COLLAPSED_SCALE = 0.85;
const COLLAPSED_OVERLAP_REM = -8.25;
const EXPANDED_OVERLAP_REM = -4.25;

export function PlayerHand({
  cards,
  size = "lg",
  className,
  canPlayAsMoney,
  canPlayAsProperty,
  canPlayAsAction,
  onDragStart,
  onDragEnd,
}: PlayerHandProps) {
  const [expanded, setExpanded] = useState(false);
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);
  const [selectedCard, setSelectedCard] = useState<HandCard | null>(null);

  const spread = expanded ? EXPANDED_SPREAD : COLLAPSED_SPREAD;
  const overlap = expanded ? EXPANDED_OVERLAP_REM : COLLAPSED_OVERLAP_REM;

  return (
    <>
      <Flex
        className={cn("relative", className)}
        align="end"
        justify="center"
        onMouseEnter={() => setExpanded(true)}
        onMouseLeave={() => {
          setExpanded(false);
          setHoveredIndex(null);
        }}
      >
        {cards.map((card, index) => (
          <div
            key={card.index}
            className={cn(
              "relative shrink-0 origin-bottom",
              "transition-all duration-300 ease-out",
              hoveredIndex === index && "-translate-y-3",
            )}
            style={{
              marginLeft: index === 0 ? 0 : `${overlap}rem`,
              rotate:
                hoveredIndex === index
                  ? "0deg"
                  : `${fanRotation(index, cards.length, spread)}deg`,
              scale: expanded ? 1 : COLLAPSED_SCALE,
              zIndex: cardZIndex(index, hoveredIndex, cards.length),
            }}
            onMouseEnter={() => setHoveredIndex(index)}
          >
            <Card
              card={card}
              size={size}
              draggable={
                (canPlayAsMoney?.(card.index) ?? false) ||
                (canPlayAsProperty?.(card.index) ?? false) ||
                (canPlayAsAction?.(card.index) ?? false)
              }
              onDragStart={() => onDragStart?.(card.index)}
              onDragEnd={onDragEnd}
              onClick={() => setSelectedCard(card)}
            />
          </div>
        ))}
      </Flex>

      <Dialog
        open={selectedCard !== null}
        onOpenChange={(open) => {
          if (!open) setSelectedCard(null);
        }}
      >
        <DialogContent
          className={
            "w-auto max-w-fit overflow-visible gap-0 border-none bg-transparent p-4 shadow-none"
          }
          showCloseButton={false}
        >
          <DialogTitle className="sr-only">
            {selectedCard ? cardTitle(selectedCard) : "Card"}
          </DialogTitle>
          {selectedCard && (
            <Card
              card={selectedCard}
              width="16rem"
              className="pointer-events-none overflow-visible"
            />
          )}
        </DialogContent>
      </Dialog>
    </>
  );
}
