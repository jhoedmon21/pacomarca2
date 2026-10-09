"""
Modelos Pydantic para la API.
"""
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from enum import Enum


class LayerType(str, Enum):
    """Tipos de capas disponibles."""
    BIOMASS = "biomasa"
    CLASSIFICATION = "clasificacion"
    S1 = "radar_s1"
    NDVI = "ndvi"
    EVI = "evi"
    SAVI = "savi"      # índice ajustado por suelo (cobertura baja)
    NDWI = "ndwi"      # índice de agua/humedad


class IndexType(str, Enum):
    """Tipos de índices para series temporales."""
    NDVI = "ndvi"
    EVI = "evi"
    BIOMASS = "biomasa"


class WeatherResponse(BaseModel):
    """Respuesta del clima."""
    temperature_2m: float = Field(description="Temperatura en °C")
    relative_humidity_2m: float = Field(description="Humedad relativa en %")
    rain: float = Field(description="Precipitación en mm")
    timestamp: Optional[datetime] = Field(default=None, description="Hora de la medición")


class TimeseriesPoint(BaseModel):
    """Punto de datos para series temporales."""
    date: str = Field(description="Fecha en formato YYYY-MM-DD")
    value: float = Field(description="Valor del índice")
    biomass: Optional[float] = Field(default=None, description="Biomasa en Kg/Ha")


class TimeseriesResponse(BaseModel):
    """Respuesta de series temporales."""
    lat: float
    lon: float
    years: int
    index: IndexType
    data: List[TimeseriesPoint]
    unit: str = Field(description="Unidad de medición")
    source: str = Field(description="Fuente de datos")


class TileResponse(BaseModel):
    """Respuesta de tiles de GEE."""
    url: str = Field(description="URL del tile de GEE")
    layer_name: str = Field(description="Nombre de la capa")
    min_val: float = Field(description="Valor mínimo para visualización")
    max_val: float = Field(description="Valor máximo para visualización")
    palette: List[str] = Field(description="Paleta de colores")
    unit: Optional[str] = Field(default=None, description="Unidad de medición")


class ClassificationResponse(BaseModel):
    """Respuesta de clasificación."""
    lat: float
    lon: float
    classification_map: dict = Field(description="Mapa de clasificación (0=Suelo, 1=Pasto Bajo, 2=Pasto Alto)")
    legend: dict = Field(description="Leyenda de clases")
    unit: str = Field(description="Unidad de medición")


class StatsResponse(BaseModel):
    """Respuesta de estadísticas resumen."""
    lat: float
    lon: float
    years: int
    layer: LayerType
    mean: float = Field(description="Promedio")
    max: float = Field(description="Máximo")
    min: float = Field(description="Mínimo")
    std: float = Field(description="Desviación estándar")
    trend: float = Field(description="Tendencia")
    anomaly_percent: float = Field(description="Anomalía porcentual vs promedio histórico")
    unit: str = Field(description="Unidad de medición")
    data_count: int = Field(description="Cantidad de datos disponibles")


class CrosscheckResponse(BaseModel):
    """Validación cruzada MODIS vs Sentinel-2."""
    modis_ndvi: float = Field(description="NDVI MODIS/061 a 250 m (media 48 días)")
    s2_ndvi: float = Field(description="NDVI Sentinel-2 a 10 m (última escena)")
    diferencia: float = Field(description="s2_ndvi - modis_ndvi")
    nota: str = Field(description="Explicación de las fuentes comparadas")


class HealthResponse(BaseModel):
    """Respuesta de health check."""
    status: str = Field(description="Estado de la aplicación")
    version: str = Field(description="Versión de la API")
    environment: str = Field(description="Entorno de ejecución")
    cache_status: str = Field(description="Estado del caché")
    gee_status: str = Field(description="Estado de conexión GEE")
    database_status: str = Field(default="desconocido", description="Estado de la base de datos")


# ---------------------------------------------------------------------------
# Puntos de control (persistencia en base de datos)
# ---------------------------------------------------------------------------
class PuntoCreate(BaseModel):
    """Payload para guardar un punto de control."""
    nombre: str = Field(min_length=1, max_length=100, description="Nombre del punto")
    lat: float = Field(ge=-90, le=90, description="Latitud en grados decimales")
    lon: float = Field(ge=-180, le=180, description="Longitud en grados decimales")
    buffer_m: int = Field(default=2000, ge=100, le=10000, description="Radio de análisis (m)")
    notas: Optional[str] = Field(default=None, max_length=1000, description="Notas del punto")

    @field_validator("nombre", "notas")
    @classmethod
    def _sin_espacios_extremos(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
        return v if v else None


class PuntoUpdate(BaseModel):
    """Payload para editar un punto (todos los campos opcionales)."""
    nombre: Optional[str] = Field(default=None, min_length=1, max_length=100)
    lat: Optional[float] = Field(default=None, ge=-90, le=90)
    lon: Optional[float] = Field(default=None, ge=-180, le=180)
    buffer_m: Optional[int] = Field(default=None, ge=100, le=10000)
    notas: Optional[str] = Field(default=None, max_length=1000)


class PuntoOut(BaseModel):
    """Punto de control guardado."""
    id: int
    nombre: str
    lat: float
    lon: float
    buffer_m: int
    notas: Optional[str] = None
    creado_en: datetime
    actualizado_en: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Historial de alertas
# ---------------------------------------------------------------------------
class AlertaCreate(BaseModel):
    """Payload para registrar una alerta (la usa el job diario)."""
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    indice: str = Field(default="biomasa", max_length=20)
    valor_actual: float
    promedio_historico: float
    anomalia_pct: float = Field(description="Anomalía porcentual vs histórico")
    severidad: str = Field(default="alerta", pattern="^(info|alerta|critica)$")
    mensaje: Optional[str] = Field(default=None, max_length=1000)
    punto_id: Optional[int] = Field(default=None, description="Vincular a un punto guardado")


class AlertaOut(BaseModel):
    """Alerta registrada."""
    id: int
    punto_id: Optional[int] = None
    lat: float
    lon: float
    indice: str
    valor_actual: float
    promedio_historico: float
    anomalia_pct: float
    severidad: str
    mensaje: Optional[str] = None
    creado_en: datetime

    model_config = {"from_attributes": True}


class ErrorResponse(BaseModel):
    """Error estandarizado."""
    error: str = Field(description="Tipo de error")
    message: str = Field(description="Mensaje descriptivo")
    detail: Optional[str] = Field(default=None, description="Detalle técnico opcional")
    timestamp: Optional[datetime] = Field(default=None, description="Hora del error")


class ValidationError(BaseModel):
    """Validación de errores."""
    field: str = Field(description="Campo afectado")
    message: str = Field(description="Mensaje de validación")


class ValidationErrorResponse(BaseModel):
    """Error de validación detallado."""
    error: str = Field(default="Validation Error")
    message: str = Field(default="One or more fields failed validation")
    details: List[ValidationError] = Field(default_factory=list)
