"""
Modelo de biomasa (forraje disponible).

ADVERTENCIA METODOLÓGICA
------------------------
Este es un modelo SIMPLE y HEURÍSTICO con fines de monitoreo operativo:

    biomasa_kg_ha = NDVI * coeficiente      (coeficiente = 2800 por defecto)

Suposiciones y limitaciones (documentadas para usuarios finales):
  * Relación lineal NDVI-biomasa; en la realidad se satura con cobertura alta.
  * Coeficiente único para todo el fundo; no distingue especies ni estado
    fenológico, y fue ajustado de forma empírica para pastizales altoandinos.
  * NDVI de MODIS (250 m) mezcla pixeles; usar como tendencia, no como medida
    exacta parcelaria.
  * Para decisiones de carga animal, validar con muestreo de campo (método
    de doble muestreo o jaula de exclusión).

El coeficiente es configurable vía la variable de entorno
BIOMASS_COEFFICIENT para recalibrar sin tocar código.
"""
from app.config import settings


class BiomassService:
    """Convierte NDVI en biomasa estimada (Kg/Ha) con modelo lineal."""

    def __init__(self, coefficient: float | None = None) -> None:
        self.coefficient = float(coefficient if coefficient is not None else settings.biomass_coefficient)

    def from_ndvi(self, ndvi: float) -> float:
        """
        Estima la biomasa a partir de NDVI.

        Args:
            ndvi: valor de NDVI ya escalado (típicamente -1..1).

        Returns:
            Biomasa estimada en Kg/Ha, redondeada a 2 decimales.
        """
        return round(ndvi * self.coefficient, 2)
