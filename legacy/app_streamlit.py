import os

# Workaround para geemap 0.37.x: fuerza el backend folium al importar el paquete.
# Evita: BoxKeyError "'Box' object has no attribute 'xyz_to_folium'"
os.environ.setdefault("USE_FOLIUM", "1")

import streamlit as st
import ee
import geemap.foliumap as geemap
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import requests
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
    # Intenta leer el token desde los secretos de Streamlit Cloud (si existen)
    try:
        if "earth_engine" in st.secrets:
            credentials = st.secrets["earth_engine"]["token"]
            home = os.path.expanduser("~")
            path = os.path.join(home, ".config", "earthengine")
            os.makedirs(path, exist_ok=True)
            with open(os.path.join(path, "credentials"), "w") as f:
                f.write(credentials)
    except FileNotFoundError:
        # No hay secrets.toml local: se usan las credenciales ya guardadas en el equipo
        pass
    
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
        <h1 style="margin:0; font-size:26px; color:#0F172A; font-weight:800;">Fundo Pacomarca</h1>
        <p style="margin:0; color:#64748B; font-size:14px;">Plataforma de Inteligencia Agronómica</p>
    </div>
    <div style="display:flex; gap:30px; text-align:right;">
        <div><span style="font-size:22px; font-weight:700; color:#0F172A;">{temp}°</span><br><span style="font-size:11px; color:#94A3B8; font-weight:600;">AIRE</span></div>
        <div><span style="font-size:22px; font-weight:700; color:#2563EB;">{hum}%</span><br><span style="font-size:11px; color:#94A3B8; font-weight:600;">HUMEDAD</span></div>
        <div><span style="font-size:22px; font-weight:700; color:#059669;">{rain}</span><br><span style="font-size:11px; color:#94A3B8; font-weight:600;">LLUVIA</span></div>
    </div>
</div>
""", unsafe_allow_html=True)

# --- VISOR Y KPI ---
c1, c2 = st.columns([3, 1])

with c1:
    with st.container():
        st.markdown('<div style="background:white; padding:10px; border-radius:12px; border:1px solid #E2E8F0;">', unsafe_allow_html=True)
        m = geemap.Map(center=[c_lat, c_lon], zoom=14, basemap="HYBRID")
        s2 = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED").filterBounds(roi).filterDate(datetime.now()-timedelta(days=60), datetime.now()).sort('CLOUDY_PIXEL_PERCENTAGE').first()
        
        val_disp = 0
        unit = ""
        legend_label = ""
        
        # LOGICA DE CAPAS OPTIMIZADA PARA NUBE (SIN CRASHES)
        if s2 or layer_mode == "Radar S1 (Estructura)":
            
            # 1. BIOMASA
            if layer_mode == "Biomasa (Kg/Ha)":
                if s2:
                    ndvi = s2.normalizedDifference(['B8', 'B4'])
                    img = ndvi.multiply(2800).rename('Biomasa')
                    vis = {'min': 0, 'max': 2500, 'palette': ['#ffffe5', '#f7fcb9', '#addd8e', '#41ab5d', '#005a32']}
                    legend_label = "Biomasa (Forraje)"
                    unit = "Kg/Ha"
                    m.addLayer(img.clip(roi), vis, layer_mode)
                    
            # 2. CLASIFICACIÓN (OPTIMIZADO: Sin WekaKMeans que rompe la nube)
            elif layer_mode == "Clasificación (IA)":
                if s2:
                    ndvi = s2.normalizedDifference(['B8', 'B4'])
                    # Clasificación Robust: 0=Suelo (Rojo), 1=Pasto Bajo (Amarillo), 2=Pasto Alto (Verde)
                    # Esta lógica es mucho más rápida y no falla en Streamlit Cloud
                    img = ee.Image(0).where(ndvi.gte(0.2), 1).where(ndvi.gte(0.45), 2).clip(roi)
                    vis = {'min': 0, 'max': 2, 'palette': ['#d73027', '#fee08b', '#1a9850']}
                    legend_label = "Clase de Hábitat"
                    unit = "ID"
                    m.addLayer(img, vis, layer_mode)
                    
            # 3. RADAR
            elif layer_mode == "Radar S1 (Estructura)":
                s1 = ee.ImageCollection('COPERNICUS/S1_GRD').filterBounds(roi).filterDate(datetime.now()-timedelta(days=30), datetime.now()).first()
                if s1:
                    img = s1.select('VV')
                    vis = {'min': -25, 'max': 5}
                    legend_label = "Retrodispersión SAR"
                    unit = "dB"
                    m.addLayer(img.clip(roi), vis, layer_mode)
                else:
                    st.toast("⚠️ No hay imagen de Radar reciente disponible.")
                    
            # 4. EVI
            elif layer_mode == "EVI":
                if s2:
                    img = s2.expression('2.5 * ((NIR - RED) / (NIR + 6 * RED - 7.5 * BLUE + 1))', {'NIR': s2.select('B8'), 'RED': s2.select('B4'), 'BLUE': s2.select('B2')})
                    vis = {'min': 0, 'max': 1, 'palette': ['white', 'green']}
                    legend_label = "Índice EVI"
                    unit = "idx"
                    m.addLayer(img.clip(roi), vis, layer_mode)
                    
            # 5. NDVI
            else: 
                if s2:
                    img = s2.normalizedDifference(['B8', 'B4'])
                    vis = {'min': 0, 'max': 0.8, 'palette': ['#d73027', '#fdae61', '#d9ef8b', '#1a9850']}
                    legend_label = "Vigor NDVI"
                    unit = "idx"
                    m.addLayer(img.clip(roi), vis, layer_mode)

            # Capa límite y cálculo de promedio
            m.addLayer(roi, {'color': 'white', 'width': 2, 'fillColor': '00000000'}, "Límite")
            
            # Intentar calcular valor promedio (si existe imagen óptica)
            try:
                if layer_mode != "Radar S1 (Estructura)" and s2:
                    # Usamos la imagen calculada arriba
                    calc_img = img if 'img' in locals() else s2.normalizedDifference(['B8', 'B4'])
                    val_disp = calc_img.reduceRegion(ee.Reducer.mean(), roi, 20).getInfo().get(list(calc_img.bandNames().getInfo())[0], 0)
                elif layer_mode == "Radar S1 (Estructura)" and 'img' in locals():
                     val_disp = img.reduceRegion(ee.Reducer.mean(), roi, 20).getInfo().get('VV', 0)
            except: val_disp = 0

        m.to_streamlit(height=480)
        st.markdown('</div>', unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="metric-card" style="text-align:center; height:100%; display:flex; flex-direction:column; justify-content:center;">
        <div style="font-size:12px; font-weight:700; color:#64748B; margin-bottom:10px;">PROMEDIO ZONAL</div>
        <div style="font-size:42px; font-weight:800; color:#0F172A; letter-spacing:-1px;">{val_disp:.2f}</div>
        <div style="font-size:14px; font-weight:600; color:#2563EB; margin-bottom:20px;">{unit}</div>
        <div style="height:5px; width:100%; background:#F1F5F9; border-radius:3px;">
            <div style="height:100%; width:60%; background:#0F172A; border-radius:3px;"></div>
        </div>
        <p style="margin-top:20px; font-size:13px; color:#475569; line-height:1.4;">
            {legend_label}<br>Dato satelital en tiempo real.
        </p>
    </div>
    """, unsafe_allow_html=True)

# --- ANALYTICS ---
st.write("")
st.markdown("### 📊 Análisis de Tendencias y Alertas")
st.markdown("<p style='color:#475569; font-size:14px;'>Evaluación de dinámica temporal y detección de anomalías.</p>", unsafe_allow_html=True)

df = get_chart_data(c_lat, c_lon, years)

if not df.empty:
    with st.container():
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["Dinámica Temporal", "Monitor de Alertas"])
        
        with tab1:
            variable_plot = 'biomasa' if "Biomasa" in layer_mode else 'v'
            y_label = "Biomasa (Kg/Ha)" if "Biomasa" in layer_mode else "Valor Índice"
            
            # Gráfico con configuración de texto negro explícita
            fig = px.area(df, x='d', y=variable_plot, height=350)
            fig.update_traces(line_color='#2563EB', fillcolor='rgba(37, 99, 235, 0.1)')
            fig.update_layout(
                plot_bgcolor='white', 
                paper_bgcolor='white',
                margin=dict(l=20,r=20,t=20,b=20),
                xaxis=dict(showgrid=False, title="", tickfont=dict(color='#0F172A')),
                yaxis=dict(showgrid=True, gridcolor='#F1F5F9', title=dict(text=y_label, font=dict(color='#0F172A')), tickfont=dict(color='#0F172A')),
                font=dict(family="Inter", color="#0F172A")
            )
            st.plotly_chart(fig, use_container_width=True)

        with tab2:
            current_val = df[variable_plot].iloc[-1]
            hist_mean = df[variable_plot].mean()
            anomaly = ((current_val - hist_mean) / hist_mean) * 100
            
            col_a, col_b = st.columns([2, 1])
            with col_a:
                if anomaly < -15:
                    st.error(f"🚨 **ALERTA DETECTADA:** Degradación Significativa (-{abs(anomaly):.1f}%)")
                    st.markdown("El valor actual está muy por debajo del promedio histórico.")
                elif anomaly > 15:
                    st.success(f"🌱 **CONDICIÓN FAVORABLE:** Superávit (+{anomaly:.1f}%)")
                    st.markdown("Condiciones superiores al promedio histórico.")
                else:
                    st.info(f"⚖️ **ESTABLE:** Variación Normal ({anomaly:.1f}%)")
                    st.markdown("Los valores se mantienen dentro del rango esperado.")
            
            with col_b:
                st.metric("Promedio Histórico", f"{hist_mean:.2f}", f"{anomaly:.1f}% vs Promedio")

        st.markdown('</div>', unsafe_allow_html=True)

# --- FIRMA ---
st.markdown("""
<div class="footer">
    Jhon Monroy | Experto en Informática
</div>
""", unsafe_allow_html=True)
