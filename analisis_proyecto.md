# Análisis del proyecto: PACOMARCA

> **Instrucciones para Claude:** Este informe describe mi proyecto. Analízalo y: (1) resume qué hace y su arquitectura, (2) detecta problemas de interfaz/UX, accesibilidad, rendimiento y calidad de código, (3) propón mejoras priorizadas (alto/medio/bajo impacto) y (4) entrégame el código mejorado, archivo por archivo, listo para copiar.

## 1. Resumen

- Archivos analizados: **4**
- Líneas de código/texto: **698**
- Tecnologías detectadas: NumPy, Pandas, Requests, Streamlit
- Puntos de entrada probables: `app.py`
- Archivos de test: **0**
- Python: 0 clases, 13 funciones

## 2. Lenguajes

| Lenguaje | Archivos | Líneas |
|---|---:|---:|
| Python | 2 | 698 |

## 3. Estructura

```
PACOMARCA/
├── analizar_proyecto.py
├── app.py
├── requirements.txt
└── requirements.txt.txt
```

## 4. Archivos más grandes (candidatos a refactor)

- `analizar_proyecto.py` — 366 líneas
- `app.py` — 332 líneas

## 5. Señales de interfaz (UI/UX)

- Páginas HTML: 0 | Hojas CSS: 0 | Componentes (React/Vue/Svelte): 0
- Estilos inline en HTML: 0
- Media queries (responsive): 0
- Variables CSS: 0 | Soporte modo oscuro: no detectado
- Atributos de accesibilidad (aria/role): 0 | `<img>` sin alt: 0

## 7. TODO / FIXME pendientes

- `analizar_proyecto.py:317` TODO: / FIXME pendientes\n")

## 8. Código fuente relevante


### `requirements.txt`
```txt
streamlit==1.32.0
earthengine-api
geemap
pandas
numpy
plotly
requests
scikit-learn

```

### `app.py`
```py
import streamlit as st
import ee
import geemap.foliumap as geemap
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import requests
import os
from datetime import datetime, timedelta

# ==========================================
# 1. CONFIGURACIÓN INICIAL
# ==========================================
st.set_page_config(
    page_title="Pacomarca Scientific Suite", 
    layout="wide", 
    page_icon="🧬", 
    initial_sidebar_state="expanded"
)

# ==========================================
# 2. CONEXIÓN SEGURA A LA NUBE (GEE)
# ==========================================
try:
    # Intenta leer el token desde los secretos de Streamlit Cloud
    if "earth_engine" in st.secrets:
        credentials = st.secrets["earth_engine"]["token"]
        home = os.path.expanduser("~")
        path = os.path.join(home, ".config", "earthengine")
        os.makedirs(path, exist_ok=True)
        with open(os.path.join(path, "credentials"), "w") as f:
            f.write(credentials)
    
    # Inicia la conexión
    ee.Initialize(project='egresados-q9tr')

except Exception as e:
    # Si falla, muestra un mensaje amigable en lugar de romper la app
    st.warning("⚠️ Esperando autenticación. Si estás en local, usa 'ee.Authenticate()'. Si estás en la nube, revisa los 'Secrets'.")
    st.stop()

# ==========================================
# 3. ESTILOS CSS PROFESIONALES
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* BASE */
    .stApp { background-color: #F8FAFC; font-family: 'Inter', sans-serif; }
    
    /* TEXTOS OSCUROS */
    .stMarkdown, .stText, h1, h2, h3, p, li, label, span { color: #0F172A !important; }

    /* SIDEBAR */
    section[data-testid="stSidebar"] { background-color: #FFFFFF; border-right: 1px solid #E2E8F0; }
    
    /* TARJETAS */
    .metric-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        margin-bottom: 15px;
    }
    
    /* INPUTS */
    .stSelectbox div[data-baseweb="select"] > div { background-color: #FFFFFF !important; color: #0F172A !important; border-color: #CBD5E1 !important; }
    .stNumberInput input { color: #0F172A !important; background-color: #FFFFFF !important; }

    /* TABS */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; background-color: transparent; border-bottom: 2px solid #E2E8F0; }
    .stTabs [data-baseweb="tab"] { height: 45px; font-weight: 600; color: #64748B; border: none; background: transparent; }
    .stTabs [aria-selected="true"] { color: #2563EB !important; border-bottom: 3px solid #2563EB !important; background-color: transparent !important; }

    /* FOOTER */
    .footer { text-align: center; padding: 40px 0; color: #64748B; font-size: 13px; font-weight: 500; border-top: 1px solid #E2E8F0; margin-top: 50px; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 4. FUNCIONES DE PROCESAMIENTO
# ==========================================
@st.cache_data
def get_weather(lat, lon):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,rain&timezone=auto"
        return requests.get(url).json()
    except: return None

@st.cache_data
def get_chart_data(lat, lon, years):
    roi_internal = ee.Geometry.Point([lon, lat]).buffer(2000)
    end = datetime.now()
    start = end - timedelta(days=365*years)
    
    ds = ee.ImageCollection('MODIS/006/MOD13Q1') \
            .filterDate(start, end) \
            .filterBounds(roi_internal) \
            .select('NDVI')
            
    data = ds.map(lambda img: ee.Feature(None, {
        'd': img.date().format('YYYY-MM-dd'), 
        'v': img.reduceRegion(ee.Reducer.mean(), roi_internal, 250).get('NDVI')
    })).getInfo()
    
    df = pd.DataFrame([f['properties'] for f in data['features']])
    if not df.empty:
        df['d'] = pd.to_datetime(df['d'])
        df['v'] = df['v']/10000
        df = df.sort_values('d')
        # Modelo de Biomasa (Kg/Ha)
        df['biomasa'] = df['v'] * 2800 
        return df
    return pd.DataFrame()

# ==========================================
# 5. SIDEBAR
# ==========================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3063/3063835.png", width=50)
    st.markdown("### PACOMARCA\n**SCIENTIFIC SUITE**")
    
    st.markdown("---")
    st.caption("📍 PUNTO DE CONTROL")
    c_lat = st.number_input("Latitud", value=-14.85000, format="%.5f")
    c_lon = st.number_input("Longitud", value=-70.92000, format="%.5f")
    roi = ee.Geometry.Point([c_lon, c_lat]).buffer(2000)

    st.caption("🛰️ CAPAS Y MODELOS")
    layer_mode = st.radio(
        "Variable de Análisis:",
        ["Biomasa (Kg/Ha)", "Clasificación (IA)", "Radar S1 (Estructura)", "NDVI (Vigor)", "EVI (Alta Densidad)"],
        captions=[
            "Forraje Disponible", 
            "Tipos de Hábitat", 
            "Penetración de Nubes",
            "Índice Estándar",
            "Índice Mejorado"
        ],
        index=0
    )
    
    st.caption("⏳ SERIE DE TIEMPO")
    years = st.slider("Años de Análisis", 5, 23, 20)

# ==========================================
# 6. DASHBOARD PRINCIPAL
# ==========================================

# --- HEADER ---
w = get_weather(c_lat, c_lon)
if w and 'current' in w:
    temp = w['current']['temperature_2m']
    hum = w['current']['relative_humidity_2m']
    rain = w['current']['rain']
else:
    temp, hum, rain = "--", "--", "--"

st.markdown(f"""
<div style="background:white; padding:1.5rem; border-radius:12px; border:1px solid #E2E8F0; display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;">
    <div>
        <h1 style="margin:0; font-size:26px; color:#0F172A; fon
```
*(truncado)*