/**
 * Tipos que reflejan los modelos Pydantic del backend (backend/app/models.py).
 * Si cambian en la API, actualizar aquí para que TypeScript lo detecte.
 */

export type LayerId =
  | 'biomasa'
  | 'clasificacion'
  | 'radar_s1'
  | 'ndvi'
  | 'evi'
  | 'savi'
  | 'ndwi'
export type IndexId = 'ndvi' | 'evi' | 'biomasa'

export interface WeatherResponse {
  temperature_2m: number | null
  relative_humidity_2m: number | null
  rain: number | null
  timestamp?: string | null
}

export interface TimeseriesPoint {
  date: string // YYYY-MM-DD
  value: number
  biomass?: number | null
}

export interface TimeseriesResponse {
  lat: number
  lon: number
  years: number
  index: IndexId
  data: TimeseriesPoint[]
  unit: string
  source: string
}

export interface TileResponse {
  url: string
  layer_name: string
  min_val: number
  max_val: number
  palette: string[]
  unit: string
}

export interface ClassificationResponse {
  lat: number
  lon: number
  classification_map: Record<'0' | '1' | '2', number>
  legend: Record<string, { label: string; color: string }>
  unit: string
}

export interface StatsResponse {
  lat: number
  lon: number
  years: number
  layer: LayerId
  mean: number
  max: number
  min: number
  std: number
  trend: number
  anomaly_percent: number
  unit: string
  data_count: number
}

export interface CrosscheckResponse {
  modis_ndvi: number
  s2_ndvi: number
  diferencia: number
  nota: string
}

export interface HealthResponse {
  status: string
  version: string
  environment: string
  cache_status: string
  database_status?: string
  gee_status: string
}

// ---------------------------------------------------------------------------
// Persistencia (base de datos)
// ---------------------------------------------------------------------------
export interface PuntoControl {
  id: number
  nombre: string
  lat: number
  lon: number
  buffer_m: number
  notas?: string | null
  creado_en: string
  actualizado_en: string
}

export interface PuntoCreateInput {
  nombre: string
  lat: number
  lon: number
  buffer_m?: number
  notas?: string
}

export interface AlertaRegistro {
  id: number
  punto_id?: number | null
  lat: number
  lon: number
  indice: string
  valor_actual: number
  promedio_historico: number
  anomalia_pct: number
  severidad: 'info' | 'alerta' | 'critica'
  mensaje?: string | null
  creado_en: string
}
