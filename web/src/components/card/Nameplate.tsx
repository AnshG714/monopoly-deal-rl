import { cva } from 'class-variance-authority'

import { Flex } from '@/components/ui/flex'
import { cn } from '@/lib/utils'

import type { VisualKind } from './utils'

const nameplateVariants = cva(
  'border-2 border-[#222936] text-center uppercase text-gray-900',
  {
    variants: {
      kind: {
        'property-single':
          'mt-[0.2rem] min-h-[2.7rem] bg-[var(--card-accent)] px-[0.35rem] py-1',
        'property-multi':
          'min-h-fit bg-[linear-gradient(90deg,var(--card-accent),var(--card-accent-2))] px-[0.35rem] py-1',
        default: 'min-h-[2.45rem] bg-[var(--card-accent)] px-[0.35rem] py-1',
      },
    },
    defaultVariants: {
      kind: 'default',
    },
  },
)

const nameplateTypeVariants = cva('font-extrabold tracking-[0.06em]', {
  variants: {
    kind: {
      'property-single': 'hidden',
      'property-multi': 'text-[0.52rem]',
      default: 'text-[0.53rem]',
    },
  },
  defaultVariants: {
    kind: 'default',
  },
})

const nameplateTitleVariants = cva('overflow-hidden font-black', {
  variants: {
    kind: {
      'property-single': 'text-[1.04rem] leading-[1.05]',
      'property-multi': 'text-[0.8rem] leading-[1.02]',
      default: 'line-clamp-2 text-[0.85rem] leading-[1.02]',
    },
  },
  defaultVariants: {
    kind: 'default',
  },
})

interface NameplateProps {
  typeLabel: string
  title: string
  kind: VisualKind
}

export function Nameplate({ typeLabel, title, kind }: NameplateProps) {
  const nameplateKind =
    kind === 'property-single' || kind === 'property-multi' ? kind : 'default'

  return (
    <Flex
      className={cn(nameplateVariants({ kind: nameplateKind }))}
      direction="column"
      align="center"
      justify="center"
      gap="none"
    >
      <span className={nameplateTypeVariants({ kind: nameplateKind })}>
        {typeLabel}
      </span>
      <strong className={nameplateTitleVariants({ kind: nameplateKind })}>
        {title}
      </strong>
    </Flex>
  )
}
