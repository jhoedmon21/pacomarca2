/**
 * i18n ligero con tipado estricto: cada clave usada en t('...') existe
 * en los dos diccionarios o TypeScript falla. Base: español.
 */
import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'

const es = {
  // Comunes
  'common.cargando': 'Cargando…',
  'common.cargandoCapa': 'Cargando capa satelital…',
  'common.error': 'No se pudo cargar',
  'common.errorMensaje': 'El servicio no respondió correctamente. Puedes reintentar.',
  'common.reintentar': 'Reintentar',
  'common.vacio': 'Sin datos disponibles',
  'common.vacioMensaje': 'No hay registros para el punto y periodo seleccionados.',
  'common.csv': 'Descargar CSV',
  'common.png': 'Descargar PNG',
  'common.saltar': 'Saltar al contenido',
  'common.anios': 'años',
  // App / cabecera
  'app.titulo': 'Fundo Pacomarca',
  'app.subtitulo': 'Plataforma de Inteligencia Agronómica',
  'header.panel': 'Abrir o cerrar el panel lateral',
  'header.tema': 'Cambiar tema (claro/oscuro/sistema)',
  'header.idioma': 'Cambiar idioma',
  'weather.aire': 'AIRE',
  'weather.humedad': 'HUMEDAD',
  'weather.lluvia': 'LLUVIA',
  // Barra lateral
  'sidebar.titulo': 'PACOMARCA',
  'sidebar.subtitulo': 'Scientific Suite',
  'sidebar.punto': 'PUNTO DE CONTROL',
  'sidebar.lat': 'Latitud',
  'sidebar.lon': 'Longitud',
  'sidebar.predeterminado': 'Usar punto por defecto',
  'sidebar.coordenadaInvalida': 'Coordenada fuera de rango',
  'sidebar.capas': 'CAPAS Y MODELOS',
  'sidebar.serie': 'SERIE DE TIEMPO',
  'sidebar.anios': 'Años de análisis',
  'sidebar.nota': 'Modelo de biomasa heurístico: NDVI × 2800 (configurable).',
  'sidebar.mapHint': 'Haz clic en el mapa para mover el punto de control',
  // Capas
  'layer.biomasa': 'Biomasa (Kg/Ha)',
  'layer.biomasa.desc': 'Forraje disponible',
  'layer.clasificacion': 'Clasificación (IA)',
  'layer.clasificacion.desc': 'Tipos de hábitat',
  'layer.radar': 'Radar S1 (Estructura)',
  'layer.radar.desc': 'Penetración de nubes',
  'layer.ndvi': 'NDVI (Vigor)',
  'layer.ndvi.desc': 'Índice estándar',
  'layer.evi': 'EVI (Alta densidad)',
  'layer.evi.desc': 'Índice mejorado',
  'layer.savi': 'SAVI (Suelo)',
  'layer.savi.desc': 'Corrige suelo en cobertura baja',
  'layer.ndwi': 'NDWI (Agua)',
  'layer.ndwi.desc': 'Humedad y bofedales',
  // KPIs
  'kpi.promedio': 'Promedio histórico',
  'kpi.ultimo': 'Último valor',
  'kpi.anomalia': 'Anomalía vs. histórico',
  'kpi.tendencia': 'Tendencia anual',
  'kpi.unidadAnio': '/año',
  // Pestañas
  'section.analisis': 'Análisis de tendencias y alertas',
  'tabs.serie': 'Dinámica temporal',
  'tabs.alertas': 'Monitor de alertas',
  'tabs.clasificacion': 'Clasificación de hábitats',
  'tabs.comparador': 'Comparador de periodos',
  // Alertas
  'alerta.degradacion': 'Degradación significativa',
  'alerta.degradacion.desc': 'El valor actual está muy por debajo del promedio histórico.',
  'alerta.favorable': 'Condición favorable',
  'alerta.favorable.desc': 'Condiciones superiores al promedio histórico.',
  'alerta.estable': 'Estable',
  'alerta.estable.desc': 'Los valores se mantienen dentro del rango esperado.',
  'alerta.umbral': 'Umbral de alerta: ±15 %',
  'alerta.promedioHistorico': 'Promedio histórico',
  'alerta.vs': 'vs promedio',
  'alerta.historial': 'Historial de alertas (base de datos)',
  'alerta.historialVacio': 'Aún no hay alertas registradas. El job diario las guardará aquí.',
  'alerta.registro': 'Alerta registrada',
  // Puntos guardados (persistencia)
  'puntos.titulo': 'PUNTOS GUARDADOS',
  'puntos.nombre': 'Nombre del punto',
  'puntos.guardar': 'Guardar',
  'puntos.guardarActual': 'Guardar el punto actual en la base de datos',
  'puntos.eliminar': 'Eliminar punto',
  'puntos.vacio': 'Guarda tu primer punto para acceder rápido desde cualquier dispositivo.',
  'puntos.errorGuardar': 'No se pudo guardar el punto.',
  'puntos.errorCargar': 'No se pudieron cargar los datos guardados.',
  // Clasificación
  'clasif.nota': 'Clasificación por umbrales de NDVI (Sentinel-2, 10 m).',
  'clasif.cobertura': 'Cobertura del área de análisis',
  // Comparador
  'comparador.periodoA': 'Periodo A',
  'comparador.periodoB': 'Periodo B',
  'comparador.diferencia': 'Diferencia',
  'comparador.nota': 'Compara el promedio anual de dos periodos de la serie.',
  'comparador.anio': 'Año',
  // Mapa
  'map.leyenda': 'Leyenda',
  'map.errorCapa': 'No se pudo cargar la capa satelital',
  'map.exportarRoi': 'Exportar área de análisis (GeoJSON)',
  'serie.concordancia': 'Concordancia MODIS vs Sentinel-2',
  // Pie
  'footer.firma': 'Jhon Monroy | Experto en Informática',
  'footer.fuentes': 'Fuentes: Google Earth Engine (MODIS 061, Sentinel-1/2) y Open-Meteo',
} as const

export type I18nKey = keyof typeof es
type Lang = 'es' | 'en'

const en: Record<I18nKey, string> = {
  'common.cargando': 'Loading…',
  'common.cargandoCapa': 'Loading satellite layer…',
  'common.error': 'Could not load',
  'common.errorMensaje': 'The service did not respond correctly. You can retry.',
  'common.reintentar': 'Retry',
  'common.vacio': 'No data available',
  'common.vacioMensaje': 'There are no records for the selected point and period.',
  'common.csv': 'Download CSV',
  'common.png': 'Download PNG',
  'common.saltar': 'Skip to content',
  'common.anios': 'years',
  'app.titulo': 'Pacomarca Farm',
  'app.subtitulo': 'Agronomic Intelligence Platform',
  'header.panel': 'Open or close the side panel',
  'header.tema': 'Change theme (light/dark/system)',
  'header.idioma': 'Change language',
  'weather.aire': 'AIR',
  'weather.humedad': 'HUMIDITY',
  'weather.lluvia': 'RAIN',
  'sidebar.titulo': 'PACOMARCA',
  'sidebar.subtitulo': 'Scientific Suite',
  'sidebar.punto': 'CONTROL POINT',
  'sidebar.lat': 'Latitude',
  'sidebar.lon': 'Longitude',
  'sidebar.predeterminado': 'Use default point',
  'sidebar.coordenadaInvalida': 'Coordinate out of range',
  'sidebar.capas': 'LAYERS & MODELS',
  'sidebar.serie': 'TIME SERIES',
  'sidebar.anios': 'Years of analysis',
  'sidebar.nota': 'Heuristic biomass model: NDVI × 2800 (configurable).',
  'sidebar.mapHint': 'Click the map to move the control point',
  'layer.biomasa': 'Biomass (Kg/Ha)',
  'layer.biomasa.desc': 'Available forage',
  'layer.clasificacion': 'Classification (AI)',
  'layer.clasificacion.desc': 'Habitat types',
  'layer.radar': 'S1 Radar (Structure)',
  'layer.radar.desc': 'Cloud penetration',
  'layer.ndvi': 'NDVI (Vigor)',
  'layer.ndvi.desc': 'Standard index',
  'layer.evi': 'EVI (High density)',
  'layer.evi.desc': 'Enhanced index',
  'layer.savi': 'SAVI (Soil)',
  'layer.savi.desc': 'Soil-corrected, low cover',
  'layer.ndwi': 'NDWI (Water)',
  'layer.ndwi.desc': 'Wetlands and moisture',
  'kpi.promedio': 'Historical average',
  'kpi.ultimo': 'Latest value',
  'kpi.anomalia': 'Anomaly vs. history',
  'kpi.tendencia': 'Annual trend',
  'kpi.unidadAnio': '/year',
  'section.analisis': 'Trend and alert analysis',
  'tabs.serie': 'Temporal dynamics',
  'tabs.alertas': 'Alert monitor',
  'tabs.clasificacion': 'Habitat classification',
  'tabs.comparador': 'Period comparison',
  'alerta.degradacion': 'Significant degradation',
  'alerta.degradacion.desc': 'The current value is well below the historical average.',
  'alerta.favorable': 'Favorable condition',
  'alerta.favorable.desc': 'Conditions above the historical average.',
  'alerta.estable': 'Stable',
  'alerta.estable.desc': 'Values remain within the expected range.',
  'alerta.umbral': 'Alert threshold: ±15 %',
  'alerta.promedioHistorico': 'Historical average',
  'alerta.vs': 'vs average',
  'alerta.historial': 'Alert history (database)',
  'alerta.historialVacio': 'No alerts recorded yet. The daily job will store them here.',
  'alerta.registro': 'Registered alert',
  'puntos.titulo': 'SAVED POINTS',
  'puntos.nombre': 'Point name',
  'puntos.guardar': 'Save',
  'puntos.guardarActual': 'Save the current point to the database',
  'puntos.eliminar': 'Delete point',
  'puntos.vacio': 'Save your first point for quick access from any device.',
  'puntos.errorGuardar': 'Could not save the point.',
  'puntos.errorCargar': 'Could not load the saved data.',
  'clasif.nota': 'NDVI threshold classification (Sentinel-2, 10 m).',
  'clasif.cobertura': 'Coverage of the analysis area',
  'comparador.periodoA': 'Period A',
  'comparador.periodoB': 'Period B',
  'comparador.diferencia': 'Difference',
  'comparador.nota': 'Compares the annual average of two periods of the series.',
  'comparador.anio': 'Year',
  'map.leyenda': 'Legend',
  'map.errorCapa': 'Could not load the satellite layer',
  'map.exportarRoi': 'Export analysis area (GeoJSON)',
  'serie.concordancia': 'MODIS vs Sentinel-2 agreement',
  'footer.firma': 'Jhon Monroy | IT Expert',
  'footer.fuentes': 'Sources: Google Earth Engine (MODIS 061, Sentinel-1/2) and Open-Meteo',
}

interface I18nContexto {
  lang: Lang
  t: (clave: I18nKey) => string
  setLang: (lang: Lang) => void
}

const Contexto = createContext<I18nContexto | null>(null)

export function I18nProvider({ children }: { children: ReactNode }) {
  const [lang, setLang] = useState<Lang>(() => {
    const guardado = localStorage.getItem('pacomarca-lang')
    return guardado === 'en' ? 'en' : 'es'
  })

  useEffect(() => {
    localStorage.setItem('pacomarca-lang', lang)
    document.documentElement.lang = lang
  }, [lang])

  const t = (clave: I18nKey) => (lang === 'es' ? es : en)[clave]

  return <Contexto.Provider value={{ lang, t, setLang }}>{children}</Contexto.Provider>
}

export function useI18n(): I18nContexto {
  const ctx = useContext(Contexto)
  if (!ctx) throw new Error('useI18n debe usarse dentro de I18nProvider')
  return ctx
}
