# Legacy — aplicación Streamlit (retirada)

Esta carpeta conserva la aplicación original de Streamlit **solo como
referencia histórica**. Ya no forma parte del proyecto activo y no se
despliega ni se mantiene.

## Por qué se retiró

- `app.py` (Streamlit) mezclaba UI, lógica y acceso a datos en un solo
  archivo, sin base de datos, sin tests y sin caché compartida.
- La suite actual la reemplaza por una arquitectura API + SPA:

```
backend/   FastAPI + SQLAlchemy (base de datos) + Redis + GEE
frontend/  React 18 + TypeScript + Vite + Tailwind + MapLibre
deploy/    Jobs (alerta diaria) y despliegue con Caddy + Docker
```

## Si necesitas ejecutarla puntualmente

```bash
cd legacy
pip install -r requirements-streamlit.txt
streamlit run app_streamlit.py
```

Requiere credenciales de Google Earth Engine (`ee.Authenticate()` o la
cuenta de servicio configurada), igual que la versión original.
