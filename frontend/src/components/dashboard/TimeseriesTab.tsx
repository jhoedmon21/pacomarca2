/**
 * Pestaña "Dinámica temporal": gráfico de área (Recharts) de la serie del
 * índice activo, con exportación a CSV y PNG (100 % en el cliente).
 */
import { useRef } from 'react'
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { Download, ImageDown } from 'lucide-react'
import { useI18n } from '../../i18n'
import { useTimeseries } from '../../hooks/useTimeseries'
import { useCrosscheck } from '../../hooks/useCrosscheck'
import { useThemeColors } from '../../hooks/useThemeColors'
import { useAppStore } from '../../store/useAppStore'
import { exportarCsv, exportarPngDesdeSvg, formatNumber } from '../../lib/utils'
import { Button } from '../ui/Button'
import { Skeleton } from '../ui/Skeleton'
import { EmptyState, ErrorState } from '../ui/StateMessages'
import { indiceDeCapa } from './KpiGrid'
import type { TimeseriesPoint } from '../../types'

interface TooltipProps {
  active?: boolean
  payload?: { payload: TimeseriesPoint }[]
  label?: string
}

function TooltipSerie({ active, payload, label }: TooltipProps) {
  const punto = payload?.[0]?.payload
  if (!active || !punto) return null
  return (
    <div className="rounded-lg border border-border bg-surface/95 px-3 py-2 text-xs shadow-card">
      <p className="font-bold">{label}</p>
      <p className="text-muted">
        {formatNumber(punto.value)}
        {punto.biomass != null && ` · ${formatNumber(punto.biomass)} Kg/Ha`}
      </p>
    </div>
  )
}

export function TimeseriesTab() {
  const { t } = useI18n()
  const { lat, lon, years, layer } = useAppStore()
  const indice = indiceDeCapa(layer)
  const serie = useTimeseries(lat, lon, years, indice)
  const crosscheck = useCrosscheck(lat, lon)
  const colores = useThemeColors()
  const graficoRef = useRef<HTMLDivElement>(null)

  const datos = serie.data?.data ?? []
  const claveY = indice === 'biomasa' ? 'biomass' : 'value'
  const etiquetaY = indice === 'biomasa' ? 'Biomasa (Kg/Ha)' : indice.toUpperCase()

  const descargarCsv = () => {
    exportarCsv(
      datos.map((p) => ({
        fecha: p.date,
        valor: p.value,
        biomasa_kg_ha: p.biomass ?? '',
      })),
      `pacomarca_${indice}_${lat}_${lon}_${years}a.csv`,
    )
  }

  const descargarPng = () => {
    if (graficoRef.current) {
      const canales = getComputedStyle(document.documentElement).getPropertyValue('--surface').trim()
      const fondo = canales ? `rgb(${canales})` : '#ffffff'
      exportarPngDesdeSvg(graficoRef.current, `pacomarca_${indice}_${lat}_${lon}.png`, fondo)
    }
  }

  return (
    <div>
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <div className="min-w-0 text-xs text-muted">
          <p>
            {etiquetaY} · {serie.data?.source}
          </p>
          {crosscheck.data && (
            <p className="mt-0.5">
              {t('serie.concordancia')}: MODIS {formatNumber(crosscheck.data.modis_ndvi)} vs S2{' '}
              {formatNumber(crosscheck.data.s2_ndvi)} (Δ{' '}
              {formatNumber(crosscheck.data.diferencia)})
            </p>
          )}
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={descargarCsv} disabled={datos.length === 0}>
            <Download aria-hidden="true" className="h-3.5 w-3.5" />
            CSV
          </Button>
          <Button variant="outline" size="sm" onClick={descargarPng} disabled={datos.length === 0}>
            <ImageDown aria-hidden="true" className="h-3.5 w-3.5" />
            PNG
          </Button>
        </div>
      </div>

      {serie.isError ? (
        <ErrorState onReintentar={() => serie.refetch()} />
      ) : serie.isLoading ? (
        <div className="space-y-2" aria-busy="true" aria-label={t('common.cargando')}>
          <Skeleton className="h-8 w-full" />
          <Skeleton className="h-[320px] w-full" />
        </div>
      ) : datos.length === 0 ? (
        <EmptyState />
      ) : (
        <div ref={graficoRef} className="h-[340px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={datos} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="gradiente-serie" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={colores.accent} stopOpacity={0.28} />
                  <stop offset="100%" stopColor={colores.accent} stopOpacity={0.02} />
                </linearGradient>
              </defs>
              <CartesianGrid stroke={colores.border} strokeDasharray="3 3" vertical={false} />
              <XAxis
                dataKey="date"
                tick={{ fontSize: 11, fill: colores.textSecondary }}
                tickFormatter={(v: string) => v.slice(0, 4)}
                minTickGap={32}
                stroke={colores.border}
              />
              <YAxis
                tick={{ fontSize: 11, fill: colores.textSecondary }}
                stroke={colores.border}
                width={56}
              />
              <Tooltip content={<TooltipSerie />} cursor={{ stroke: colores.accent, strokeOpacity: 0.4 }} />
              <Area
                type="monotone"
                dataKey={claveY}
                name={etiquetaY}
                stroke={colores.accent}
                strokeWidth={2}
                fill="url(#gradiente-serie)"
                isAnimationActive={false}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  )
}
