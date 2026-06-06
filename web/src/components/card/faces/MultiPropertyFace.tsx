import type { Card } from '@/api/types'
import { Flex } from '@/components/ui/flex'

import { COLOR_MAP } from '../colors'
import { RentLadder } from '../RentLadder'
import { colorLabel } from '../utils'

interface MultiPropertyFaceProps {
  card: Card
}

export function MultiPropertyFace({ card }: MultiPropertyFaceProps) {
  const color1 = card.color1 ? COLOR_MAP[card.color1] : undefined
  const color2 = card.color2 ? COLOR_MAP[card.color2] : undefined

  return (
    <Flex className="w-full [--flex-gap:0.12rem]" direction="column" gap="none">
      <RentLadder
        rents={card.color1_rents}
        label={card.color1 ? colorLabel(card.color1) : undefined}
        color={color1}
        density="multi"
      />
      <div className="my-[0.12rem] h-px bg-[#c8d4e0]" />
      <RentLadder
        rents={card.color2_rents}
        label={card.color2 ? colorLabel(card.color2) : undefined}
        color={color2}
        density="multi"
      />
    </Flex>
  )
}
