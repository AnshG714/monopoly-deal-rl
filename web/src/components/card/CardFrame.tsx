import { cva } from 'class-variance-authority'

import type { Card } from '@/api/types'
import { Flex } from '@/components/ui/flex'
import { cn } from '@/lib/utils'

import { frameShowsColorBand, frameShowsNameplate } from './chrome'
import { ColorBand } from './ColorBand'
import { CardFace } from './faces/CardFace'
import { Nameplate } from './Nameplate'
import {
  cardTitle,
  cardTypeLabel,
  colorBandColors,
  type VisualKind,
} from './utils'

const frameVariants = cva('relative z-[1] h-full min-h-0', {
  variants: {
    kind: {
      money: 'px-2 pt-[0.78rem] pb-[0.42rem]',
      default: 'px-[0.48rem] pt-[0.78rem] pb-[0.36rem]',
    },
  },
  defaultVariants: {
    kind: 'default',
  },
})

interface CardFrameProps {
  card: Card
  kind: VisualKind
}

export function CardFrame({ card, kind }: CardFrameProps) {
  return (
    <Flex
      className={cn(frameVariants({ kind: kind === 'money' ? 'money' : 'default' }))}
      direction="column"
      gap="sm"
    >
      {frameShowsColorBand(kind) && (
        <ColorBand colors={colorBandColors(card)} layout="multi" />
      )}
      {frameShowsNameplate(kind) && (
        <Nameplate
          typeLabel={cardTypeLabel(card)}
          title={cardTitle(card)}
          kind={kind}
        />
      )}
      <div className="grid min-h-0 flex-1 place-items-center">
        <CardFace card={card} />
      </div>
      <div className="mt-auto text-center text-[0.46rem] text-[#64748b]">
        © Monopoly Deal Engine
      </div>
    </Flex>
  )
}
