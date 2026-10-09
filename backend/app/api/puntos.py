"""
Puntos de control: CRUD persistido en base de datos.

Permite guardar parcelas/puntos de interés (p. ej. canchas de pastoreo),
recuperarlos desde cualquier dispositivo y eliminarlos. La anomalía y las
series se calculan en vivo contra GEE; aquí solo persisten coordenadas y
metadatos del usuario.
"""
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.db.models import PuntoControl
from app.models import PuntoCreate, PuntoOut, PuntoUpdate

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/puntos", tags=["puntos de control"])


async def _obtener(db: AsyncSession, punto_id: int) -> PuntoControl:
    """Busca un punto o lanza 404."""
    punto = await db.get(PuntoControl, punto_id)
    if punto is None:
        raise HTTPException(status_code=404, detail=f"No existe el punto {punto_id}.")
    return punto


@router.get("", response_model=List[PuntoOut], summary="Lista de puntos guardados")
async def listar_puntos(
    db: AsyncSession = Depends(get_db),
    limite: int = Query(default=100, ge=1, le=500, description="Máximo de resultados"),
) -> List[PuntoControl]:
    """Puntos de control ordenados por nombre."""
    resultado = await db.execute(select(PuntoControl).order_by(PuntoControl.nombre).limit(limite))
    return list(resultado.scalars().all())


@router.post(
    "",
    response_model=PuntoOut,
    status_code=status.HTTP_201_CREATED,
    summary="Guardar un punto de control",
)
async def crear_punto(datos: PuntoCreate, db: AsyncSession = Depends(get_db)) -> PuntoControl:
    """Guarda un punto con nombre, coordenadas y radio de análisis."""
    punto = PuntoControl(**datos.model_dump())
    db.add(punto)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=409, detail="No se pudo guardar el punto (conflicto)."
        ) from exc
    await db.refresh(punto)
    logger.info("Punto guardado: %s (%s, %s)", punto.nombre, punto.lat, punto.lon)
    return punto


@router.patch("/{punto_id}", response_model=PuntoOut, summary="Editar un punto")
async def actualizar_punto(
    punto_id: int, cambios: PuntoUpdate, db: AsyncSession = Depends(get_db)
) -> PuntoControl:
    """Actualiza solo los campos enviados (nombre, coordenadas, notas...)."""
    punto = await _obtener(db, punto_id)
    for campo, valor in cambios.model_dump(exclude_unset=True).items():
        setattr(punto, campo, valor)
    await db.commit()
    await db.refresh(punto)
    return punto


@router.delete(
    "/{punto_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un punto",
)
async def eliminar_punto(punto_id: int, db: AsyncSession = Depends(get_db)) -> Response:
    """Elimina el punto y sus alertas asociadas (cascade)."""
    punto = await _obtener(db, punto_id)
    await db.delete(punto)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
