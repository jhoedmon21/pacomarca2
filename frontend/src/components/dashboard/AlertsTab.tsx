/**
 * Pestaña "Monitor de alertas": semáforo según la anomalía del último valor
 * frente al promedio histórico (umbrales ±15 %) + historial persistido en
 * base de datos (registrado por el job diario).
 */
import { History, Scale, Sprout, Siren } from 'lucide-react'
import { useI18n } from '../../i18n'
import { useStats } from '../../hooks/useStats'
import { useAlertas } from '../../hooks/useAlertas'
import { useAppStore } from '../../store/useAppStore'
import { formatNumber } from '../../lib/utils'
import { Badge } from '../ui/Badge'
import { Card, CardContent } from '../ui/Card'
import { Skeleton } from '../ui/Skeleton'
import { ErrorState } from '../ui/StateMessages'

const TONO_SEVERIDAD = {
  critica: 'danger',
  alerta: 'accent',
  info: 'success',
} as const

/** Historial de alertas registradas en la base de datos (job diario). */
function HistorialAlertas() {
  const { t } = useI18n()
  const alertas = useAlertas(20)

  return (
    <Card>
      <CardContent className="p-5">
        <p className="mb-3 flex items-center gap-2 text-[11px] font-bold uppercase tracking-wider text-muted">
          <History aria-hidden="true" className="h-3.5 w-3.5" />
          {t('alerta.historial')}
        </p>
        {alertas.isLoading ? (
          <div className="space-y-2">
            <Skeleton className="h-9 w-full" />
            <Skeleton className="h-9 w-full" />
          </div>
        ) : alertas.isError ? (
          <p className="text-xs text-muted">{t('puntos.errorCargar')}</p>
        ) : (alertas.data?.length ?? 0) === 0 ? (
          <p className="text-xs text-muted">{t('alerta.historialVacio')}</p>
        ) : (
          <ul className="divide-y divide-border">
            {alertas.data?.map((alerta) => (
              <li key={alerta.id} className="flex items-center gap-3 py-2">
                <Badge variant={TONO_SEVERIDAD[alerta.severidad] ?? 'accent'}>
                  {alerta.anomalia_pct > 0 ? '+' : ''}
                  {formatNumber(alerta.anomalia_pct)}%
                </Badge>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-xs font-semibold">
                    {alerta.mensaje ?? t('alerta.registro')}
                  </p>
                  <p className="text-[10px] text-muted">
                    {new Date(alerta.creado_en).toLocaleString()} · {alerta.lat.toFixed(4)},{' '}
                    {alerta.lon.toFixed(4)}
                  </p>
                </div>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  )
}

export function AlertsTab() {
  const { t } = useI18n()
  const { lat, lon, years, layer } = useAppStore()
  const stats = useStats(lat, lon, years, layer)

  if (stats.isError) {
    return <ErrorState onReintentar={() => stats.refetch()} />
  }

  const datos = stats.data
  const anomalia = datos?.anomaly_percent ?? 0

  type Estado = { icono: typeof Siren; titulo: string; descripcion: string; tono: string; badge: 'danger' | 'success' | 'accent' }
  let estado: Estado
  if (anomalia < -15) {
    estado = {
      icono: Siren,
      titulo: t('alerta.degradacion'),
      descripcion: t('alerta.degradacion.desc'),
      tono: 'bg-danger/10 text-danger',
      badge: 'danger',
    }
  } else if (anomalia > 15) {
    estado = {
      icono: Sprout,
      titulo: t('alerta.favorable'),
      descripcion: t('alerta.favorable.desc'),
      tono: 'bg-success/10 text-success',
      badge: 'success',
    }
  } else {
    estado = {
      icono: Scale,
      titulo: t('alerta.estable'),
      descripcion: t('alerta.estable.desc'),
      tono: 'bg-accent/10 text-accent',
      badge: 'accent',
    }
  }

  const Icono = estado.icono

  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-[2fr_1fr]">
      <Card>
        <CardContent className="flex items-center gap-4 p-6">
          {stats.isLoading ? (
            <>
              <Skeleton className="h-14 w-14 shrink-0 rounded-full" />
              <div className="flex-1 space-y-2">
                <Skeleton className="h-5 w-48" />
                <Skeleton className="h-4 w-64" />
              </div>
            </>
          ) : (
            <>
              <span className={`flex h-14 w-14 shrink-0 items-center justify-center rounded-full ${estado.tono}`}>
                <Icono aria-hidden="true" className="h-7 w-7" />
              </span>
              <div className="min-w-0">
                <p className="text-base font-extrabold">
                  {estado.titulo}{' '}
                  <Badge variant={estado.badge}>
                    {anomalia > 0 ? '+' : ''}
                    {formatNumber(anomalia)}%
                  </Badge>
                </p>
                <p className="mt-1 text-sm text-muted">{estado.descripcion}</p>
                <p className="mt-2 text-xs text-muted">{t('alerta.umbral')}</p>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardContent className="flex h-full flex-col justify-center p-6">
          <p className="text-[11px] font-bold uppercase tracking-wider text-muted">
            {t('alerta.promedioHistorico')}
          </p>
          {stats.isLoading ? (
            <Skeleton className="mt-2 h-10 w-28" />
          ) : (
            <>
              <p className="mt-1 text-3xl font-extrabold tabular-nums">
                {formatNumber(datos?.mean)}
                <span className="ml-1 text-sm font-semibold text-muted">{datos?.unit}</span>
              </p>
              <p className="mt-2 text-xs text-muted">
                {t('alerta.vs')}: {anomalia > 0 ? '+' : ''}
                {formatNumber(anomalia)}% · {datos?.data_count} {t('common.anios') === 'years' ? 'records' : 'registros'}
              </p>
            </>
          )}
        </CardContent>
      </Card>
      </div>

      <HistorialAlertas />
    </div>
  )
}
