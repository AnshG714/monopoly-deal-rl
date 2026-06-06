import type { VisualKind } from './utils'

export function frameShowsColorBand(kind: VisualKind): boolean {
  return kind === 'property-multi'
}

export function frameShowsNameplate(kind: VisualKind): boolean {
  return kind === 'property-single' || kind === 'property-multi'
}
