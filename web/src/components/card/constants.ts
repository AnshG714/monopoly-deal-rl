/** Canonical card artboard — all layout is authored at this size. */
export const CARD_DESIGN_WIDTH_REM = 12
export const CARD_DESIGN_HEIGHT_REM = 17.15

export const CARD_SIZES = {
  sm: '5.5rem',
  md: '12rem',
} as const

export type CardSize = keyof typeof CARD_SIZES

export const RAINBOW_COLORS = [
  'brown',
  'light_blue',
  'pink',
  'orange',
  'red',
  'yellow',
  'green',
  'blue',
  'railroad',
  'utility',
] as const

export const ACTION_ACCENTS: Record<string, string> = {
  deal_breaker: '#7c3aed',
  debt_collector: '#c4b5fd',
  double_rent: '#f59e0b',
  forced_deal: '#64748b',
  house: '#38bdf8',
  hotel: '#f472b6',
  its_my_birthday: '#fb923c',
  just_say_no: '#67e8f9',
  pass_go: '#fde68a',
  sly_deal: '#a3a3a3',
}

export const ACTION_THEMES: Record<string, { paper: string; symbol: string }> = {
  deal_breaker: { paper: '#cfc4f0', symbol: '#eee8ff' },
  debt_collector: { paper: '#d6e1e0', symbol: '#edf7f5' },
  double_rent: { paper: '#eee4c2', symbol: '#fff7d6' },
  forced_deal: { paper: '#d4d7dc', symbol: '#f1f5f9' },
  house: { paper: '#d2d8d2', symbol: '#dcfce7' },
  hotel: { paper: '#d7e5f7', symbol: '#eff6ff' },
  its_my_birthday: { paper: '#ded0c7', symbol: '#ffedd5' },
  just_say_no: { paper: '#b9dded', symbol: '#e0f7ff' },
  pass_go: { paper: '#ebe5c8', symbol: '#fff8d5' },
  sly_deal: { paper: '#d3d5da', symbol: '#f8fafc' },
}

export const DEFAULT_CARD_PAPER = '#eef6ff'
export const DEFAULT_CARD_SYMBOL = '#eef6ff'
export const ACTION_CARD_PAPER = '#d8d3ea'

export const ACTION_COPY: Record<string, string> = {
  deal_breaker: 'Steal a full property set from any player.',
  debt_collector: 'Force any player to pay you $5M.',
  double_rent: 'Play with a rent card to charge double.',
  forced_deal: 'Swap one property with another player.',
  house: 'Add onto a full set to raise its rent.',
  hotel: 'Add onto a full set with a house.',
  its_my_birthday: 'All other players pay you $2M.',
  just_say_no: 'Cancel an action played against you.',
  pass_go: 'Draw two extra cards.',
  sly_deal: 'Steal one property from any player.',
}

export const MONEY_ACCENTS: Record<number, [string, string]> = {
  1: ['#d9dfcc', '#9eaa8e'],
  2: ['#d7ccd7', '#aa96ad'],
  3: ['#cfd3cd', '#9aa09a'],
  4: ['#b9cde5', '#7895b7'],
  5: ['#9d8bd6', '#6b5aa7'],
  10: ['#d0aa38', '#9a741a'],
}
