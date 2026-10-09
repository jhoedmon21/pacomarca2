/**
 * Leyenda de color de la capa activa (superpuesta al mapa).
 * Para capas sin paleta (radar dB) usa una rampa gris.
 */
import { useI18n } from '../../i18n'
import { formatNumber } from '../../lib/utils'

interface MapLegendProps {
  titulo: string
  paleta: string[]
  minVal: number
  maxVal: number
  unidad: string
}

export function MapLegend({ titulo, paleta, minVal, maxVal, unidad }: MapLegendProps) {
  const { t } = useI18n()

  const colores =
    paleta.length > 0 ? paleta : ['#1a1a1a', '#4d4d4d', '#808080', '#b3b3b3', '#e6e6e6']
  const degradado = `linear-gradient(to right, ${colores.join(', ')})`
  const descripcion = `${t('map.leyenda')} ${titulo}: de ${formatNumber(minVal)} a ${formatNumber(maxVal)} ${unidad}`

  return (
    <div className="absolute bottom-3 left-3 z-10 w-52 rounded-lg border border-border bg-surface/95 p-3 shadow-card backdrop-blur">
      <p className="text-[10px] font-bold uppercase tracking-widest text-muted">{t('map.leyenda')}</p>
      <p className="mb-2 truncate text-xs font-bold" title={titulo}>
        {titulo}
      </p>
      <div
        role="img"
        aria-label={descripcion}
        className="h-3 w-full rounded-full border border-border"
        style={{ background: degradado }}
      />
      <div className="mt-1 flex justify-between text-[10px] font-semibold text-muted">
        <span>{formatNumber(minVal)}</span>
        <span>{unidad}</span>
        <span>{formatNumber(maxVal)}</span>
      </div>
    </div>
  )
}
