/**
 * Mapa protagonista (MapLibre GL):
 * - Base satelital (Esri World Imagery, como el HYBRID original).
 * - Capa raster de GEE (URL de tiles del backend) según la capa activa.
 * - Círculo del ROI (buffer 2000 m) y marcador arrastrable.
 * - Clic en el mapa = nuevo punto de control (además de lat/lon manual).
 */
import { useEffect, useRef } from 'react'
import maplibregl, { type StyleSpecification } from 'maplibre-gl'
import { Download, Loader2, MousePointerClick, TriangleAlert } from 'lucide-react'
import { useI18n } from '../../i18n'
import { useTiles } from '../../hooks/useTiles'
import { useAppStore } from '../../store/useAppStore'
import { circuloGeoJson, exportarGeoJson } from '../../lib/utils'
import { MapLegend } from './MapLegend'
import { Skeleton } from '../ui/Skeleton'

const ESTILO_SATELITE: StyleSpecification = {
  version: 8,
  sources: {
    satelite: {
      type: 'raster',
      tiles: [
        'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
      ],
      tileSize: 256,
      attribution: 'Imágenes © Esri, Maxar, Earthstar Geographics',
    },
  },
  layers: [
    { id: 'fondo', type: 'background', paint: { 'background-color': '#1f1913' } },
    { id: 'satelite', type: 'raster', source: 'satelite' },
  ],
}

const ID_FUENTE_GEE = 'gee'
const ID_CAPA_GEE = 'capa-gee'
const ID_FUENTE_ROI = 'roi'
const ID_CAPA_ROI_BASE = 'roi-base'
const ID_CAPA_ROI_LINEA = 'roi-linea'

export function MapView() {
  const contenedorRef = useRef<HTMLDivElement>(null)
  const mapaRef = useRef<maplibregl.Map | null>(null)
  const marcadorRef = useRef<maplibregl.Marker | null>(null)

  const { lat, lon, layer, setPunto } = useAppStore()
  const { t } = useI18n()
  const tiles = useTiles(lat, lon, layer)

  // ---- Inicialización (una sola vez) ----
  // lon/lat iniciales solo sierten el centro de arranque; los cambios
  // posteriores los maneja el efecto del punto, por eso la lista vacía.
  useEffect(() => {
    const contenedor = contenedorRef.current
    if (!contenedor || mapaRef.current) return

    const mapa = new maplibregl.Map({
      container: contenedor,
      style: ESTILO_SATELITE,
      center: [lon, lat],
      zoom: 12.5,
      attributionControl: { compact: true },
    })
    mapaRef.current = mapa

    mapa.addControl(new maplibregl.NavigationControl(), 'top-right')

    // Clic: nuevo punto de control
    mapa.on('click', (e) => setPunto(e.lngLat.lat, e.lngLat.lng))

    // El ancho cambia al plegar el sidebar: mantener el tamaño correcto
    const observador = new ResizeObserver(() => mapa.resize())
    observador.observe(contenedor)

    return () => {
      observador.disconnect()
      mapa.remove()
      mapaRef.current = null
      marcadorRef.current = null
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // ---- Punto de control: marcador, ROI y centrado ----
  useEffect(() => {
    const mapa = mapaRef.current
    if (!mapa) return

    const aplicar = () => {
      // Marcador arrastrable (alternativa accesible: inputs del sidebar)
      if (!marcadorRef.current) {
        marcadorRef.current = new maplibregl.Marker({ color: '#e07643', draggable: true })
          .setLngLat([lon, lat])
          .addTo(mapa)
        marcadorRef.current.on('dragend', () => {
          const pos = marcadorRef.current?.getLngLat()
          if (pos) setPunto(pos.lat, pos.lng)
        })
      } else {
        marcadorRef.current.setLngLat([lon, lat])
      }

      // ROI (círculo de 2000 m)
      const datos = circuloGeoJson(lat, lon, 2000)
      const fuente = mapa.getSource(ID_FUENTE_ROI)
      if (fuente && fuente.type === 'geojson') {
        ;(fuente as maplibregl.GeoJSONSource).setData(datos)
      } else {
        mapa.addSource(ID_FUENTE_ROI, { type: 'geojson', data: datos })
        // Contorno doble (oscuro + blanco) para contraste sobre satélite
        mapa.addLayer({
          id: ID_CAPA_ROI_BASE,
          type: 'line',
          source: ID_FUENTE_ROI,
          paint: { 'line-color': '#000000', 'line-width': 4, 'line-opacity': 0.55 },
        })
        mapa.addLayer({
          id: ID_CAPA_ROI_LINEA,
          type: 'line',
          source: ID_FUENTE_ROI,
          paint: { 'line-color': '#ffffff', 'line-width': 2 },
        })
      }

      mapa.flyTo({ center: [lon, lat], speed: 1.4, essential: true })
    }

    if (mapa.isStyleLoaded()) aplicar()
    else mapa.once('load', aplicar)
  }, [lat, lon, setPunto])

  // ---- Capa raster de GEE según la capa activa ----
  useEffect(() => {
    const mapa = mapaRef.current
    if (!mapa || !tiles.data) return

    const aplicar = () => {
      if (mapa.getLayer(ID_CAPA_GEE)) mapa.removeLayer(ID_CAPA_GEE)
      if (mapa.getSource(ID_FUENTE_GEE)) mapa.removeSource(ID_FUENTE_GEE)

      mapa.addSource(ID_FUENTE_GEE, {
        type: 'raster',
        tiles: [tiles.data.url],
        tileSize: 256,
      })
      // Debajo de las líneas del ROI si ya existen
      const antes = mapa.getLayer(ID_CAPA_ROI_BASE) ? ID_CAPA_ROI_BASE : undefined
      mapa.addLayer(
        {
          id: ID_CAPA_GEE,
          type: 'raster',
          source: ID_FUENTE_GEE,
          paint: { 'raster-opacity': 0.85, 'raster-fade-duration': 300 },
        },
        antes,
      )
    }

    if (mapa.isStyleLoaded()) aplicar()
    else mapa.once('load', aplicar)
  }, [tiles.data])

  const cargandoCapa = tiles.isFetching && !tiles.data

  return (
    <div className="relative h-[420px] overflow-hidden rounded-xl border border-border lg:h-full lg:min-h-[520px]">
      <div ref={contenedorRef} className="absolute inset-0" aria-label={t('app.titulo')} role="application" />

      {/* Pista de interacción */}
      <div className="pointer-events-none absolute left-3 top-3 z-10 flex items-center gap-1.5 rounded-full bg-black/60 px-3 py-1.5 text-xs font-semibold text-white backdrop-blur">
        <MousePointerClick aria-hidden="true" className="h-3.5 w-3.5" />
        {t('sidebar.mapHint')}
      </div>

      {/* Exportar el área de análisis como GeoJSON (SIG: QGIS/ArcGIS) */}
      <button
        type="button"
        title={t('map.exportarRoi')}
        aria-label={t('map.exportarRoi')}
        onClick={() =>
          exportarGeoJson(circuloGeoJson(lat, lon, 2000), `pacomarca_roi_${lat}_${lon}.geojson`)
        }
        className="absolute left-3 top-12 z-10 flex h-9 w-9 items-center justify-center rounded-lg bg-surface/95 text-muted shadow-card backdrop-blur transition-colors hover:text-fg"
      >
        <Download aria-hidden="true" className="h-4 w-4" />
      </button>

      {/* Estado de la capa GEE */}
      {cargandoCapa && (
        <div className="absolute bottom-3 right-3 z-10 flex items-center gap-2 rounded-lg bg-surface/95 px-3 py-2 text-xs font-semibold text-muted shadow-card">
          <Loader2 aria-hidden="true" className="h-3.5 w-3.5 animate-spin" />
          {t('common.cargandoCapa')}
          <Skeleton className="hidden" />
        </div>
      )}
      {tiles.isError && (
        <div role="alert" className="absolute bottom-3 right-3 z-10 flex items-center gap-2 rounded-lg bg-danger/95 px-3 py-2 text-xs font-semibold text-danger-fg">
          <TriangleAlert aria-hidden="true" className="h-3.5 w-3.5" />
          {t('map.errorCapa')}
        </div>
      )}

      {/* Leyenda */}
      {tiles.data && (
        <MapLegend
          titulo={tiles.data.layer_name}
          paleta={tiles.data.palette}
          minVal={tiles.data.min_val}
          maxVal={tiles.data.max_val}
          unidad={tiles.data.unit}
        />
      )}
    </div>
  )
}
