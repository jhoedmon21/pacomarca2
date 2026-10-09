/**
 * Utilidades compartidas: clases CSS, formato numérico, exportaciones
 * (CSV/PNG) y geometría del área de análisis.
 */
import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

/** Combina clases de Tailwind sin conflictos (convención shadcn/ui). */
export function cn(...entradas: ClassValue[]) {
  return twMerge(clsx(entradas))
}

const formato = new Intl.NumberFormat('es-PE', { maximumFractionDigits: 2 })

/** Formatea un número para mostrar en la UI (es-PE). */
export function formatNumber(valor: number | null | undefined): string {
  if (valor === null || valor === undefined || Number.isNaN(valor)) return '--'
  return formato.format(valor)
}

/** Limita un número al rango [min, max]. */
export function clamp(n: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, n))
}

function descargarBlob(blob: Blob, nombre: string) {
  const url = URL.createObjectURL(blob)
  const enlace = document.createElement('a')
  enlace.href = url
  enlace.download = nombre
  enlace.click()
  URL.revokeObjectURL(url)
}

/** Exporta filas de datos a CSV (con BOM para que Excel respete ñ/acentos). */
export function exportarCsv(
  filas: Record<string, string | number | null | undefined>[],
  nombre: string,
) {
  if (filas.length === 0) return
  const encabezados = Object.keys(filas[0])
  const lineas = [
    encabezados.join(','),
    ...filas.map((f) =>
      encabezados
        .map((h) => {
          const v = f[h]
          return v === null || v === undefined ? '' : String(v)
        })
        .join(','),
    ),
  ]
  descargarBlob(new Blob(['\uFEFF' + lineas.join('\n')], { type: 'text/csv;charset=utf-8' }), nombre)
}

/**
 * Exporta a PNG el primer <svg> dentro de un contenedor (los gráficos de
 * Recharts son SVG nativos, así que la conversión es puramente local).
 */
export function exportarPngDesdeSvg(contenedor: HTMLElement, nombre: string, fondo = '#ffffff') {
  const svg = contenedor.querySelector('svg')
  if (!svg) return
  const rect = svg.getBoundingClientRect()
  const clon = svg.cloneNode(true) as SVGSVGElement
  clon.setAttribute('width', String(rect.width))
  clon.setAttribute('height', String(rect.height))
  clon.setAttribute('xmlns', 'http://www.w3.org/2000/svg')

  const datos = new XMLSerializer().serializeToString(clon)
  const url = URL.createObjectURL(new Blob([datos], { type: 'image/svg+xml;charset=utf-8' }))
  const img = new Image()
  img.onload = () => {
    const escala = 2 // resolución retina
    const lienzo = document.createElement('canvas')
    lienzo.width = rect.width * escala
    lienzo.height = rect.height * escala
    const ctx = lienzo.getContext('2d')
    if (!ctx) return
    ctx.fillStyle = fondo
    ctx.fillRect(0, 0, lienzo.width, lienzo.height)
    ctx.drawImage(img, 0, 0, lienzo.width, lienzo.height)
    URL.revokeObjectURL(url)
    lienzo.toBlob((blob) => {
      if (blob) descargarBlob(blob, nombre)
    }, 'image/png')
  }
  img.src = url
}

/** Exporta un objeto GeoJSON a archivo .geojson (por ejemplo, el ROI). */
export function exportarGeoJson(geojson: unknown, nombre: string) {
  descargarBlob(
    new Blob([JSON.stringify(geojson, null, 2)], { type: 'application/geo+json' }),
    nombre,
  )
}

/** Genera el círculo (polígono GeoJSON) del área de análisis en metros. */
export function circuloGeoJson(lat: number, lon: number, radioM: number, pasos = 128) {
  const coordenadas: [number, number][] = []
  const dLat = radioM / 111320
  const dLon = radioM / (111320 * Math.cos((lat * Math.PI) / 180))
  for (let i = 0; i <= pasos; i++) {
    const angulo = (i / pasos) * 2 * Math.PI
    coordenadas.push([lon + dLon * Math.sin(angulo), lat + dLat * Math.cos(angulo)])
  }
  return {
    type: 'FeatureCollection' as const,
    features: [
      {
        type: 'Feature' as const,
        properties: {},
        geometry: { type: 'Polygon' as const, coordinates: [coordenadas] },
      },
    ],
  }
}
