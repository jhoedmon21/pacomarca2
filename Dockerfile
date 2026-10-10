# ============================================================
# Dockerfile en la raíz del repo: compila el backend para Railway.
# Railway compila desde la raíz del repositorio, así que copia las
# rutas de backend/ al contexto. (El docker-compose usa
# backend/Dockerfile con backend/ como contexto; este archivo es
# solo para Railway/plataformas que compilan desde la raíz.)
# ============================================================

# ---------- Etapa 1: dependencias ----------
FROM python:3.12-slim AS builder

WORKDIR /build

# Compiladores/librerías mínimas para wheels que no tienen binario
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir --upgrade pip \
    && /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# ---------- Etapa 2: runtime ----------
FROM python:3.12-slim

# Usuario sin privilegios (requerido por endurecimiento del contenedor)
RUN groupadd -g 1001 appgroup && useradd -u 1001 -g appgroup -m appuser \
    && mkdir -p /srv/app/data && chown -R appuser:appgroup /srv/app/data

# Traer el venv ya construido (misma imagen base => compatible)
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /srv/app
COPY backend/app ./app

USER appuser

EXPOSE 8000

# Healthcheck: si /api/health falla, Docker reinicia/marca unhealthy
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request,sys; r=urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=4); sys.exit(0 if r.status==200 else 1)"

# 1 worker por defecto: GEE mantiene estado por proceso.
# Para escalar, subir workers vía comando en docker-compose.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
