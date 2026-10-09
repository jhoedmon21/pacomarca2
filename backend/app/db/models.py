"""
Modelos ORM (SQLAlchemy 2.0, tipados).

- PuntoControl: parcelas/puntos monitoreados guardados por el usuario.
- RegistroAlerta: historial persistente de alertas generadas por el job diario
  (o manualmente) para auditar la evolución de las degradaciones.
"""
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _ahora() -> datetime:
    """UTC con zona horaria explícita (independiente del reloj del contenedor)."""
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """Base declarativa compartida."""


class PuntoControl(Base):
    """Punto/parcela de monitoreo guardado por el usuario."""

    __tablename__ = "puntos_control"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lon: Mapped[float] = mapped_column(Float, nullable=False)
    buffer_m: Mapped[int] = mapped_column(Integer, nullable=False, default=2000)
    notas: Mapped[str | None] = mapped_column(Text, nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_ahora)
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_ahora, onupdate=_ahora
    )

    alertas: Mapped[list["RegistroAlerta"]] = relationship(
        back_populates="punto", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover - depuración
        return f"<PuntoControl {self.id} {self.nombre!r} ({self.lat}, {self.lon})>"


class RegistroAlerta(Base):
    """Alerta histórica: anomalía detectada sobre un punto en una fecha dada."""

    __tablename__ = "registros_alerta"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    punto_id: Mapped[int | None] = mapped_column(
        ForeignKey("puntos_control.id", ondelete="SET NULL"), nullable=True, index=True
    )
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lon: Mapped[float] = mapped_column(Float, nullable=False)
    indice: Mapped[str] = mapped_column(String(20), nullable=False, default="biomasa")
    valor_actual: Mapped[float] = mapped_column(Float, nullable=False)
    promedio_historico: Mapped[float] = mapped_column(Float, nullable=False)
    anomalia_pct: Mapped[float] = mapped_column(Float, nullable=False)
    severidad: Mapped[str] = mapped_column(String(10), nullable=False, default="alerta")
    mensaje: Mapped[str | None] = mapped_column(Text, nullable=True)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_ahora, index=True
    )

    punto: Mapped[PuntoControl | None] = relationship(back_populates="alertas")

    def __repr__(self) -> str:  # pragma: no cover - depuración
        return f"<RegistroAlerta {self.id} {self.anomalia_pct:+.1f}% {self.severidad}>"
