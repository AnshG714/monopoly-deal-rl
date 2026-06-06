import { cva } from 'class-variance-authority'
import type { ReactNode } from 'react'

import { Flex } from '@/components/ui/flex'
import { cn } from '@/components/ui'

const actionWindowVariants = cva(
  'relative h-full w-full px-2 py-[0.55rem] pt-[0.65rem] text-center before:absolute before:bottom-[0.42rem] before:top-[0.42rem] before:w-[0.34rem] before:border before:border-[rgba(34,41,54,0.35)] before:bg-[color-mix(in_srgb,var(--card-accent)_36%,white)] before:content-[""] after:absolute after:bottom-[0.42rem] after:top-[0.42rem] after:w-[0.34rem] after:border after:border-[rgba(34,41,54,0.35)] after:bg-[color-mix(in_srgb,var(--card-accent)_36%,white)] after:content-[""] before:left-[0.38rem] after:right-[0.38rem] border-[3px] border-double border-[color-mix(in_srgb,var(--card-accent)_54%,#222936)] bg-[repeating-linear-gradient(90deg,transparent_0_0.34rem,rgba(17,24,39,0.04)_0.34rem_0.44rem),linear-gradient(135deg,color-mix(in_srgb,var(--card-paper)_84%,#94a3b8),var(--card-paper))]',
)

const actionLabelVariants = cva(
  'relative z-[1] self-start border border-[rgba(34,41,54,0.28)] bg-white/60 px-[0.42rem] py-[0.15rem] text-[0.66rem] font-black tracking-[0.05em] uppercase',
)

const actionTitleVariants = cva(
  'relative z-[1] my-auto grid aspect-square w-[88%] shrink-0 place-items-center rounded-full border-[0.5rem] border-[var(--card-accent)] bg-[#eef6ff] px-[0.34rem] text-[1.05rem] font-black leading-[1.05] text-gray-900 uppercase',
  {
    variants: {
      rent: {
        true: 'border-[#c2410c]',
        false: '',
      },
    },
    defaultVariants: {
      rent: false,
    },
  },
)

interface ActionWindowProps {
  children: ReactNode
}

export function ActionWindow({ children }: ActionWindowProps) {
  return (
    <Flex
      className={cn(actionWindowVariants())}
      direction="column"
      align="center"
      justify="start"
      gap="none"
    >
      {children}
    </Flex>
  )
}

interface ActionLabelProps {
  children: ReactNode
}

export function ActionLabel({ children }: ActionLabelProps) {
  return <span className={actionLabelVariants()}>{children}</span>
}

interface ActionTitleProps {
  rent?: boolean
  children: ReactNode
}

export function ActionTitle({ rent = false, children }: ActionTitleProps) {
  return (
    <strong className={actionTitleVariants({ rent })}>{children}</strong>
  )
}

interface ActionCopyProps {
  children: ReactNode
}

export function ActionCopy({ children }: ActionCopyProps) {
  return (
    <p className="m-0 text-[0.62rem] leading-[1.15] font-semibold text-slate-700">
      {children}
    </p>
  )
}
