/**
 * Composición del dashboard: mapa + KPIs a la par, panel de análisis debajo.
 * Reemplaza 1:1 la vista principal de la app de Streamlit original.
 */
import { useI18n } from './i18n'
import { AppShell } from './components/layout/AppShell'
import { MapView } from './components/dashboard/MapView'
import { KpiGrid } from './components/dashboard/KpiGrid'
import { AnalysisPanel } from './components/dashboard/AnalysisPanel'

export default function App() {
  const { t } = useI18n()

  return (
    <AppShell>
      <section aria-label={t('app.titulo')} className="grid gap-4 lg:grid-cols-[minmax(0,3fr)_minmax(0,1fr)]">
        <MapView />
        <div className="min-w-0">
          <KpiGrid />
        </div>
      </section>

      <section aria-labelledby="titulo-analisis" className="space-y-3">
        <div className="flex items-start gap-3">
          <span aria-hidden="true" className="mt-1.5 h-6 w-1 shrink-0 rounded-full bg-accent" />
          <div>
            <h2
              id="titulo-analisis"
              className="font-display text-xl font-semibold leading-tight tracking-tight"
            >
              {t('section.analisis')}
            </h2>
            <p className="text-sm text-muted">{t('sidebar.mapHint')}</p>
          </div>
        </div>
        <AnalysisPanel />
      </section>
    </AppShell>
  )
}
