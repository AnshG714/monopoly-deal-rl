import { useState } from "react";

import type { Card as CardData } from "@/api/types";
import { Card } from "@/components/card";
import {
  CARD_DESIGN_HEIGHT_REM,
  CARD_DESIGN_WIDTH_REM,
  CARD_SIZES,
} from "@/components/card/constants";
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";
import { cn, Flex } from "@/components/ui";

interface PlayerBankProps {
  cards: CardData[];
  className?: string;
  dialogTitle?: string;
  emptyLabel?: string;
  acceptsDrop?: boolean;
  onDrop?: () => void;
}

const PILE_SIZE = "md" as const;
const PILE_OVERLAP_REM = -7.5;

export function PlayerBank({
  cards,
  className,
  dialogTitle = "Bank",
  emptyLabel = "Bank",
  acceptsDrop = false,
  onDrop,
}: PlayerBankProps) {
  const [dragOver, setDragOver] = useState(false);
  const [open, setOpen] = useState(false);

  const interactive = Boolean(onDrop);
  const dropReady = interactive && acceptsDrop;
  const highlighted = dropReady && dragOver;

  return (
    <>
      <Flex
        align="end"
        justify="center"
        className={cn(
          "relative shrink-0 cursor-pointer rounded-[14px] border-2 p-2 transition-colors duration-150",
          interactive
            ? cn(
                "border-dashed bg-white/60",
                dropReady && "monopoly-drop-aura",
                highlighted
                  ? "border-[rgba(74,202,0,0.95)] bg-[rgba(74,202,0,0.08)]"
                  : "border-[var(--color-border)]",
              )
            : "border-[var(--color-border)] bg-white/60",
          className,
        )}
        style={{
          minWidth: CARD_SIZES[PILE_SIZE],
          minHeight: `calc(${CARD_SIZES[PILE_SIZE]} * ${CARD_DESIGN_HEIGHT_REM} / ${CARD_DESIGN_WIDTH_REM})`,
        }}
        onClick={() => setOpen(true)}
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
        {cards.length === 0 ? (
          <span
            className={cn(
              "px-4 text-sm font-medium",
              interactive
                ? "text-[var(--color-text)]"
                : "text-muted-foreground",
            )}
          >
            {emptyLabel}
          </span>
        ) : (
          cards.map((card, index) => (
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
          ))
        )}
      </Flex>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent
          className={cn(
            "flex w-full max-w-3xl flex-col gap-4 sm:max-w-3xl",
            "max-h-[85vh] overflow-y-auto",
          )}
        >
          <DialogTitle>{dialogTitle}</DialogTitle>
          {cards.length === 0 ? (
            <p className="text-muted-foreground text-sm">No cards in bank.</p>
          ) : (
            <Flex wrap="wrap" gap="md" justify="center">
              {cards.map((card, index) => (
                <Card
                  key={index}
                  card={card}
                  size="md"
                  className="overflow-visible"
                />
              ))}
            </Flex>
          )}
        </DialogContent>
      </Dialog>
    </>
  );
}
