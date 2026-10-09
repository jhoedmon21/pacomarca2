/**
 * Insignia de estado (por ejemplo: +12.5 % en verde).
 */
import { cva, type VariantProps } from 'class-variance-authority'
import type { HTMLAttributes } from 'react'
import { cn } from '../../lib/utils'

const variantes = cva('inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-bold', {
  variants: {
    variant: {
      neutral: 'bg-surface-2 text-muted',
      success: 'bg-success/10 text-success',
      warning: 'bg-warning/10 text-warning',
      danger: 'bg-danger/10 text-danger',
      accent: 'bg-accent/10 text-accent',
    },
  },
  defaultVariants: { variant: 'neutral' },
})

export interface BadgeProps
  extends HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof variantes> {}

export function Badge({ className, variant, ...props }: BadgeProps) {
  return <span className={cn(variantes({ variant }), className)} {...props} />
}
