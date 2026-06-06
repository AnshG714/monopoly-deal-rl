import { cva } from 'class-variance-authority'

import { Flex } from '@/components/ui/flex'
import { cn } from '@/lib/utils'

const colorBandVariants = cva(
  'overflow-hidden border-2 border-[#222936] bg-[var(--card-accent)]',
  {
    variants: {
      layout: {
        frame: 'min-h-[1.55rem]',
        multi:
          'min-h-[1.1rem] border bg-[linear-gradient(90deg,var(--card-accent),var(--card-accent-2))]',
        face: 'min-h-[1.55rem] w-full',
      },
    },
    defaultVariants: {
      layout: 'frame',
    },
  },
)

interface ColorBandProps {
  colors: string[]
  layout?: 'frame' | 'multi' | 'face'
  className?: string
}

export function ColorBand({
  colors,
  layout = 'frame',
  className,
}: ColorBandProps) {
  return (
    <Flex
      className={cn(colorBandVariants({ layout }), className)}
      align="stretch"
      gap="none"
    >
      {colors.map((color, index) => (
        <span
          key={`${color}-${index}`}
          className="block min-w-[0.35rem] flex-1"
          style={{ backgroundColor: color }}
        />
      ))}
    </Flex>
  )
}
