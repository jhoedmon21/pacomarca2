"""
Configuración centralizada de la aplicación (Pydantic Settings v2).

Todas las variables se leen desde el entorno o desde un archivo `.env`.
Ningún secreto debe escribirse directamente en el código.
La correspondencia es insensible a mayúsculas: `gee_project` <-> `GEE_PROJECT`.
"""
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración global de Pacomarca Scientific Suite (backend)."""

    # --- Google Earth Engine ---
    gee_project: str = Field(default="egresados-q9tr", description="Project ID de GEE")
    gee_service_account_email: str = Field(default="", description="Email de la cuenta de servicio")
    # Contenido JSON de la clave privada O ruta a un secret montado (ej. /run/secrets/gee.json)
    gee_private_key_json: str = Field(default="", description="JSON de la cuenta de servicio o ruta al archivo")

    # --- Open-Meteo (sin API key) ---
    openmeteo_base_url: str = Field(default="https://api.open-meteo.com/v1/forecast")

    # --- Caché ---
    cache_ttl_seconds: int = Field(default=3600, description="TTL por defecto del caché (s)")
    redis_url: str = Field(default="", description="URL de Redis; vacío => caché en memoria")

    # --- Base de datos (persistencia) ---
    # SQLite local por defecto (cero configuración); en producción se puede
    # apuntar a un Postgres gratuito (Neon, Supabase, Railway...):
    #   postgresql+asyncpg://usuario:clave@host/db?ssl=require
    database_url: str = Field(
        default="sqlite+aiosqlite:///./data/pacomarca.db",
        description="URL de la base de datos (SQLite local o Postgres)",
    )
    database_echo: bool = Field(default=False, description="Registrar las sentencias SQL (debug)")

    # --- Aplicación ---
    app_env: str = Field(default="development")
    app_debug: bool = Field(default=True)
    app_host: str = Field(default="0.0.0.0")
    app_port: int = Field(default=8000)
    app_version: str = Field(default="1.0.0")

    # --- CORS (separado por comas si viene como cadena; la Union permite
    # que pydantic-settings tolere valores no-JSON y el validador los parta) ---
    allowed_origins: List[str] | str = Field(
        default=["http://localhost:5173", "http://localhost:3000"],
        description="Orígenes permitidos, separados por comas",
    )

    # --- Seguridad ---
    secret_key: str = Field(default="dev-secret-key-cambiar-en-produccion")
    rate_limit_per_minute: int = Field(default=100, description="Peticiones por minuto por IP")

    # --- Punto de control por defecto ---
    default_lat: float = Field(default=-14.85)
    default_lon: float = Field(default=-70.92)
    roi_buffer_m: int = Field(default=2000, description="Radio del área de análisis (m)")

    # --- Modelo de biomasa (heurístico) ---
    biomass_coefficient: float = Field(
        default=2800.0,
        description="Coeficiente del modelo biomasa_kg_ha = NDVI * coeficiente",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,  # permite GEE_PROJECT, Cache_TTL_Seconds, etc.
        extra="ignore",
    )

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def _parse_origins(cls, v):
        """Permite ALLOWED_ORIGINS como cadena separada por comas."""
        if isinstance(v, str):
            return [origen.strip() for origen in v.split(",") if origen.strip()]
        return v

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() in ("prod", "production")


# Instancia única de configuración
settings = Settings()
