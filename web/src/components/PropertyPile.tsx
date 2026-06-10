import { useState } from "react";

import type { PropertySet } from "@/api/types";
import { Card } from "@/components/card";
import { COLOR_MAP } from "@/components/card/colors";
import {
  CARD_DESIGN_HEIGHT_REM,
  CARD_DESIGN_WIDTH_REM,
  CARD_SIZES,
} from "@/components/card/constants";
import { colorLabel } from "@/components/card/utils";
import { isWildPropertyCard } from "@/lib/legalMoves";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";
import { cn, Flex } from "@/components/ui";

const PILE_SIZE = "md" as const;
const PILE_OVERLAP_REM = -2.75;

interface PropertyPileProps {
  pile: PropertySet;
  setIdx?: number;
  canMoveWild?: (setIdx: number, cardIdx: number) => boolean;
  onMoveWild?: (setIdx: number, cardIdx: number) => void;
  className?: string;
}

export function PropertyPile({
  pile,
  setIdx,
  canMoveWild,
  onMoveWild,
  className,
}: PropertyPileProps) {
  const [open, setOpen] = useState(false);
  const accent = COLOR_MAP[pile.color] ?? pile.color;

  function handleMoveWild(cardIdx: number) {
    if (setIdx === undefined) return;
    setOpen(false);
    onMoveWild?.(setIdx, cardIdx);
  }

  return (
    <>
      <Flex
        direction="column"
        align="center"
        gap="xs"
        className={cn("shrink-0 cursor-pointer", className)}
        onClick={() => setOpen(true)}
      >
        <Flex
          align="center"
          justify="center"
          className="rounded-full px-2 py-0.5 text-[0.65rem] font-semibold text-white"
          style={{ backgroundColor: accent }}
        >
          {colorLabel(pile.color)}
          {pile.complete && " · complete"}
          {pile.has_house && " · house"}
          {pile.has_hotel && " · hotel"}
        </Flex>

        <Flex
          align="end"
          justify="center"
          className="rounded-[10px] border border-[var(--color-border)] bg-white/60 px-1 pb-1 pt-2"
          style={{
            minWidth: CARD_SIZES[PILE_SIZE],
            minHeight: `calc(${CARD_SIZES[PILE_SIZE]} * ${CARD_DESIGN_HEIGHT_REM} / ${CARD_DESIGN_WIDTH_REM} + 0.5rem)`,
          }}
        >
          {pile.cards.map((card, index) => (
            <div
              key={index}
              className="pointer-events-none relative shrink-0"
              style={{
                marginLeft: index === 0 ? 0 : `${PILE_OVERLAP_REM}rem`,
                zIndex: index,
              }}
            >
              <Card card={card} size={PILE_SIZE} />
            </div>
          ))}
        </Flex>
      </Flex>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent
          className={cn(
            "flex w-full max-w-3xl flex-col gap-4 sm:max-w-3xl",
            "max-h-[85vh] overflow-y-auto",
          )}
        >
          <DialogTitle>{colorLabel(pile.color)} properties</DialogTitle>
          <Flex wrap="wrap" gap="md" justify="center">
            {pile.cards.map((card, index) => {
              const showMoveWild =
                setIdx !== undefined &&
                isWildPropertyCard(card) &&
                canMoveWild?.(setIdx, index);

              return (
                <Flex
                  key={index}
                  direction="column"
                  align="center"
                  gap="sm"
                  className="shrink-0"
                >
                  <Card
                    card={card}
                    size="md"
                    className="overflow-visible"
                  />
                  {showMoveWild && (
                    <Button
                      type="button"
                      size="sm"
                      variant="outline"
                      onClick={() => handleMoveWild(index)}
                    >
                      Move to another color
                    </Button>
                  )}
                </Flex>
              );
            })}
          </Flex>
        </DialogContent>
      </Dialog>
    </>
  );
}
