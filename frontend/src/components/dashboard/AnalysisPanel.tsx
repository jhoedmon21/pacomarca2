/**
 * Panel de análisis: pestañas (serie temporal, alertas, clasificación,
 * comparador) con persistencia de la pestaña activa en sesión.
 */
import { useState } from 'react'
import { BarChart3, GitCompareArrows, Layers, Siren } from 'lucide-react'
import { useI18n } from '../../i18n'
import { Tabs, TabPanel, type TabItem } from '../ui/Tabs'
import { Card } from '../ui/Card'
import { TimeseriesTab } from './TimeseriesTab'
import { AlertsTab } from './AlertsTab'
import { ClassificationTab } from './ClassificationTab'
import { ComparisonTab } from './ComparisonTab'

export function AnalysisPanel() {
  const { t } = useI18n()
  const [activa, setActiva] = useState('serie')

  const items: TabItem[] = [
    { id: 'serie', label: t('tabs.serie'), icono: BarChart3 },
    { id: 'alertas', label: t('tabs.alertas'), icono: Siren },
    { id: 'clasificacion', label: t('tabs.clasificacion'), icono: Layers },
    { id: 'comparador', label: t('tabs.comparador'), icono: GitCompareArrows },
  ]

  return (
    <Card className="p-4 sm:p-5">
      <Tabs items={items} valor={activa} onChange={setActiva} aria-label={t('section.analisis')} />
      <TabPanel id="serie" activo={activa === 'serie'}>
        <TimeseriesTab />
      </TabPanel>
      <TabPanel id="alertas" activo={activa === 'alertas'}>
        <AlertsTab />
      </TabPanel>
      <TabPanel id="clasificacion" activo={activa === 'clasificacion'}>
        <ClassificationTab />
      </TabPanel>
      <TabPanel id="comparador" activo={activa === 'comparador'}>
        <ComparisonTab />
      </TabPanel>
    </Card>
  )
}
