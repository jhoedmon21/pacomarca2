"""
Historial de alertas persistido en base de datos.

El job diario (`deploy/jobs/alerta_diaria.py`) registra aquí cada degradación
detectada vía POST; el dashboard las lista para auditar la evolución.
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.db.models import PuntoControl, RegistroAlerta
from app.models import AlertaCreate, AlertaOut

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/alertas", tags=["alertas"])


@router.get("", response_model=List[AlertaOut], summary="Historial de alertas")
async def listar_alertas(
    db: AsyncSession = Depends(get_db),
    limite: int = Query(default=50, ge=1, le=500, description="Máximo de resultados"),
    punto_id: Optional[int] = Query(default=None, description="Filtrar por punto de control"),
) -> List[RegistroAlerta]:
    """Alertas más recientes primero; opcionalmente de un solo punto."""
    consulta = select(RegistroAlerta).order_by(desc(RegistroAlerta.creado_en)).limit(limite)
    if punto_id is not None:
        consulta = consulta.where(RegistroAlerta.punto_id == punto_id)
    resultado = await db.execute(consulta)
    return list(resultado.scalars().all())


@router.post(
    "",
    response_model=AlertaOut,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar una alerta",
)
async def registrar_alerta(datos: AlertaCreate, db: AsyncSession = Depends(get_db)) -> RegistroAlerta:
    """Registra una alerta. Si `punto_id` viene, se valida que exista."""
    if datos.punto_id is not None and await db.get(PuntoControl, datos.punto_id) is None:
        raise HTTPException(
            status_code=404, detail=f"No existe el punto {datos.punto_id} para vincular la alerta."
        )
    alerta = RegistroAlerta(**datos.model_dump())
    db.add(alerta)
    await db.commit()
    await db.refresh(alerta)
    logger.info("Alerta registrada: %s (anomalía %+.1f%%)", alerta.severidad, alerta.anomalia_pct)
    return alerta
