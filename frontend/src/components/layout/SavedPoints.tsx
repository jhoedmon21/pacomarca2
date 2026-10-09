/**
 * Puntos guardados (persistidos en la base de datos):
 * lista para cargar/eliminar y un formulario para guardar el punto actual.
 */
import { useState, type FormEvent } from 'react'
import { BookmarkPlus, Check, Database, MapPin, Trash2 } from 'lucide-react'
import { useI18n } from '../../i18n'
import { useAppStore } from '../../store/useAppStore'
import { useCrearPunto, useEliminarPunto, usePuntos } from '../../hooks/usePuntos'
import { Button } from '../ui/Button'
import { cn } from '../../lib/utils'

export function SavedPoints() {
  const { t } = useI18n()
  const { lat, lon, setPunto } = useAppStore()
  const puntos = usePuntos()
  const crear = useCrearPunto()
  const eliminar = useEliminarPunto()
  const [nombre, setNombre] = useState('')
  const [guardado, setGuardado] = useState(false)

  const alGuardar = async (e: FormEvent) => {
    e.preventDefault()
    const nombreLimpio = nombre.trim()
    if (!nombreLimpio) return
    try {
      await crear.mutateAsync({ nombre: nombreLimpio, lat, lon })
      setNombre('')
      setGuardado(true)
      setTimeout(() => setGuardado(false), 2000)
    } catch {
      // El estado del hook (crear.isError) ya refleja el fallo en la UI
    }
  }

  const alEliminar = async (id: number) => {
    try {
      await eliminar.mutateAsync(id)
    } catch {
      // El listado se queda como estaba; el error se muestra vía toast implícito
    }
  }

  return (
    <section aria-labelledby="titulo-guardados">
      <h2
        id="titulo-guardados"
        className="mb-2 flex items-center gap-1.5 text-[10px] font-bold tracking-widest text-muted"
      >
        <Database aria-hidden="true" className="h-3 w-3" /> {t('puntos.titulo')}
      </h2>

      <form onSubmit={alGuardar} className="mb-3 flex gap-2">
        <label htmlFor="nombre-punto" className="sr-only">
          {t('puntos.nombre')}
        </label>
        <input
          id="nombre-punto"
          type="text"
          value={nombre}
          onChange={(e) => setNombre(e.target.value)}
          placeholder={t('puntos.nombre')}
          maxLength={100}
          className="h-9 min-w-0 flex-1 rounded-lg border border-border bg-surface px-2.5 text-sm"
        />
        <Button
          type="submit"
          size="sm"
          variant="outline"
          disabled={!nombre.trim() || crear.isPending}
          aria-label={t('puntos.guardarActual')}
        >
          {guardado ? (
            <Check aria-hidden="true" className="h-3.5 w-3.5 text-success" />
          ) : (
            <BookmarkPlus aria-hidden="true" className="h-3.5 w-3.5" />
          )}
          <span className="hidden xl:inline">{t('puntos.guardar')}</span>
        </Button>
      </form>

      {crear.isError && (
        <p role="alert" className="mb-2 rounded-lg bg-danger/10 p-2 text-[11px] text-danger">
          {t('puntos.errorGuardar')}
        </p>
      )}

      {puntos.isLoading ? (
        <p className="px-1 text-[11px] text-muted">{t('common.cargando')}</p>
      ) : puntos.isError ? (
        <p className="px-1 text-[11px] text-muted">{t('puntos.errorCargar')}</p>
      ) : (
        <ul className="space-y-1" aria-label={t('puntos.titulo')}>
          {puntos.data?.map((punto) => {
            const activo =
              punto.lat.toFixed(5) === lat.toFixed(5) && punto.lon.toFixed(5) === lon.toFixed(5)
            return (
              <li key={punto.id} className="group flex items-center gap-1">
                <button
                  type="button"
                  onClick={() => setPunto(punto.lat, punto.lon)}
                  title={punto.notas ?? `${punto.lat}, ${punto.lon}`}
                  className={cn(
                    'flex min-w-0 flex-1 items-center gap-2 rounded-lg px-2.5 py-1.5 text-left text-xs font-semibold transition-colors',
                    activo ? 'bg-accent/10 text-accent' : 'text-fg hover:bg-surface-2',
                  )}
                >
                  <MapPin aria-hidden="true" className="h-3.5 w-3.5 shrink-0" />
                  <span className="min-w-0 truncate">{punto.nombre}</span>
                </button>
                <button
                  type="button"
                  onClick={() => alEliminar(punto.id)}
                  aria-label={`${t('puntos.eliminar')} ${punto.nombre}`}
                  title={t('puntos.eliminar')}
                  disabled={eliminar.isPending}
                  className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg text-muted opacity-0 transition-opacity hover:bg-danger/10 hover:text-danger focus-visible:opacity-100 group-hover:opacity-100"
                >
                  <Trash2 aria-hidden="true" className="h-3.5 w-3.5" />
                </button>
              </li>
            )
          })}
          {(puntos.data?.length ?? 0) === 0 && (
            <li className="px-1 text-[11px] text-muted">{t('puntos.vacio')}</li>
          )}
        </ul>
      )}
    </section>
  )
}
