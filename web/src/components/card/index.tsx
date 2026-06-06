import { cva } from "class-variance-authority";
import type { CSSProperties } from "react";

import type { Card as CardData } from "@/api/types";
import { cn } from "@/components/ui";

import { CardFrame } from "./CardFrame";
import { CornerBadge } from "./CornerBadge";
import {
  CARD_DESIGN_HEIGHT_REM,
  CARD_DESIGN_WIDTH_REM,
  CARD_SIZES,
  type CardSize,
} from "./constants";
import {
  cardThemeVars,
  cardTitle,
  shellKind,
  valueText,
  visualKind,
} from "./utils";

const shellBase =
  'relative isolate h-full w-full select-none font-[Arial,Helvetica,sans-serif] text-[0.86rem] text-gray-900 before:pointer-events-none before:absolute before:inset-[0.34rem] before:rounded-[9px] before:border before:border-[#84a0c6] before:content-[""] shadow-[0_15px_30px_rgba(0,0,0,0.3),inset_0_0_0_1px_rgba(255,255,255,0.72)]';

const cardShellVariants = cva(
  `${shellBase} rounded-[14px] border-2 p-[0.55rem] transition-[box-shadow,transform] duration-150 ease-in-out`,
  {
    variants: {
      kind: {
        money:
          "border-[#74819a] bg-[linear-gradient(145deg,color-mix(in_srgb,var(--card-accent)_82%,white),var(--card-accent)),var(--card-accent)] before:border-[color-mix(in_srgb,var(--card-accent-2)_62%,#1f2937)]",
        action:
          "border-[color-mix(in_srgb,var(--card-accent)_54%,#334155)] bg-[linear-gradient(145deg,rgba(255,255,255,0.75),rgba(219,232,250,0.4)),var(--card-paper)]",
        rent: "border-[#74819a] bg-[linear-gradient(145deg,rgba(255,255,255,0.75),rgba(219,232,250,0.4)),var(--card-paper)]",
        "property-single":
          "border-[#74819a] bg-[linear-gradient(145deg,rgba(255,255,255,0.75),rgba(219,232,250,0.4)),var(--card-paper)]",
        "property-multi":
          "border-[#74819a] bg-[linear-gradient(145deg,rgba(255,255,255,0.75),rgba(219,232,250,0.4)),var(--card-paper)]",
        "property-wild":
          "border-[#74819a] bg-[linear-gradient(145deg,rgba(255,255,255,0.75),rgba(219,232,250,0.4)),var(--card-paper)]",
        default:
          "border-[#74819a] bg-[linear-gradient(145deg,rgba(255,255,255,0.75),rgba(219,232,250,0.4)),var(--card-paper)]",
      },
    },
    defaultVariants: {
      kind: "default",
    },
  },
);

const viewportVariants = cva("relative shrink-0 overflow-hidden", {
  variants: {
    draggable: {
      true: "cursor-grab hover:shadow-[0_18px_34px_rgba(0,0,0,0.35),0_0_0_2px_rgba(45,212,191,0.35)] active:cursor-grabbing [&_[data-card-shell]]:active:translate-y-0.5 [&_[data-card-shell]]:active:-rotate-1",
      false: "",
    },
    clickable: {
      true: "cursor-pointer focus-visible:outline-2 focus-visible:outline-[var(--accent)] focus-visible:outline-offset-2",
      false: "",
    },
  },
  defaultVariants: {
    draggable: false,
    clickable: false,
  },
});

type CardViewportStyle = CSSProperties & {
  "--card-scale"?: string;
};

export interface CardProps {
  card: CardData;
  size?: CardSize;
  /** Display width; height follows design aspect ratio. Overrides `size`. */
  width?: string;
  draggable?: boolean;
  className?: string;
  onDragStart?: () => void;
  onDragEnd?: () => void;
  onClick?: () => void;
}

export function Card({
  card,
  size = "md",
  width,
  draggable = false,
  className,
  onDragStart,
  onDragEnd,
  onClick,
}: CardProps) {
  const kind = visualKind(card);
  const title = cardTitle(card);
  const displayWidth = width ?? CARD_SIZES[size];

  const viewportStyle: CardViewportStyle = {
    width: displayWidth,
    height: `calc(${displayWidth} * ${CARD_DESIGN_HEIGHT_REM} / ${CARD_DESIGN_WIDTH_REM})`,
    aspectRatio: `${CARD_DESIGN_WIDTH_REM} / ${CARD_DESIGN_HEIGHT_REM}`,
    "--card-scale": `calc(${displayWidth} / ${CARD_DESIGN_WIDTH_REM}rem)`,
  };

  const canvasStyle: CardViewportStyle = {
    width: `${CARD_DESIGN_WIDTH_REM}rem`,
    height: `${CARD_DESIGN_HEIGHT_REM}rem`,
    transform: "scale(var(--card-scale))",
    transformOrigin: "top left",
  };

  return (
    <div
      className={cn(
        viewportVariants({
          draggable,
          clickable: Boolean(onClick),
        }),
        className,
      )}
      style={viewportStyle}
      draggable={draggable}
      onDragStart={(event) => {
        if (!draggable) return;
        event.dataTransfer.effectAllowed = "move";
        onDragStart?.();
      }}
      onDragEnd={() => onDragEnd?.()}
      onClick={
        onClick
          ? (event) => {
              event.stopPropagation();
              onClick();
            }
          : undefined
      }
      role={onClick ? "button" : undefined}
      tabIndex={onClick ? 0 : undefined}
      onKeyDown={
        onClick
          ? (event) => {
              if (event.key === "Enter" || event.key === " ") {
                event.preventDefault();
                onClick();
              }
            }
          : undefined
      }
      title={title}
    >
      <div className="origin-top-left" style={canvasStyle}>
        <div
          data-card-shell
          className={cn(
            cardShellVariants({ kind: shellKind(kind) }),
            "bg-white",
          )}
          style={cardThemeVars(card) as CSSProperties}
        >
          <CornerBadge position="top" value={valueText(card)} kind={kind} />
          <CardFrame card={card} kind={kind} />
          <CornerBadge position="bottom" value={valueText(card)} kind={kind} />
        </div>
      </div>
    </div>
  );
}
