import type { Card } from '@/api/types'
import { Flex } from '@/components/ui/flex'

import { ColorBand } from '../ColorBand'
import { colorBandColors } from '../utils'

interface WildPropertyFaceProps {
  card: Card
}

export function WildPropertyFace({ card }: WildPropertyFaceProps) {
  return (
    <Flex
      className="w-full text-center [--flex-gap:0.7rem]"
      direction="column"
      align="center"
      gap="none"
    >
      <ColorBand colors={colorBandColors(card)} layout="face" />
      <div className="grid h-[4.2rem] w-[4.2rem] place-items-center rounded-full bg-[radial-gradient(circle_at_50%_32%,#fff_0_20%,transparent_21%),linear-gradient(180deg,#111827_0_30%,#f8fafc_31%_58%,#111827_59%)] text-[0.9rem] font-black text-gray-900">
        M
      </div>
      <p className="m-0 text-[0.62rem] leading-[1.15] font-semibold text-slate-700">
        This card can be used as part of any property set.
      </p>
    </Flex>
  )
}
