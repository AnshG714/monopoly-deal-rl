import type { Card } from "@/api/types";

import { valueText } from "../utils";

interface MoneyFaceProps {
  card: Card;
}

export function MoneyFace({ card }: MoneyFaceProps) {
  return (
    <div className='relative grid h-full w-full place-items-center border-[0.34rem] border-double border-[color-mix(in_srgb,var(--card-accent-2)_72%,#111827)] bg-[linear-gradient(90deg,transparent_0_8%,rgba(255,255,255,0.18)_8%_11%,transparent_11%_89%,rgba(255,255,255,0.18)_89%_92%,transparent_92%),radial-gradient(circle,rgba(255,255,255,0.45)_0_32%,transparent_33%),linear-gradient(145deg,var(--card-accent),var(--card-accent-2))] shadow-[inset_0_0_0_0.2rem_rgba(255,255,255,0.2),inset_0_0_0_0.42rem_rgba(17,24,39,0.08)] before:pointer-events-none before:absolute before:inset-[0.62rem] before:border before:border-[rgba(17,24,39,0.45)] before:content-[""] after:pointer-events-none after:absolute after:inset-[1.02rem] after:border after:border-dotted after:border-[rgba(17,24,39,0.45)] after:opacity-55 after:content-[""]'>
      <span className="relative z-[1] grid h-[6.35rem] w-[6.35rem] place-items-center rounded-full border-[3px] border-zinc-800 bg-white/30 text-[1.9rem] font-black shadow-[inset_0_0_0_0.22rem_rgba(17,24,39,0.08)]">
        {valueText(card)}
      </span>
    </div>
  );
}
