/**
 * Panel lateral colapsable:
 * - Escritorio (lg+): fijo; plegado muestra solo el riel de iconos.
 * - Móvil/tablet: off-canvas con fondo oscuro cerrable.
 * Controles: coordenadas del punto (con validación), capa activa y años.
 */
import { useEffect, useState, type KeyboardEvent } from 'react'
import {
  Droplets,
  Info,
  Layers,
  MapPin,
  Radar,
  RotateCcw,
  Satellite,
  Sprout,
  Sun,
  Timer,
  X,
} from 'lucide-react'
import { useI18n, type I18nKey } from '../../i18n'
import { useAppStore } from '../../store/useAppStore'
import { SavedPoints } from './SavedPoints'
import { Button } from '../ui/Button'
import { Slider } from '../ui/Slider'
import { cn } from '../../lib/utils'
import type { LayerId } from '../../types'

const CAPAS: { id: LayerId; clave: I18nKey; icono: typeof Sprout }[] = [
  { id: 'biomasa', clave: 'layer.biomasa', icono: Sprout },
  { id: 'clasificacion', clave: 'layer.clasificacion', icono: Layers },
  { id: 'radar_s1', clave: 'layer.radar', icono: Radar },
  { id: 'ndvi', clave: 'layer.ndvi', icono: Satellite },
  { id: 'evi', clave: 'layer.evi', icono: Satellite },
  { id: 'savi', clave: 'layer.savi', icono: Sun },
  { id: 'ndwi', clave: 'layer.ndwi', icono: Droplets },
]

/** Entradas de lat/lon con commit al salir/Enter y validación de rango. */
function EntradasCoordenadas() {
  const { t } = useI18n()
  const { lat, lon, setPunto } = useAppStore()
  const [textoLat, setTextoLat] = useState(String(lat))
  const [textoLon, setTextoLon] = useState(String(lon))

  // Sincronizar cuando el punto cambia desde el mapa
  useEffect(() => {
    setTextoLat(String(lat))
    setTextoLon(String(lon))
  }, [lat, lon])

  const confirmar = () => {
    const nuevaLat = parseFloat(textoLat)
    const nuevaLon = parseFloat(textoLon)
    const latOk = !Number.isNaN(nuevaLat) && nuevaLat >= -90 && nuevaLat <= 90
    const lonOk = !Number.isNaN(nuevaLon) && nuevaLon >= -180 && nuevaLon <= 180
    if (!latOk) setTextoLat(String(lat)) // revertir si es inválida
    if (!lonOk) setTextoLon(String(lon))
    if (latOk && lonOk) setPunto(nuevaLat, nuevaLon)
  }

  const alPulsarTecla = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') confirmar()
  }

  return (
    <div className="space-y-3">
      <div>
        <label htmlFor="entrada-lat" className="mb-1 block text-xs font-semibold text-muted">
          {t('sidebar.lat')}
        </label>
        <input
          id="entrada-lat"
          type="number"
          step="0.00001"
          value={textoLat}
          onChange={(e) => setTextoLat(e.target.value)}
          onBlur={confirmar}
          onKeyDown={alPulsarTecla}
          aria-describedby="ayuda-lat"
          className="h-9 w-full rounded-lg border border-border bg-surface px-2.5 text-sm tabular-nums"
        />
        <p id="ayuda-lat" className="mt-1 text-[10px] text-muted">-90 … 90</p>
      </div>
      <div>
        <label htmlFor="entrada-lon" className="mb-1 block text-xs font-semibold text-muted">
          {t('sidebar.lon')}
        </label>
        <input
          id="entrada-lon"
          type="number"
          step="0.00001"
          value={textoLon}
          onChange={(e) => setTextoLon(e.target.value)}
          onBlur={confirmar}
          onKeyDown={alPulsarTecla}
          aria-describedby="ayuda-lon"
          className="h-9 w-full rounded-lg border border-border bg-surface px-2.5 text-sm tabular-nums"
        />
        <p id="ayuda-lon" className="mt-1 text-[10px] text-muted">-180 … 180</p>
      </div>
      <Button variant="outline" size="sm" className="w-full" onClick={() => setPunto(-14.85, -70.92)}>
        <RotateCcw aria-hidden="true" className="h-3.5 w-3.5" />
        {t('sidebar.predeterminado')}
      </Button>
    </div>
  )
}

/** Selector de capa tipo grupo de radio (navegable con flechas). */
function SelectorCapas() {
  const { t } = useI18n()
  const { layer, setCapa } = useAppStore()

  const alPulsarTecla = (e: KeyboardEvent<HTMLDivElement>) => {
    if (e.key !== 'ArrowDown' && e.key !== 'ArrowUp') return
    e.preventDefault()
    const indice = CAPAS.findIndex((c) => c.id === layer)
    const delta = e.key === 'ArrowDown' ? 1 : -1
    setCapa(CAPAS[(indice + delta + CAPAS.length) % CAPAS.length].id)
  }

  return (
    <div role="radiogroup" aria-label={t('sidebar.capas')} onKeyDown={alPulsarTecla} className="space-y-1">
      {CAPAS.map((capa) => {
        const activa = capa.id === layer
        const Icono = capa.icono
        return (
          <button
            key={capa.id}
            type="button"
            role="radio"
            aria-checked={activa}
            tabIndex={activa ? 0 : -1}
            onClick={() => setCapa(capa.id)}
            className={cn(
              'flex w-full items-center gap-3 rounded-lg px-3 py-2 text-left text-sm font-semibold transition-colors',
              activa ? 'bg-accent/10 text-accent' : 'text-fg hover:bg-surface-2',
            )}
          >
            <Icono aria-hidden="true" className="h-4 w-4 shrink-0" />
            <span className="min-w-0">
              {t(capa.clave)}
              <span className="block text-[11px] font-normal text-muted">
                {t(`${capa.clave}.desc` as I18nKey)}
              </span>
            </span>
          </button>
        )
      })}
    </div>
  )
}

export function Sidebar() {
  const { t } = useI18n()
  const { sidebarAbierto, alternarSidebar, years, setAnios, layer, setCapa } = useAppStore()

  return (
    <>
      {/* Fondo móvil */}
      {sidebarAbierto && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={alternarSidebar}
          aria-hidden="true"
        />
      )}

      <aside
        aria-label={t('sidebar.titulo')}
        className={cn(
          'fixed inset-y-0 left-0 z-50 flex w-64 flex-col border-r border-border bg-surface transition-transform duration-200',
          sidebarAbierto ? 'translate-x-0' : '-translate-x-full lg:translate-x-0 lg:w-16',
        )}
      >
        {/* Marca */}
        <div className="flex h-16 items-center gap-2 border-b border-border px-4">
          <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-accent text-accent-fg">
            <Satellite aria-hidden="true" className="h-5 w-5" />
          </span>
          <div className={cn('min-w-0', !sidebarAbierto && 'lg:hidden')}>
            <p className="truncate text-sm font-extrabold tracking-wide">{t('sidebar.titulo')}</p>
            <p className="truncate text-[10px] font-semibold text-muted">{t('sidebar.subtitulo')}</p>
          </div>
          <button
            type="button"
            onClick={alternarSidebar}
            aria-label={t('header.panel')}
            className="ml-auto flex h-8 w-8 items-center justify-center rounded-lg text-muted hover:bg-surface-2 hover:text-fg lg:hidden"
          >
            <X aria-hidden="true" className="h-4 w-4" />
          </button>
        </div>

        {/* Contenido expandido (oculto cuando está plegado en escritorio) */}
        <div className={cn('flex-1 space-y-6 overflow-y-auto p-4', !sidebarAbierto && 'lg:hidden')}>
          <section aria-labelledby="titulo-punto">
            <h2 id="titulo-punto" className="mb-2 flex items-center gap-1.5 text-[10px] font-bold tracking-widest text-muted">
              <MapPin aria-hidden="true" className="h-3 w-3" /> {t('sidebar.punto')}
            </h2>
            <EntradasCoordenadas />
          </section>

          <section aria-labelledby="titulo-capas">
            <h2 id="titulo-capas" className="mb-2 flex items-center gap-1.5 text-[10px] font-bold tracking-widest text-muted">
              <Layers aria-hidden="true" className="h-3 w-3" /> {t('sidebar.capas')}
            </h2>
            <SelectorCapas />
          </section>

          <section aria-labelledby="titulo-serie">
            <h2 id="titulo-serie" className="mb-2 flex items-center gap-1.5 text-[10px] font-bold tracking-widest text-muted">
              <Timer aria-hidden="true" className="h-3 w-3" /> {t('sidebar.serie')}
            </h2>
            <Slider
              label={t('sidebar.anios')}
              valor={years}
              min={5}
              max={26}
              onCommit={setAnios}
              formato={(v) => `${v} ${t('common.anios')}`}
            />
          </section>

          <SavedPoints />

          <p className="flex items-start gap-2 rounded-lg bg-surface-2 p-3 text-[11px] leading-snug text-muted">
            <Info aria-hidden="true" className="mt-0.5 h-3.5 w-3.5 shrink-0" />
            {t('sidebar.nota')}
          </p>
        </div>

        {/* Riel de iconos cuando está plegado (solo escritorio) */}
        <div className={cn('hidden flex-1 flex-col items-center gap-2 p-3', !sidebarAbierto && 'lg:flex')}>
          <button
            type="button"
            onClick={alternarSidebar}
            aria-label={t('header.panel')}
            className="flex h-10 w-10 items-center justify-center rounded-lg text-muted hover:bg-surface-2 hover:text-fg"
          >
            <Layers aria-hidden="true" className="h-5 w-5" />
          </button>
          {CAPAS.map((capa) => {
            const Icono = capa.icono
            return (
              <button
                key={capa.id}
                type="button"
                title={t(capa.clave)}
                aria-label={t(capa.clave)}
                aria-pressed={capa.id === layer}
                onClick={() => setCapa(capa.id)}
                className={cn(
                  'flex h-10 w-10 items-center justify-center rounded-lg transition-colors',
                  capa.id === layer ? 'bg-accent/10 text-accent' : 'text-muted hover:bg-surface-2 hover:text-fg',
                )}
              >
                <Icono aria-hidden="true" className="h-5 w-5" />
              </button>
            )
          })}
        </div>
      </aside>
    </>
  )
}
