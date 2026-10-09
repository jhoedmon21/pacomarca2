"""
Fixtures comunes: cliente de prueba con GEE y Open-Meteo simulados y una base
de datos SQLite efímera por test. Así los tests no necesitan credenciales,
red ni estado compartido.
"""
import asyncio

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_gee, get_weather
from app.config import settings
from app.db import init_db, reset_engine
from app.main import create_app


class FakeGEE:
    """Doble de prueba del servicio de Earth Engine."""

    ready = True

    def ensure_ready(self) -> None:
        return None

    def get_timeseries(self, lat: float, lon: float, years: int, index: str = "ndvi"):
        return [
            {"date": "2026-01-01", "value": 0.30, "biomass": 840.0},
            {"date": "2026-01-17", "value": 0.40, "biomass": 1120.0},
        ]

    def get_classification(self, lat: float, lon: float):
        return {
            "classification_map": {"0": 10.0, "1": 30.0, "2": 60.0},
            "legend": {
                "0": {"label": "Suelo desnudo", "color": "#d73027"},
                "1": {"label": "Pasto bajo", "color": "#fee08b"},
                "2": {"label": "Pasto alto", "color": "#1a9850"},
            },
            "unit": "% del área",
        }

    def get_tile_url(self, lat: float, lon: float, layer: str):
        return {
            "url": "https://earthengine.googleapis.com/map/fake/{z}/{x}/{y}?token=t",
            "layer_name": "Capa de prueba",
            "min_val": 0.0,
            "max_val": 1.0,
            "palette": ["#ffffff", "#008000"],
            "unit": "índice",
        }

    def get_stats(self, lat: float, lon: float, years: int, layer: str = "biomasa"):
        return {
            "mean": 980.0, "max": 1120.0, "min": 840.0, "std": 140.0,
            "trend": 50.0, "anomaly_percent": 14.29, "unit": "Kg/Ha", "data_count": 2,
        }

    def crosscheck_modis_s2(self, lat: float, lon: float):
        return {
            "modis_ndvi": 0.3100,
            "s2_ndvi": 0.3400,
            "diferencia": 0.0300,
            "nota": "MODIS 250 m (media 48 días) vs Sentinel-2 10 m",
        }


class FakeWeather:
    """Doble de prueba del servicio de Open-Meteo."""

    async def get_current_weather(self, lat: float, lon: float):
        return {
            "temperature_2m": 12.5,
            "relative_humidity_2m": 60.0,
            "rain": 0.0,
            "wind_speed_10m": 3.0,
            "timestamp": "2026-10-08T10:00",
        }


@pytest.fixture
def client(tmp_path, monkeypatch) -> TestClient:
    """Cliente HTTP contra la app con dependencias simuladas y BD temporal."""
    monkeypatch.setattr(settings, "database_url", f"sqlite+aiosqlite:///{tmp_path}/test.db")
    reset_engine()
    asyncio.run(init_db())

    app = create_app()
    app.dependency_overrides[get_gee] = lambda: FakeGEE()
    app.dependency_overrides[get_weather] = lambda: FakeWeather()
    yield TestClient(app)

    reset_engine()
