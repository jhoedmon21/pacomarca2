/**
 * Select nativo estilizado: accesible por defecto (teclado + lector de pantalla).
 */
import { forwardRef, type SelectHTMLAttributes } from 'react'
import { ChevronDown } from 'lucide-react'
import { cn } from '../../lib/utils'

export interface Opcion {
  value: string
  label: string
}

export interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: string
  opciones: Opcion[]
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(
  ({ label, opciones, className, id, ...props }, ref) => {
    const idCampo = id ?? props.name
    return (
      <div className="w-full">
        {label && (
          <label htmlFor={idCampo} className="mb-1 block text-xs font-semibold text-muted">
            {label}
          </label>
        )}
        <div className="relative">
          <select
            ref={ref}
            id={idCampo}
            className={cn(
              'h-10 w-full appearance-none rounded-lg border border-border bg-surface px-3 pr-9 text-sm text-fg',
              'focus:border-accent focus:outline-none focus-visible:outline-none',
              className,
            )}
            {...props}
          >
            {opciones.map((op) => (
              <option key={op.value} value={op.value}>
                {op.label}
              </option>
            ))}
          </select>
          <ChevronDown
            aria-hidden="true"
            className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted"
          />
        </div>
      </div>
    )
  },
)
Select.displayName = 'Select'
