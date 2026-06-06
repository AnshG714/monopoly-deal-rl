import type { Card } from '@/api/types'

import { ColorBand } from '../ColorBand'
import { RentColors } from '../RentColors'
import { colorBandColors } from '../utils'
import {
  ActionCopy,
  ActionLabel,
  ActionTitle,
  ActionWindow,
} from './ActionWindow'

interface RentFaceProps {
  card: Card
}

export function RentFace({ card }: RentFaceProps) {
  const colors = [card.color1, card.color2].filter(Boolean) as string[]

  return (
    <ActionWindow>
      <ActionLabel>Action Card</ActionLabel>
      <ActionTitle rent>Rent</ActionTitle>
      {colors.length > 0 ? (
        <RentColors colors={colors} />
      ) : (
        <ColorBand colors={colorBandColors(card)} layout="face" />
      )}
      <ActionCopy>Charge rent for properties in the shown colors.</ActionCopy>
    </ActionWindow>
  )
}
