/**
 * Cliente HTTP tipado contra la API de Pacomarca.
 * En desarrollo usa el proxy de Vite (/api -> localhost:8000);
 * en producción, el reverse proxy (Caddy) sirve /api en el mismo origen.
 */
import type {
  AlertaRegistro,
  ClassificationResponse,
  CrosscheckResponse,
  HealthResponse,
  IndexId,
  LayerId,
  PuntoControl,
  PuntoCreateInput,
  StatsResponse,
  TileResponse,
  TimeseriesResponse,
  WeatherResponse,
} from '../types'

const BASE = import.meta.env.VITE_API_URL ?? ''

const AYUDA_API =
  'El frontend no está conectado a la API: define VITE_API_URL con la URL pública del backend.'

export class ApiError extends Error {
  constructor(
    public status: number,
    mensaje: string,
  ) {
    super(mensaje)
  }
}

/** ¿La respuesta es JSON? Evita el críptico "Unexpected token '<'" cuando llega HTML. */
function esJson(respuesta: Response): boolean {
  return (respuesta.headers.get('content-type') ?? '').includes('json')
}

/** Lee el cuerpo como JSON o lanza un ApiError explicando qué pasó realmente. */
async function leerJson<T>(respuesta: Response, ruta: string): Promise<T> {
  if (!esJson(respuesta)) {
    const esHtml = (respuesta.headers.get('content-type') ?? '').includes('html')
    throw new ApiError(
      respuesta.status,
      esHtml
        ? `La ruta ${ruta} devolvió HTML en vez de JSON (HTTP ${respuesta.status}). ${AYUDA_API}`
        : `Respuesta no JSON al llamar ${ruta} (HTTP ${respuesta.status}).`,
    )
  }
  try {
    return (await respuesta.json()) as T
  } catch {
    throw new ApiError(respuesta.status, `La API devolvió un JSON inválido en ${ruta}.`)
  }
}

/** fetch con un mensaje claro cuando no hay red o el host no existe. */
async function pedir(url: string, init?: RequestInit): Promise<Response> {
  try {
    return await fetch(url, init)
  } catch {
    throw new ApiError(0, `No se pudo contactar la API en ${url}. ${AYUDA_API}`)
  }
}

async function parseError(respuesta: Response, ruta: string): Promise<ApiError> {
  const cuerpo = await respuesta.json().catch(() => null)
  const mensaje =
    cuerpo?.message ?? cuerpo?.detail ?? `Error HTTP ${respuesta.status} al llamar ${ruta}`
  return new ApiError(respuesta.status, typeof mensaje === 'string' ? mensaje : JSON.stringify(mensaje))
}

async function get<T>(ruta: string, params?: Record<string, string | number>): Promise<T> {
  const qs = new URLSearchParams()
  for (const [clave, valor] of Object.entries(params ?? {})) qs.set(clave, String(valor))
  const url = `${BASE}/api${ruta}${qs.toString() ? `?${qs.toString()}` : ''}`

  const respuesta = await pedir(url, { headers: { Accept: 'application/json' } })
  if (!respuesta.ok) throw await parseError(respuesta, ruta)
  return leerJson<T>(respuesta, ruta)
}

async function enviar<T>(
  ruta: string,
  metodo: 'POST' | 'PATCH' | 'DELETE',
  cuerpo?: unknown,
): Promise<T> {
  const respuesta = await pedir(`${BASE}/api${ruta}`, {
    method: metodo,
    headers: cuerpo !== undefined ? { 'Content-Type': 'application/json' } : undefined,
    body: cuerpo !== undefined ? JSON.stringify(cuerpo) : undefined,
  })
  if (!respuesta.ok) throw await parseError(respuesta, ruta)
  if (respuesta.status === 204) return undefined as T
  return leerJson<T>(respuesta, ruta)
}

export const api = {
  salud: () => get<HealthResponse>('/health'),
  clima: (lat: number, lon: number) => get<WeatherResponse>('/weather', { lat, lon }),
  serie: (lat: number, lon: number, years: number, index: IndexId) =>
    get<TimeseriesResponse>('/timeseries', { lat, lon, years, index }),
  tiles: (layer: LayerId, lat: number, lon: number) =>
    get<TileResponse>(`/tiles/${layer}`, { lat, lon }),
  clasificacion: (lat: number, lon: number) =>
    get<ClassificationResponse>('/classification', { lat, lon }),
  crosscheck: (lat: number, lon: number) =>
    get<CrosscheckResponse>('/crosscheck', { lat, lon }),
  stats: (lat: number, lon: number, years: number, layer: LayerId) =>
    get<StatsResponse>('/stats', { lat, lon, years, layer }),

  // Persistencia (base de datos)
  puntos: {
    listar: () => get<PuntoControl[]>('/puntos'),
    crear: (datos: PuntoCreateInput) => enviar<PuntoControl>('/puntos', 'POST', datos),
    actualizar: (id: number, cambios: Partial<PuntoCreateInput>) =>
      enviar<PuntoControl>(`/puntos/${id}`, 'PATCH', cambios),
    eliminar: (id: number) => enviar<void>(`/puntos/${id}`, 'DELETE'),
  },
  alertas: {
    listar: (limite = 50, puntoId?: number) =>
      get<AlertaRegistro[]>('/alertas', { limite, ...(puntoId ? { punto_id: puntoId } : {}) }),
  },
}
