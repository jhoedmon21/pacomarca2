/**
 * Tarjetas KPI con indicadores de tendencia (↑↓→):
 * promedio histórico, último valor, anomalía vs. histórico y tendencia anual.
 */
import { Activity, ArrowRight, ArrowUp, ChartColumn, Sigma } from 'lucide-react'
import { useI18n } from '../../i18n'
import { useStats } from '../../hooks/useStats'
import { useTimeseries } from '../../hooks/useTimeseries'
import { useAppStore } from '../../store/useAppStore'
import { formatNumber, cn } from '../../lib/utils'
import { Card, CardContent } from '../ui/Card'
import { Skeleton } from '../ui/Skeleton'
import { ErrorState } from '../ui/StateMessages'
import type { IndexId } from '../../types'
import type { ReactNode } from 'react'

/** Índice de serie temporal asociado a la capa activa (como en la app original). */
export function indiceDeCapa(layer: string): IndexId {
  if (layer === 'biomasa') return 'biomasa'
  if (layer === 'evi') return 'evi'
  return 'ndvi'
}

function FlechaTendencia({
  valor,
  positivoEsBueno = true,
  className = 'h-4 w-4',
}: {
  valor: number
  positivoEsBueno?: boolean
  className?: string
}) {
  if (Math.abs(valor) < 0.005) {
    return <ArrowRight aria-hidden="true" className={cn('text-muted', className)} />
  }
  const sube = valor > 0
  const bueno = positivoEsBueno ? sube : !sube
  return (
    <ArrowUp
      aria-hidden="true"
      className={cn(className, sube ? '' : 'rotate-180', bueno ? 'text-success' : 'text-danger')}
    />
  )
}

/** Tarjeta KPI compacta: icono + etiqueta (envuelve, sin truncar) + valor. */
function KpiCard({
  titulo,
  valor,
  unidad,
  icono,
  extra,
  cargando,
}: {
  titulo: string
  valor: string
  unidad?: string
  icono: ReactNode
  extra?: ReactNode
  cargando?: boolean
}) {
  return (
    <Card className="min-w-0">
      <CardContent className="flex h-full items-center gap-3 p-4">
        <span
          aria-hidden="true"
          className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-accent/10 text-accent"
        >
          {icono}
        </span>
        <div className="min-w-0 flex-1">
          <p className="text-[11px] font-bold uppercase leading-tight tracking-wider text-muted">
            {titulo}
          </p>
          {cargando ? (
            <Skeleton className="mt-1.5 h-6 w-24" />
          ) : (
            <p className="mt-0.5 truncate text-xl font-extrabold tabular-nums tracking-tight">
              {valor}
              {unidad && <span className="ml-1 text-xs font-semibold text-muted">{unidad}</span>}
            </p>
          )}
          {extra && <p className="mt-0.5 truncate text-[11px] text-muted">{extra}</p>}
        </div>
      </CardContent>
    </Card>
  )
}

export function KpiGrid() {
  const { t } = useI18n()
  const { lat, lon, years, layer } = useAppStore()

  const stats = useStats(lat, lon, years, layer)
  const indice = indiceDeCapa(layer)
  const serie = useTimeseries(lat, lon, years, indice)

  if (stats.isError) {
    return (
      <Card>
        <ErrorState onReintentar={() => stats.refetch()} />
      </Card>
    )
  }

  const datos = stats.data
  const ultimo = serie.data?.data?.length
    ? serie.data.data[serie.data.data.length - 1]
    : undefined
  const valorUltimo =
    indice === 'biomasa' ? (ultimo?.biomass ?? null) : (ultimo?.value ?? null)

  const anomalia = datos?.anomaly_percent ?? 0
  const cargando = stats.isLoading

  return (
    <div
      className="grid h-full auto-rows-fr grid-cols-1 gap-3"
      aria-busy={cargando}
    >
      <KpiCard
        titulo={t('kpi.promedio')}
        valor={formatNumber(datos?.mean)}
        unidad={datos?.unit}
        icono={<Sigma aria-hidden="true" className="h-5 w-5" />}
        cargando={cargando}
      />
      <KpiCard
        titulo={t('kpi.ultimo')}
        valor={formatNumber(valorUltimo)}
        unidad={serie.data?.unit}
        icono={<ChartColumn aria-hidden="true" className="h-5 w-5" />}
        extra={ultimo ? <span>{ultimo.date}</span> : undefined}
        cargando={serie.isLoading}
      />
      <KpiCard
        titulo={t('kpi.anomalia')}
        valor={datos ? `${anomalia > 0 ? '+' : ''}${formatNumber(anomalia)}%` : '--'}
        icono={<FlechaTendencia valor={anomalia} className="h-5 w-5" />}
        extra={<span>{t('alerta.umbral')}</span>}
        cargando={cargando}
      />
      <KpiCard
        titulo={t('kpi.tendencia')}
        valor={datos ? `${datos.trend > 0 ? '+' : ''}${formatNumber(datos.trend)}` : '--'}
        unidad={datos ? `${datos.unit}${t('kpi.unidadAnio')}` : undefined}
        icono={<Activity aria-hidden="true" className="h-5 w-5" />}
        extra={<FlechaTendencia valor={datos?.trend ?? 0} />}
        cargando={cargando}
      />
    </div>
  )
}
