import { cva } from "class-variance-authority";

import { Flex } from "@/components/ui/flex";

const rentValueVariants = cva("font-black", {
  variants: {
    density: {
      default: "text-[0.94rem]",
      multi: "text-[0.52rem]",
    },
  },
  defaultVariants: {
    density: "default",
  },
});

const rentTableVariants = cva("w-full", {
  variants: {
    density: {
      default: "px-[0.15rem] py-[0.35rem]",
      multi: "px-[0.1rem] py-[0.05rem]",
    },
  },
  defaultVariants: {
    density: "default",
  },
});

const rentCaptionVariants = cva(
  "mb-[0.35rem] block text-center font-bold uppercase",
  {
    variants: {
      density: {
        default: "text-[0.6rem] text-slate-600",
        single: "text-[1.32rem] font-medium tracking-[0.02em] text-gray-900",
        multi: "mb-[0.06rem] text-[0.48rem] text-gray-900",
      },
    },
    defaultVariants: {
      density: "default",
    },
  },
);

const rentRowVariants = cva("my-[0.3rem] [--flex-gap:0.36rem]", {
  variants: {
    density: {
      default: "",
      multi: "my-[0.04rem] [--flex-gap:0.1rem]",
    },
  },
  defaultVariants: {
    density: "default",
  },
});

const rentCountVariants = cva(
  "grid place-items-center rounded-[0.18rem] border border-slate-500 border-t-[0.25rem] border-t-[var(--card-accent)] bg-blue-100 font-extrabold",
  {
    variants: {
      density: {
        default: "h-[1.36rem] w-[1.36rem] text-[0.74rem]",
        multi: "h-[0.82rem] w-[0.82rem] border-t-[0.14rem] text-[0.44rem]",
      },
    },
    defaultVariants: {
      density: "default",
    },
  },
);

interface RentLadderProps {
  rents: number[] | undefined;
  label?: string;
  color?: string;
  density?: "default" | "single" | "multi";
}

export function RentLadder({
  rents,
  label,
  color,
  density = "default",
}: RentLadderProps) {
  if (!rents || rents.length === 0) return null;

  const rowDensity = density === "multi" ? "multi" : "default";
  const captionDensity =
    density === "single" ? "single" : density === "multi" ? "multi" : "default";

  return (
    <div className={rentTableVariants({ density: rowDensity })}>
      <span className={rentCaptionVariants({ density: captionDensity })}>
        {label ? `${label} rent` : "Rent"}
      </span>
      {rents.map((rent, index) => (
        <Flex
          key={`${label ?? "rent"}-${index}`}
          className={rentRowVariants({ density: rowDensity })}
          align="center"
          gap="none"
        >
          <span
            className={rentCountVariants({ density: rowDensity })}
            style={color ? { borderTopColor: color } : undefined}
          >
            {index + 1}
          </span>
          <span className="min-w-[1.15rem] flex-1 border-b border-dotted border-slate-500" />
          <span className={rentValueVariants({ density: rowDensity })}>
            ${rent}M
          </span>
        </Flex>
      ))}
    </div>
  );
}
