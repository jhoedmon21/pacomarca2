"""
Tests de la clasificación heurística de hábitats por umbrales de NDVI.
"""
from app.services.classification import ClassificationService


def test_umbral_suelo_desnudo():
    servicio = ClassificationService()
    assert servicio.classify_ndvi(0.0) == 0
    assert servicio.classify_ndvi(0.19) == 0


def test_umbral_pasto_bajo():
    servicio = ClassificationService()
    assert servicio.classify_ndvi(0.20) == 1  # límite inclusivo
    assert servicio.classify_ndvi(0.44) == 1


def test_umbral_pasto_alto():
    servicio = ClassificationService()
    assert servicio.classify_ndvi(0.45) == 2  # límite inclusivo
    assert servicio.classify_ndvi(0.9) == 2


def test_histograma_a_porcentajes():
    porcentajes = ClassificationService.percentages_from_histogram({"0": 10, "1": 30, "2": 60})
    assert porcentajes == {"0": 10.0, "1": 30.0, "2": 60.0}


def test_histograma_vacio_devuelve_ceros():
    porcentajes = ClassificationService.percentages_from_histogram({})
    assert porcentajes == {"0": 0.0, "1": 0.0, "2": 0.0}


def test_leyenda_en_espanol():
    leyenda = ClassificationService().legend()
    assert leyenda["0"]["label"] == "Suelo desnudo"
    assert leyenda["1"]["label"] == "Pasto bajo"
    assert leyenda["2"]["label"] == "Pasto alto"
    assert all("color" in info for info in leyenda.values())
