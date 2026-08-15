import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import type * as React from "react";

import { cn } from "./cn";

const flexVariants = cva("gap-[length:var(--flex-gap,0px)]", {
  variants: {
    direction: {
      row: "flex-row",
      column: "flex-col",
      "row-reverse": "flex-row-reverse",
      "column-reverse": "flex-col-reverse",
    },
    align: {
      start: "items-start",
      center: "items-center",
      end: "items-end",
      stretch: "items-stretch",
      baseline: "items-baseline",
    },
    justify: {
      start: "justify-start",
      center: "justify-center",
      end: "justify-end",
      between: "justify-between",
      around: "justify-around",
      evenly: "justify-evenly",
    },
    wrap: {
      nowrap: "flex-nowrap",
      wrap: "flex-wrap",
      "wrap-reverse": "flex-wrap-reverse",
    },
    inline: {
      true: "inline-flex",
      false: "flex",
    },
    gap: {
      none: "[--flex-gap:0px]",
      xs: "[--flex-gap:var(--space-xs)]",
      sm: "[--flex-gap:var(--space-sm)]",
      md: "[--flex-gap:var(--space-md)]",
      lg: "[--flex-gap:var(--space-lg)]",
      xl: "[--flex-gap:var(--space-xl)]",
      card: "[--flex-gap:var(--card-gap)]",
    },
  },
  defaultVariants: {
    direction: "row",
    align: "stretch",
    justify: "start",
    wrap: "nowrap",
    inline: false,
    gap: "none",
  },
});

type FlexStyle = React.CSSProperties & {
  "--flex-gap"?: string;
};

function Flex({
  className,
  direction,
  align,
  justify,
  wrap,
  inline,
  gap,
  asChild = false,
  style,
  ...props
}: React.ComponentProps<"div"> &
  VariantProps<typeof flexVariants> & {
    asChild?: boolean;
  }) {
  const Comp = asChild ? Slot : "div";

  return (
    <Comp
      data-slot="flex"
      className={cn(
        flexVariants({
          direction,
          align,
          justify,
          wrap,
          inline,
          gap,
          className,
        }),
      )}
      style={style as FlexStyle}
      {...props}
    />
  );
}

export { Flex };
