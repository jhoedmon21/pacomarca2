/**
 * Pestaña "Clasificación de hábitats": barra apilada de cobertura por clase
 * (0 Suelo, 1 Pasto bajo, 2 Pasto alto) construida con divs accesibles.
 */
import { useI18n } from '../../i18n'
import { useClassification } from '../../hooks/useClassification'
import { useAppStore } from '../../store/useAppStore'
import { formatNumber } from '../../lib/utils'
import { Card, CardContent } from '../ui/Card'
import { Skeleton } from '../ui/Skeleton'
import { ErrorState } from '../ui/StateMessages'

const ORDEN_CLASES = ['0', '1', '2'] as const

export function ClassificationTab() {
  const { t } = useI18n()
  const { lat, lon } = useAppStore()
  const clasificacion = useClassification(lat, lon)

  if (clasificacion.isError) {
    return <ErrorState onReintentar={() => clasificacion.refetch()} />
  }

  const datos = clasificacion.data

  return (
    <Card>
      <CardContent className="space-y-4 p-5">
        <div>
          <p className="text-sm font-bold">{t('clasif.cobertura')}</p>
          <p className="text-xs text-muted">{t('clasif.nota')}</p>
        </div>

        {clasificacion.isLoading ? (
          <>
            <Skeleton className="h-7 w-full rounded-full" aria-busy="true" />
            <div className="space-y-2">
              {ORDEN_CLASES.map((c) => (
                <Skeleton key={c} className="h-5 w-56" />
              ))}
            </div>
          </>
        ) : (
          <>
            {/* Barra apilada */}
            <div
              role="img"
              aria-label={ORDEN_CLASES.map(
                (c) => `${datos?.legend[c]?.label ?? c}: ${formatNumber(datos?.classification_map[c] ?? 0)}%`,
              ).join(', ')}
              className="flex h-7 w-full overflow-hidden rounded-full border border-border"
            >
              {ORDEN_CLASES.map((c) => (
                <div
                  key={c}
                  style={{
                    width: `${datos?.classification_map[c] ?? 0}%`,
                    backgroundColor: datos?.legend[c]?.color ?? '#94a3b8',
                  }}
                  title={`${datos?.legend[c]?.label}: ${formatNumber(datos?.classification_map[c] ?? 0)}%`}
                />
              ))}
            </div>

            {/* Leyenda */}
            <ul className="space-y-1.5">
              {ORDEN_CLASES.map((c) => (
                <li key={c} className="flex items-center gap-2 text-sm">
                  <span
                    aria-hidden="true"
                    className="h-3.5 w-3.5 shrink-0 rounded-sm border border-border"
                    style={{ backgroundColor: datos?.legend[c]?.color }}
                  />
                  <span className="min-w-0 flex-1 truncate">{datos?.legend[c]?.label}</span>
                  <span className="font-bold tabular-nums">
                    {formatNumber(datos?.classification_map[c] ?? 0)}%
                  </span>
                </li>
              ))}
            </ul>
            <p className="text-xs text-muted">{datos?.unit}</p>
          </>
        )}
      </CardContent>
    </Card>
  )
}
