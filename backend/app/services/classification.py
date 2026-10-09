"""
Clasificación (IA) de hábitats altoandinos por umbrales de NDVI.

Modelo de reglas (no entrenado): es determinista, explicable y no requiere
muestras etiquetadas. Si en el futuro se entrena un clasificador supervisado
(por ejemplo con scikit-learn sobre muestras de campo), debe reemplazar el
método `classify_ndvi` manteniendo esta misma interfaz.

Umbrales por defecto calibrados para pastizales del altiplano de Puno:
    NDVI <  0.20 -> 0 Suelo desnudo
    0.20 <= NDVI < 0.45 -> 1 Pasto bajo
    NDVI >= 0.45 -> 2 Pasto alto
"""
from typing import Dict


class ClassificationService:
    """Clasificación heurística de hábitats basada en NDVI."""

    UMBRAL_PASTO_BAJO = 0.20
    UMBRAL_PASTO_ALTO = 0.45

    CLASES: Dict[int, Dict[str, str]] = {
        0: {"label": "Suelo desnudo", "color": "#d73027"},
        1: {"label": "Pasto bajo", "color": "#fee08b"},
        2: {"label": "Pasto alto", "color": "#1a9850"},
    }

    def classify_ndvi(self, ndvi: float) -> int:
        """Devuelve la clase (0, 1 o 2) para un valor de NDVI."""
        if ndvi >= self.UMBRAL_PASTO_ALTO:
            return 2
        if ndvi >= self.UMBRAL_PASTO_BAJO:
            return 1
        return 0

    def legend(self) -> Dict[str, Dict[str, str]]:
        """Leyenda de clases para la UI, con etiquetas en español."""
        return {
            str(clase): {"label": info["label"], "color": info["color"]}
            for clase, info in self.CLASES.items()
        }

    @staticmethod
    def percentages_from_histogram(histograma: Dict[str, float]) -> Dict[str, float]:
        """
        Convierte un histograma de conteo por clase en porcentajes.
        Las claves de GEE pueden venir como '0', '1', '2' o numéricas.
        """
        normalizado = {str(k): float(v) for k, v in (histograma or {}).items()}
        total = sum(normalizado.values())
        if total <= 0:
            return {"0": 0.0, "1": 0.0, "2": 0.0}
        return {
            clase: round(normalizado.get(clase, 0.0) / total * 100.0, 2)
            for clase in ("0", "1", "2")
        }
