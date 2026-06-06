import { cva } from 'class-variance-authority'

import { cn } from '@/components/ui'

import { cornerKind, type VisualKind } from './utils'

const cornerVariants = cva(
  'absolute z-[2] grid h-[1.82rem] w-[1.82rem] place-items-center rounded-full border-2 text-[0.58rem] font-extrabold leading-none shadow-[0_1px_0_rgba(255,255,255,0.7)]',
  {
    variants: {
      position: {
        top: 'top-[0.28rem] left-[0.28rem]',
        bottom: 'right-[0.28rem] bottom-[0.28rem] rotate-180',
      },
      kind: {
        money:
          'border-[#222936] bg-[color-mix(in_srgb,var(--card-accent)_78%,white)] text-gray-900',
        action:
          'border-[color-mix(in_srgb,var(--card-accent)_74%,#334155)] bg-white text-gray-900',
        default: 'border-[#56647a] bg-[#eef6ff] text-gray-900',
      },
    },
    defaultVariants: {
      position: 'top',
      kind: 'default',
    },
  },
)

interface CornerBadgeProps {
  position: 'top' | 'bottom'
  value: string
  kind: VisualKind
}

export function CornerBadge({ position, value, kind }: CornerBadgeProps) {
  return (
    <span
      className={cn(
        cornerVariants({
          position,
          kind: cornerKind(kind),
        }),
      )}
    >
      {value}
    </span>
  )
}
