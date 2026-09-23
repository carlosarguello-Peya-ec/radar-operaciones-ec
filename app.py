import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import pytz

st.set_page_config(page_title="Radar Delivery - PedidosYa", layout="wide", initial_sidebar_state="collapsed")

# Estilo corporativo limpio y responsivo
st.markdown("""
<style>
    .stApp { background-color: #F7F7F7; }
    h1, h2 { color: #EA044E !important; font-family: 'Arial', sans-serif; }
    div[data-testid="stMetricValue"] { color: #EA044E !important; font-weight: bold; }
    div[data-testid="stDataFrame"] { width: 100% !important; }
</style>
""", unsafe_allow_html=True)

# Coordenadas extraídas de los mapas operativos de PedidosYa
ZONAS_LOGISTICAS = {
    "📍 UIO (Quito y Valles)": {
        "Norte (Mitad del Mundo / Carcelén)": {"lat": -0.0450, "lon": -78.4600},
        "Carapungo / Calderón": {"lat": -0.0950, "lon": -78.4400},
        "Centro (Bicentenario a Centro Histórico)": {"lat": -0.1800, "lon": -78.4800},
        "Sur (Todo el Sur)": {"lat": -0.2800, "lon": -78.5400},
        "Cumbayá y Tumbaco": {"lat": -0.2100, "lon": -78.4000},
        "Valle de los Chillos": {"lat": -0.2900, "lon": -78.4500}
    },
    "📍 GYE (Guayaquil y Alrededores)": {
        "Centro / Norte": {"lat": -2.1450, "lon": -79.9000},
        "Oeste (Vía a la Costa)": {"lat": -2.1850, "lon": -79.9500},
        "Samborondón / La Aurora": {"lat": -2.1150, "lon": -79.8700},
        "Sur (Todo el Sur)": {"lat": -2.2350, "lon": -79.8950},
        "Durán": {"lat": -2.1750, "lon": -79.8250}
    }
}

def obtener_datos_clima(lat, lon):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=precipitation&hourly=precipitation&timezone=America%2FGuayaquil&forecast_days=2"
    try:
        response = requests.get(url, timeout=5).json()
        lluvia_actual = response.get("current", {}).get("precipitation", 0.0)
        
        horas = response["hourly"]["time"]
        lluvias = response["hourly"]["precipitation"]
        hora_actual_str = response["current"]["time"][:13]
        
        idx = next((i for i, t in enumerate(horas) if t.startswith(hora_actual_str)), 0)
        labels_6h = [h[-5:] for h in horas[idx:idx+6]]
        valores_6h = lluvias[idx:idx+6]
        
        return lluvia_actual, labels_6h, valores_6h
    except Exception:
        return None, [], []

def mostrar_tarjeta_zona(nombre, lluvia_mm, labels_6h, valores_6h):
    if lluvia_mm is None:
        st.error(f"{nombre} - Sin conexión a la API")
        return

    if lluvia_mm >= 7.5: estado, icono = "Alerta: Lluvia Fuerte", "🚨"
    elif lluvia_mm >= 2.0: estado, icono = "Precaución: Lluvia Moderada", "🌧️"
    elif lluvia_mm > 0: estado, icono = "Operación Normal: Garúa", "💧"
    else: estado, icono = "Operación Normal: Seco", "☀️"

    with st.container(border=True):
        st.markdown(f"<p style='margin:0; font-weight:bold; color:#333; font-size:1.1rem;'>{nombre}</p>", unsafe_allow_html=True)
        st.metric(label=f"{icono} {estado}", value=f"{lluvia_mm} mm/h")
        
        if labels_6h:
            df = pd.DataFrame({"Hora": labels_6h, "Lluvia (mm/h)": valores_6h})
            st.markdown("<p style='font-size:0.8rem; color:#666; margin-top:5px; margin-bottom:2px;'>Pronóstico (Próximas 6h)</p>", unsafe_allow_html=True)
            st.dataframe(df, use_container_width=True, hide_index=True, height=230)

@st.fragment(run_every="5m") 
def tablero_tiempo_real():
    tz_ec = pytz.timezone('America/Guayaquil')
    hora_ec = datetime.now(tz_ec).strftime('%Y-%m-%d %H:%M:%S')
    
    st.title("Radar Delivery - Operaciones")
    st.caption(f"Última actualización: **{hora_ec}** | Actualización automática cada 5 minutos")
    st.divider()
    
    # Distribución responsiva
    col_uio, col_gye = st.columns(2)
    
    with col_uio:
        st.header("🏔️ Quito")
        for nombre, coords in ZONAS_LOGISTICAS["📍 UIO (Quito y Valles)"].items():
            ll, labels, vals = obtener_datos_clima(coords["lat"], coords["lon"])
            mostrar_tarjeta_zona(nombre, ll, labels, vals)

    with col_gye:
        st.header("🌊 Guayaquil")
        for nombre, coords in ZONAS_LOGISTICAS["📍 GYE (Guayaquil y Alrededores)"].items():
            ll, labels, vals = obtener_datos_clima(coords["lat"], coords["lon"])
            mostrar_tarjeta_zona(nombre, ll, labels, vals)

tablero_tiempo_real()
