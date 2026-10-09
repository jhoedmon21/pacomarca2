/**
 * Pestaña "Comparador de periodos": promedio anual de la serie en dos años
 * elegidos (A vs B), con diferencia porcentual. Usa la misma serie ya cargada.
 */
import { useMemo, useState } from 'react'
import { ArrowLeftRight } from 'lucide-react'
import { useI18n } from '../../i18n'
import { useTimeseries } from '../../hooks/useTimeseries'
import { useAppStore } from '../../store/useAppStore'
import { formatNumber } from '../../lib/utils'
import { Badge } from '../ui/Badge'
import { Card, CardContent } from '../ui/Card'
import { Skeleton } from '../ui/Skeleton'
import { EmptyState, ErrorState } from '../ui/StateMessages'
import { Select } from '../ui/Select'
import { indiceDeCapa } from './KpiGrid'

export function ComparisonTab() {
  const { t } = useI18n()
  const { lat, lon, years, layer } = useAppStore()
  const indice = indiceDeCapa(layer)
  const serie = useTimeseries(lat, lon, years, indice)

  const aniosDisponibles = useMemo(() => {
    const unicos = [...new Set((serie.data?.data ?? []).map((p) => p.date.slice(0, 4)))]
    return unicos.sort()
  }, [serie.data])

  const porDefectoA = aniosDisponibles[0] ?? ''
  const porDefectoB = aniosDisponibles[aniosDisponibles.length - 1] ?? ''
  const [anioA, setAnioA] = useState<string | null>(null)
  const [anioB, setAnioB] = useState<string | null>(null)
  const seleccionA = anioA ?? porDefectoA
  const seleccionB = anioB ?? porDefectoB

  const promedios = useMemo(() => {
    const clave = indice === 'biomasa' ? 'biomass' : 'value'
    const promedio = (anio: string) => {
      const puntos = (serie.data?.data ?? []).filter((p) => p.date.startsWith(anio))
      if (puntos.length === 0) return null
      const suma = puntos.reduce((acc, p) => acc + (p[clave] ?? 0), 0)
      return suma / puntos.length
    }
    return { A: promedio(seleccionA), B: promedio(seleccionB) }
  }, [serie.data, indice, seleccionA, seleccionB])

  if (serie.isError) {
    return <ErrorState onReintentar={() => serie.refetch()} />
  }
  if (serie.isLoading) {
    return (
      <Card>
        <CardContent className="space-y-3" aria-busy="true">
          <Skeleton className="h-10 w-72" />
          <Skeleton className="h-16 w-full" />
          <Skeleton className="h-10 w-full" />
        </CardContent>
      </Card>
    )
  }
  if (aniosDisponibles.length === 0) {
    return <EmptyState />
  }

  const opciones = aniosDisponibles.map((a) => ({ value: a, label: a }))
  const diferencia =
    promedios.A && promedios.B && promedios.A !== 0
      ? ((promedios.B - promedios.A) / promedios.A) * 100
      : null
  const unidad = serie.data?.unit ?? ''

  return (
    <Card>
      <CardContent className="space-y-4 p-5">
        <p className="text-xs text-muted">{t('comparador.nota')}</p>

        <div className="grid gap-3 sm:grid-cols-2">
          <Select
            label={`${t('comparador.periodoA')} (año)`}
            name="periodo-a"
            opciones={opciones}
            value={seleccionA}
            onChange={(e) => setAnioA(e.target.value)}
          />
          <Select
            label={`${t('comparador.periodoB')} (año)`}
            name="periodo-b"
            opciones={opciones}
            value={seleccionB}
            onChange={(e) => setAnioB(e.target.value)}
          />
        </div>

        <div className="grid gap-3 sm:grid-cols-3">
          {[
            { titulo: `${t('comparador.periodoA')} · ${seleccionA}`, valor: promedios.A },
            { titulo: `${t('comparador.periodoB')} · ${seleccionB}`, valor: promedios.B },
          ].map((caja) => (
            <div key={caja.titulo} className="rounded-lg border border-border bg-surface-2 p-3">
              <p className="text-[11px] font-bold uppercase tracking-wider text-muted">{caja.titulo}</p>
              <p className="mt-1 text-xl font-extrabold tabular-nums">
                {formatNumber(caja.valor)}
                <span className="ml-1 text-xs font-semibold text-muted">{unidad}</span>
              </p>
            </div>
          ))}
          <div className="rounded-lg border border-border bg-surface-2 p-3">
            <p className="flex items-center gap-1 text-[11px] font-bold uppercase tracking-wider text-muted">
              <ArrowLeftRight aria-hidden="true" className="h-3 w-3" />
              {t('comparador.diferencia')} B vs A
            </p>
            <p className="mt-1">
              {diferencia === null ? (
                '--'
              ) : (
                <Badge variant={diferencia >= 0 ? 'success' : 'danger'}>
                  {diferencia >= 0 ? '+' : ''}
                  {formatNumber(diferencia)}%
                </Badge>
              )}
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
