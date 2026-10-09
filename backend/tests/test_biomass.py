"""
Tests del modelo heurístico de biomasa (Kg/Ha = NDVI * coeficiente).
"""
from app.config import settings
from app.services.biomass import BiomassService


def test_modelo_por_defecto_usa_coeficiente_2800():
    servicio = BiomassService()
    assert servicio.coefficient == 2800.0
    assert servicio.from_ndvi(0.5) == 1400.0


def test_coeficiente_configurable():
    servicio = BiomassService(coefficient=1000.0)
    assert servicio.from_ndvi(0.5) == 500.0


def test_ndvi_cero_da_biomasa_cero():
    assert BiomassService().from_ndvi(0.0) == 0.0


def test_redondeo_a_dos_decimales():
    assert BiomassService().from_ndvi(0.333333) == 933.33


def test_coherencia_con_configuracion_global():
    # El servicio debe reflejar BIOMASS_COEFFICIENT si cambia la configuración
    assert BiomassService().coefficient == settings.biomass_coefficient
