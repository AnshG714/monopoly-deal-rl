import type { Card } from '@/api/types'

import { ACTION_COPY } from '../constants'
import { cardTitle, cardTypeLabel } from '../utils'
import {
  ActionCopy,
  ActionLabel,
  ActionTitle,
  ActionWindow,
} from './ActionWindow'

interface ActionFaceProps {
  card: Card
}

export function ActionFace({ card }: ActionFaceProps) {
  const copy = card.action_type ? ACTION_COPY[card.action_type] : undefined

  return (
    <ActionWindow>
      <ActionLabel>{cardTypeLabel(card)}</ActionLabel>
      <ActionTitle>{cardTitle(card)}</ActionTitle>
      {copy && <ActionCopy>{copy}</ActionCopy>}
    </ActionWindow>
  )
}
