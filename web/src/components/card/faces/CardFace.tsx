import type { Card } from '@/api/types'

import { cardTitle } from '../utils'
import { ActionWindow } from './ActionWindow'
import { ActionFace } from './ActionFace'
import { MoneyFace } from './MoneyFace'
import { PropertyFace } from './PropertyFace'
import { RentFace } from './RentFace'

interface CardFaceProps {
  card: Card
}

export function CardFace({ card }: CardFaceProps) {
  if (card.type === 'money') return <MoneyFace card={card} />
  if (card.action_type) return <ActionFace card={card} />
  if (card.type === 'rent') return <RentFace card={card} />
  if (card.property_kind) return <PropertyFace card={card} />

  return <ActionWindow>{cardTitle(card)}</ActionWindow>
}
