/**
 * Pestañas accesibles (patrón WAI-ARIA Tabs):
 * - tablist con role, flechas izq/der para navegar, Home/End.
 * - Los paneles se identifican como panel-<id> y se enlazan con aria-controls.
 */
import { useRef, type KeyboardEvent } from 'react'
import type { LucideIcon } from 'lucide-react'
import { cn } from '../../lib/utils'

export interface TabItem {
  id: string
  label: string
  icono?: LucideIcon
}

interface TabsProps {
  items: TabItem[]
  valor: string
  onChange: (id: string) => void
  'aria-label': string
}

export function Tabs({ items, valor, onChange, ...aria }: TabsProps) {
  const botonesRef = useRef<(HTMLButtonElement | null)[]>([])

  const enfocar = (indice: number) => {
    const objetivo = botonesRef.current[indice]
    objetivo?.focus()
  }

  const alPulsarTecla = (e: KeyboardEvent<HTMLElement>, indice: number) => {
    const total = items.length
    let siguiente = -1
    if (e.key === 'ArrowRight') siguiente = (indice + 1) % total
    else if (e.key === 'ArrowLeft') siguiente = (indice - 1 + total) % total
    else if (e.key === 'Home') siguiente = 0
    else if (e.key === 'End') siguiente = total - 1
    if (siguiente >= 0) {
      e.preventDefault()
      onChange(items[siguiente].id)
      enfocar(siguiente)
    }
  }

  return (
    <div
      role="tablist"
      aria-label={aria['aria-label']}
      className="flex gap-1 overflow-x-auto border-b border-border"
      onKeyDown={(e) => {
        // Teclado global del grupo: aplica sobre la pestaña activa
        const indice = items.findIndex((i) => i.id === valor)
        alPulsarTecla(e, indice)
      }}
    >
      {items.map((item, indice) => {
        const activo = item.id === valor
        const Icono = item.icono
        return (
          <button
            key={item.id}
            ref={(nodo) => (botonesRef.current[indice] = nodo)}
            role="tab"
            id={`tab-${item.id}`}
            aria-selected={activo}
            aria-controls={`panel-${item.id}`}
            tabIndex={activo ? 0 : -1}
            onClick={() => onChange(item.id)}
            onKeyDown={(e) => alPulsarTecla(e, indice)}
            className={cn(
              'flex shrink-0 items-center gap-2 border-b-2 px-4 py-2.5 text-sm font-semibold transition-colors',
              activo
                ? 'border-accent text-accent'
                : 'border-transparent text-muted hover:border-border hover:text-fg',
            )}
          >
            {Icono && <Icono aria-hidden="true" className="h-4 w-4" />}
            {item.label}
          </button>
        )
      })}
    </div>
  )
}

/** Panel de contenido de una pestaña (se oculta con display, no se desmonta,
 * para conservar el estado interno de gráficos). */
export function TabPanel({
  id,
  activo,
  children,
}: {
  id: string
  activo: boolean
  children: React.ReactNode
}) {
  return (
    <div
      role="tabpanel"
      id={`panel-${id}`}
      aria-labelledby={`tab-${id}`}
      hidden={!activo}
      tabIndex={0}
      className="pt-4 focus-visible:outline-none"
    >
      {children}
    </div>
  )
}
