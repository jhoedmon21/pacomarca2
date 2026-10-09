/**
 * Botón con variantes (convención shadcn/ui sobre class-variance-authority).
 */
import { cva, type VariantProps } from 'class-variance-authority'
import { forwardRef, type ButtonHTMLAttributes } from 'react'
import { cn } from '../../lib/utils'

const variantes = cva(
  'inline-flex items-center justify-center gap-2 rounded-lg font-semibold transition-colors disabled:pointer-events-none disabled:opacity-50',
  {
    variants: {
      variant: {
        default: 'bg-accent text-accent-fg hover:opacity-90',
        outline: 'border border-border bg-surface text-fg hover:bg-surface-2',
        ghost: 'text-fg hover:bg-surface-2',
        danger: 'bg-danger text-danger-fg hover:opacity-90',
      },
      size: {
        sm: 'h-8 px-3 text-xs',
        md: 'h-10 px-4 text-sm',
        icon: 'h-9 w-9',
      },
    },
    defaultVariants: { variant: 'default', size: 'md' },
  },
)

export interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof variantes> {}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, ...props }, ref) => (
    <button ref={ref} className={cn(variantes({ variant, size }), className)} {...props} />
  ),
)
Button.displayName = 'Button'
