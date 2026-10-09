/**
 * Slider de rango nativo estilizado.
 * El valor visual se actualiza al arrastrar, pero solo se confirma
 * (onCommit) al soltar, para no disparar consultas a GEE en cada píxel.
 */
import { useRef, useState, type KeyboardEvent } from 'react'

export interface SliderProps {
  label: string
  valor: number
  min: number
  max: number
  paso?: number
  formato?: (v: number) => string
  onCommit: (valor: number) => void
  className?: string
}

export function Slider({ label, valor, min, max, paso = 1, formato, onCommit, className }: SliderProps) {
  const [local, setLocal] = useState(valor)
  const ultimoConfirmado = useRef(valor)

  // Si el valor externo cambia (por persistencia), sincronizar
  if (valor !== ultimoConfirmado.current) {
    ultimoConfirmado.current = valor
    setLocal(valor)
  }

  const confirmar = () => {
    if (local !== ultimoConfirmado.current) {
      ultimoConfirmado.current = local
      onCommit(local)
    }
  }

  const alSoltarPuntero = () => confirmar()
  const alSoltarTecla = (e: KeyboardEvent<HTMLInputElement>) => {
    if (['ArrowLeft', 'ArrowRight', 'Home', 'End', 'PageUp', 'PageDown'].includes(e.key)) {
      // el valor cambia con la tecla; confirmar en el siguiente tick
      setTimeout(confirmar, 0)
    }
  }

  return (
    <div className={className}>
      <div className="mb-1 flex items-baseline justify-between">
        <span className="text-xs font-semibold text-muted">{label}</span>
        <span className="text-xs font-bold text-fg" aria-live="polite">
          {formato ? formato(local) : local}
        </span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={paso}
        value={local}
        aria-label={label}
        onChange={(e) => setLocal(Number(e.target.value))}
        onPointerUp={alSoltarPuntero}
        onBlur={confirmar}
        onKeyUp={alSoltarTecla}
        className="h-2 w-full cursor-pointer appearance-none rounded-full bg-surface-2"
        style={{ accentColor: 'rgb(var(--accent))' }}
      />
    </div>
  )
}
