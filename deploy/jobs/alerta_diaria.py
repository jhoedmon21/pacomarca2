"""
Job de alerta diaria: revisa la anomalía de biomasa del punto por defecto,
registra cada alerta en la base de datos (historial del dashboard) y envía un
correo si la degradación supera el umbral configurado.

Ejecución manual (dentro del VPS):
    docker compose --profile jobs run --rm alerta

Programación (cron del host, ejemplo 07:00 todos los días):
    0 7 * * * cd /srv/pacomarca && docker compose --profile jobs run --rm alerta >> /var/log/pacomarca-alerta.log 2>&1

El registro en base de datos siempre se intenta (no requiere configuración);
el correo solo se envía si SMTP_HOST y ALERTA_EMAIL_DESTINO están definidos
(SMTP_USER/SMTP_PASS si el servidor exige autenticación).
"""
import os
import smtplib
import sys
from email.mime.text import MIMEText

import httpx

API_URL = os.environ.get("API_URL", "http://backend:8000")
LAT = os.environ.get("DEFAULT_LAT", "-14.85")
LON = os.environ.get("DEFAULT_LON", "-70.92")
ANIOS = os.environ.get("ANIOS_ALERTA", "20")
UMBRAL = float(os.environ.get("ALERTA_UMBRAL_PORCENTAJE", "-15"))
SMTP_HOST = os.environ.get("SMTP_HOST", "")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASS = os.environ.get("SMTP_PASS", "")
DESTINO = os.environ.get("ALERTA_EMAIL_DESTINO", "")


def enviar(asunto: str, cuerpo: str) -> None:
    """Envía un correo de texto plano por SMTP con STARTTLS."""
    mensaje = MIMEText(cuerpo, "plain", "utf-8")
    mensaje["Subject"] = asunto
    mensaje["From"] = SMTP_USER or "pacomarca@localhost"
    mensaje["To"] = DESTINO
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as smtp:
        smtp.starttls()
        if SMTP_USER and SMTP_PASS:
            smtp.login(SMTP_USER, SMTP_PASS)
        smtp.send_message(mensaje)


def severidad(anomalia: float) -> str:
    """Clasifica la anomalía según el umbral configurado."""
    if anomalia <= UMBRAL * 2:
        return "critica"
    return "alerta"


def registrar_en_db(datos: dict, anomalia: float) -> bool:
    """Persiste la alerta vía POST /api/alertas (historial del dashboard)."""
    try:
        respuesta = httpx.post(
            f"{API_URL}/api/alertas",
            json={
                "lat": float(LAT),
                "lon": float(LON),
                "indice": "biomasa",
                "valor_actual": float(datos.get("anomaly_percent", 0.0)),
                "promedio_historico": float(datos.get("mean", 0.0)),
                "anomalia_pct": anomalia,
                "severidad": severidad(anomalia),
                "mensaje": (
                    f"Degradación de biomasa {anomalia:+.2f}% vs promedio "
                    f"histórico ({ANIOS} años) detectada por el job diario."
                ),
            },
            timeout=30,
        )
        respuesta.raise_for_status()
        return True
    except Exception as exc:  # noqa: BLE001 - el correo no debe bloquearse por esto
        print(f"AVISO: no se pudo registrar la alerta en la base de datos: {exc}")
        return False


def main() -> int:
    respuesta = httpx.get(
        f"{API_URL}/api/stats",
        params={"lat": LAT, "lon": LON, "years": ANIOS, "layer": "biomasa"},
        timeout=120,
    )
    respuesta.raise_for_status()
    datos = respuesta.json()

    anomalia = float(datos.get("anomaly_percent", 0.0))
    print(f"Anomalía de biomasa: {anomalia:+.2f}% (umbral de alerta {UMBRAL}%)")

    if anomalia > UMBRAL:
        print("Sin alerta: dentro del rango esperado.")
        return 0

    registrado = registrar_en_db(datos, anomalia)
    print(f"Alerta {'registrada en' if registrado else 'NO registrada en'} la base de datos.")

    if not SMTP_HOST or not DESTINO:
        print("SMTP_HOST o ALERTA_EMAIL_DESTINO sin configurar: no se envía correo.")
        return 0

    cuerpo = (
        "Degradación de forraje detectada en Pacomarca\n"
        "=============================================\n\n"
        f"Punto de control: lat {LAT}, lon {LON}\n"
        f"Anomalía vs promedio histórico ({ANIOS} años): {anomalia:+.2f}%\n"
        f"Promedio histórico: {datos.get('mean')} {datos.get('unit')}\n"
        f"Último valor de la serie: ver dashboard.\n\n"
        "Revisa el dashboard para ver la serie completa y el mapa de la capa.\n\n"
        "-- Pacomarca Scientific Suite"
    )
    enviar(f"[Pacomarca] Alerta de degradación {anomalia:+.1f}%", cuerpo)
    print("Alerta enviada por correo.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001 - job desatendido: log y salir con error
        print(f"ERROR en la alerta diaria: {exc}", file=sys.stderr)
        sys.exit(1)
