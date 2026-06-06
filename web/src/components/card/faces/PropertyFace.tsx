import type { Card } from '@/api/types'

import { COLOR_MAP } from '../colors'
import { RentLadder } from '../RentLadder'
import { MultiPropertyFace } from './MultiPropertyFace'
import { WildPropertyFace } from './WildPropertyFace'

interface PropertyFaceProps {
  card: Card
}

export function PropertyFace({ card }: PropertyFaceProps) {
  if (card.property_kind === 'wild') {
    return <WildPropertyFace card={card} />
  }

  if (card.property_kind === 'multi') {
    return <MultiPropertyFace card={card} />
  }

  return (
    <RentLadder
      rents={card.rents}
      color={card.color ? COLOR_MAP[card.color] : undefined}
      density="single"
    />
  )
}
