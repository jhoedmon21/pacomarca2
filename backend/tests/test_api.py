"""
Tests de integración de la API (con dependencias simuladas).
"""
from fastapi.testclient import TestClient

from app.api.deps import get_gee, get_weather
from app.config import settings
from app.main import create_app
from tests.conftest import FakeGEE, FakeWeather


# ---------------------------------------------------------------- salud
def test_health_ok(client: TestClient):
    respuesta = client.get("/api/health")
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["status"] in ("ok", "degradado")
    assert cuerpo["version"] == settings.app_version
    assert "gee_status" in cuerpo


# ---------------------------------------------------------------- clima
def test_weather_devuelve_datos(client: TestClient):
    respuesta = client.get("/api/weather", params={"lat": -14.85, "lon": -70.92})
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["temperature_2m"] == 12.5
    assert cuerpo["relative_humidity_2m"] == 60.0
    assert cuerpo["rain"] == 0.0


def test_weather_lat_invalida_da_422_en_espanol(client: TestClient):
    respuesta = client.get("/api/weather", params={"lat": 200, "lon": -70.92})
    assert respuesta.status_code == 422
    cuerpo = respuesta.json()
    assert cuerpo["error"] == "Error de validación"
    assert cuerpo["details"][0]["field"] == "lat"


# ---------------------------------------------------------------- series
def test_timeseries_json(client: TestClient):
    respuesta = client.get("/api/timeseries", params={"lat": -14.85, "lon": -70.92, "years": 5, "index": "ndvi"})
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert len(cuerpo["data"]) == 2
    assert cuerpo["index"] == "ndvi"
    assert cuerpo["data"][0]["biomass"] == 840.0


def test_timeseries_csv(client: TestClient):
    respuesta = client.get("/api/timeseries", params={"lat": -14.85, "lon": -70.92, "years": 5, "index": "biomasa", "format": "csv"})
    assert respuesta.status_code == 200
    assert respuesta.headers["content-type"].startswith("text/csv")
    assert "fecha,valor,biomasa_kg_ha" in respuesta.text
    assert "attachment" in respuesta.headers["content-disposition"]


def test_timeseries_years_fuera_de_rango(client: TestClient):
    assert client.get("/api/timeseries", params={"lat": -14.85, "lon": -70.92, "years": 0}).status_code == 422
    assert client.get("/api/timeseries", params={"lat": -14.85, "lon": -70.92, "years": 27}).status_code == 422


def test_timeseries_index_inexistente(client: TestClient):
    respuesta = client.get("/api/timeseries", params={"lat": -14.85, "lon": -70.92, "index": "ndwi"})
    assert respuesta.status_code == 422


# ---------------------------------------------------------------- tiles
def test_tiles_devuelve_plantilla_xyz(client: TestClient):
    respuesta = client.get("/api/tiles/ndvi", params={"lat": -14.85, "lon": -70.92})
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert "{z}" in cuerpo["url"] and "{x}" in cuerpo["url"] and "{y}" in cuerpo["url"]
    assert cuerpo["palette"]


def test_tiles_capa_inexistente(client: TestClient):
    assert client.get("/api/tiles/noexiste", params={"lat": -14.85, "lon": -70.92}).status_code == 422


def test_tiles_nuevas_capas_savi_y_ndwi(client: TestClient):
    for capa in ("savi", "ndwi"):
        respuesta = client.get(f"/api/tiles/{capa}", params={"lat": -14.85, "lon": -70.92})
        assert respuesta.status_code == 200
        assert "{z}" in respuesta.json()["url"]


# ---------------------------------------------------------------- límite de años
def test_timeseries_26_anios_permitidos(client: TestClient):
    respuesta = client.get("/api/timeseries", params={"lat": -14.85, "lon": -70.92, "years": 26})
    assert respuesta.status_code == 200


def test_timeseries_27_anios_falla(client: TestClient):
    assert client.get("/api/timeseries", params={"lat": -14.85, "lon": -70.92, "years": 27}).status_code == 422


# ---------------------------------------------------------------- crosscheck
def test_crosscheck_comparacion_de_escalas(client: TestClient):
    respuesta = client.get("/api/crosscheck", params={"lat": -14.85, "lon": -70.92})
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["modis_ndvi"] == 0.31
    assert cuerpo["s2_ndvi"] == 0.34
    assert cuerpo["diferencia"] == 0.03
    assert "MODIS" in cuerpo["nota"]


# ---------------------------------------------------------------- métricas
def test_metrics_expone_contadores_prometheus():
    app = create_app()
    cliente = TestClient(app)
    cliente.get("/")
    cliente.get("/api/health")
    respuesta = cliente.get("/metrics")
    assert respuesta.status_code == 200
    texto = respuesta.text
    assert "pacomarca_http_requests_total" in texto
    assert 'estado="200"' in texto
    assert "pacomarca_http_latency_ms_sum" in texto


def test_metrics_agrega_rutas_desconocidas():
    # Una ruta desconocida larga se agrega como <otra>, sin cardinalidad infinita
    app = create_app()
    cliente = TestClient(app)
    cliente.get("/ruta-desconocida-larguisima-que-no-existe-1234567890")
    texto = cliente.get("/metrics").text
    assert "<otra>" in texto
    assert "/ruta-desconocida-larguisima" not in texto


# ---------------------------------------------------------------- clasificación
def test_classification_porcentajes(client: TestClient):
    respuesta = client.get("/api/classification", params={"lat": -14.85, "lon": -70.92})
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["classification_map"]["2"] == 60.0
    assert len(cuerpo["legend"]) == 3


# ---------------------------------------------------------------- estadísticas
def test_stats_resumen(client: TestClient):
    respuesta = client.get("/api/stats", params={"lat": -14.85, "lon": -70.92, "years": 20, "layer": "biomasa"})
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["mean"] == 980.0
    assert cuerpo["unit"] == "Kg/Ha"
    assert cuerpo["data_count"] == 2


# ---------------------------------------------------------------- rate limit
def test_rate_limit_devuelve_429(monkeypatch):
    monkeypatch.setattr(settings, "rate_limit_per_minute", 3)
    app = create_app()
    cliente = TestClient(app)

    estados = [cliente.get("/").status_code for _ in range(4)]
    assert estados[:3] == [200, 200, 200]
    assert estados[3] == 429
    cuerpo_429 = cliente.get("/").json()
    assert cuerpo_429["error"] == "rate_limit"


def test_health_no_consume_cuota_de_rate_limit(monkeypatch):
    monkeypatch.setattr(settings, "rate_limit_per_minute", 3)
    app = create_app()
    cliente = TestClient(app)
    # Health está exento: nunca debe devolver 429
    for _ in range(6):
        assert cliente.get("/api/health").status_code == 200


# ---------------------------------------------------------------- ruta desconocida
def test_ruta_desconocida_da_404_json(client: TestClient):
    respuesta = client.get("/api/no-existe")
    assert respuesta.status_code == 404


# ---------------------------------------------------------------- caché de weather
def test_weather_segunda_llamada_usa_cache(client: TestClient, monkeypatch):
    """La segunda llamada con mismas coordenadas debe salir del caché:
    forzamos un fallo del servicio real; si el caché funciona, no se invoca."""
    llamadas = {"n": 0}

    class WeatherQueCuenta(FakeWeather):
        async def get_current_weather(self, lat, lon):
            llamadas["n"] += 1
            return await super().get_current_weather(lat, lon)

    from app.api import weather as modulo_weather
    monkeypatch.setattr(modulo_weather, "get_weather", lambda: WeatherQueCuenta())
    # Re-registramos el override con el nuevo proveedor
    app = client.app  # type: ignore[attr-defined]
    app.dependency_overrides[get_weather] = lambda: WeatherQueCuenta()

    cliente = TestClient(app)
    cliente.get("/api/weather", params={"lat": -10.11, "lon": -70.22})
    cliente.get("/api/weather", params={"lat": -10.11, "lon": -70.22})
    assert llamadas["n"] == 1
