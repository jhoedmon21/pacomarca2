/**
 * Cabecera fija: título, clima en vivo del punto, tema e idioma.
 */
import { CloudRain, Droplets, Languages, Menu, Monitor, Moon, Sun, Thermometer } from 'lucide-react'
import { useI18n } from '../../i18n'
import { useAppStore } from '../../store/useAppStore'
import { useTheme } from '../../theme/ThemeProvider'
import { useWeather } from '../../hooks/useWeather'
import { Skeleton } from '../ui/Skeleton'

function IndicadorClima() {
  const { lat, lon } = useAppStore()
  const { t } = useI18n()
  const { data, isLoading } = useWeather(lat, lon)

  const celdas = [
    { icono: Thermometer, etiqueta: t('weather.aire'), valor: data ? `${Math.round(data.temperature_2m ?? 0)}°` : '--' },
    { icono: Droplets, etiqueta: t('weather.humedad'), valor: data ? `${Math.round(data.relative_humidity_2m ?? 0)}%` : '--' },
    { icono: CloudRain, etiqueta: t('weather.lluvia'), valor: data ? `${(data.rain ?? 0).toFixed(1)}` : '--' },
  ]

  return (
    <div role="status" aria-live="polite" className="flex items-center gap-4">
      {celdas.map((celda) => (
        <div key={celda.etiqueta} className="text-right">
          {isLoading ? (
            <Skeleton className="h-6 w-10" />
          ) : (
            <p className="text-lg font-bold leading-tight tabular-nums">{celda.valor}</p>
          )}
          <p className="flex items-center justify-end gap-1 text-[10px] font-semibold tracking-wider text-muted">
            <celda.icono aria-hidden="true" className="h-3 w-3" />
            {celda.etiqueta}
          </p>
        </div>
      ))}
    </div>
  )
}

function AlternarTema() {
  const { t } = useI18n()
  const { tema, alternarTema } = useTheme()
  const Icono = tema === 'light' ? Sun : tema === 'dark' ? Moon : Monitor
  const siguiente = tema === 'light' ? 'dark' : tema === 'dark' ? 'system' : 'light'
  return (
    <button
      type="button"
      onClick={alternarTema}
      aria-label={`${t('header.tema')} (${siguiente})`}
      className="flex h-9 w-9 items-center justify-center rounded-lg text-muted transition-colors hover:bg-surface-2 hover:text-fg"
    >
      <Icono aria-hidden="true" className="h-5 w-5" />
    </button>
  )
}

function AlternarIdioma() {
  const { t, lang, setLang } = useI18n()
  return (
    <button
      type="button"
      onClick={() => setLang(lang === 'es' ? 'en' : 'es')}
      aria-label={t('header.idioma')}
      className="flex h-9 items-center gap-1.5 rounded-lg px-2 text-xs font-bold uppercase text-muted transition-colors hover:bg-surface-2 hover:text-fg"
    >
      <Languages aria-hidden="true" className="h-4 w-4" />
      {lang === 'es' ? 'EN' : 'ES'}
    </button>
  )
}

export function Header() {
  const { t } = useI18n()
  const alternarSidebar = useAppStore((s) => s.alternarSidebar)

  return (
    <header className="sticky top-0 z-30 border-b border-border bg-surface">
      <div className="mx-auto flex h-16 max-w-7xl 2xl:max-w-[1536px] items-center justify-between gap-3 px-4 lg:px-8">
        <div className="flex min-w-0 items-center gap-3">
          <button
            type="button"
            onClick={alternarSidebar}
            aria-label={t('header.panel')}
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg text-muted transition-colors hover:bg-surface-2 hover:text-fg"
          >
            <Menu aria-hidden="true" className="h-5 w-5" />
          </button>
          <div className="min-w-0">
            <h1 className="truncate font-display text-lg font-semibold leading-tight tracking-tight sm:text-xl">
              {t('app.titulo')}
            </h1>
            <p className="hidden truncate text-xs text-muted sm:block">{t('app.subtitulo')}</p>
          </div>
        </div>
        <div className="flex shrink-0 items-center gap-2 sm:gap-4">
          <IndicadorClima />
          <div className="hidden items-center gap-1 border-l border-border pl-2 sm:flex">
            <AlternarIdioma />
            <AlternarTema />
          </div>
        </div>
      </div>
    </header>
  )
}
