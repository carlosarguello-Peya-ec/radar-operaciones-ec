import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import pytz
import io

st.set_page_config(page_title="Weather Ops - PedidosYa", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    .stApp { background-color: #F7F7F7; }
    h1, h2, h3 { color: #EA044E !important; font-family: 'Arial', sans-serif; }
    div[data-testid="stMetricValue"] { color: #EA044E !important; font-weight: bold; }
    div[data-testid="stDataFrame"] { width: 100% !important; }
    .stTabs [data-baseweb="tab-list"] { gap: 20px; }
    .stTabs [data-baseweb="tab"] { font-weight: bold; color: #666; }
    .stTabs [aria-selected="true"] { color: #EA044E !important; border-bottom-color: #EA044E !important; }
</style>
""", unsafe_allow_html=True)

# 1. DICCIONARIO UNIFICADO CON TODAS LAS CIUDADES
COBERTURA_PEYA = {
    "Quito": { 
        "Norte": {"lat": -0.045, "lon": -78.46}, 
        "Carapungo": {"lat": -0.095, "lon": -78.44}, 
        "Centro": {"lat": -0.18, "lon": -78.48}, 
        "Sur": {"lat": -0.28, "lon": -78.54}, 
        "Cumbaya_Tumbaco": {"lat": -0.21, "lon": -78.40}, 
        "Valle_Chillos": {"lat": -0.29, "lon": -78.45} 
    },
    "Guayaquil": { 
        "Centro_Norte": {"lat": -2.145, "lon": -79.90}, 
        "Oeste": {"lat": -2.185, "lon": -79.95}, 
        "Samborondon_Aurora": {"lat": -2.115, "lon": -79.87}, 
        "Sur": {"lat": -2.235, "lon": -79.89}, 
        "Duran": {"lat": -2.175, "lon": -79.82} 
    },
    "Potential Cities": { 
        "Cuenca": {"lat": -2.9000, "lon": -79.0000}, 
        "Ambato": {"lat": -1.2417, "lon": -78.6167}, 
        "Riobamba": {"lat": -1.6700, "lon": -78.6500},
        "Machala": {"lat": -3.2583, "lon": -79.9605}, 
        "Manta": {"lat": -0.9500, "lon": -80.7167}, 
        "Santo Domingo": {"lat": -0.2500, "lon": -79.1667}, 
        "Ibarra": {"lat": 0.3500, "lon": -78.1167}, 
        "Portoviejo": {"lat": -1.0500, "lon": -80.4500},
        "Santa Elena": {"lat": -2.2262, "lon": -80.8587},
        "Loja": {"lat": -4.0000, "lon": -79.2000},
        "Babahoyo": {"lat": -1.8022, "lon": -79.5344},
        "Latacunga": {"lat": -0.9316, "lon": -78.6158},
        "Milagro": {"lat": -2.1333, "lon": -79.5833},
        "Cayambe": {"lat": 0.0408, "lon": -78.1452},
        "Quevedo": {"lat": -1.0286, "lon": -79.4635},
        "Playas": {"lat": -2.6319, "lon": -80.3881},
        "Daule": {"lat": -1.8622, "lon": -79.9775},
        "El Coca": {"lat": -0.4667, "lon": -76.9833}
    }
}

# 2. RADAR OPERATIVO (TIEMPO REAL)
def obtener_clima_realtime(lat, lon):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=precipitation&hourly=precipitation,precipitation_probability&timezone=America%2FGuayaquil&forecast_days=2"
    try:
        resp = requests.get(url, timeout=5).json()
        lluvia_act = resp.get("current", {}).get("precipitation", 0.0)
        horas = resp["hourly"]["time"]
        lluvias = resp["hourly"]["precipitation"]
        probs = resp["hourly"]["precipitation_probability"]
        
        hora_actual = resp["current"]["time"][:13]
        idx = next((i for i, t in enumerate(horas) if t.startswith(hora_actual)), 0)
        
        return lluvia_act, [h[-5:] for h in horas[idx:idx+6]], lluvias[idx:idx+6], probs[idx:idx+6]
    except: 
        return None, [], [], []

def renderizar_tarjeta_tabla(nombre, lluvia, labels, lluvias_val, probs_val):
    if lluvia is None:
        st.error(f"{nombre} - Sin conexión")
        return
    estado, icono = ("🚨 Alerta Fuerte", "🚨") if lluvia >= 7.5 else ("🌧️ Precaución Moderada", "🌧️") if lluvia >= 2.0 else ("💧 Garúa", "💧") if lluvia > 0 else ("☀️ Operación Normal", "☀️")
    
    with st.container(border=True):
        st.markdown(f"<p style='margin:0; font-weight:bold; color:#333; font-size:1.1rem;'>{nombre}</p>", unsafe_allow_html=True)
        st.metric(label=estado, value=f"{lluvia} mm/h")
        if labels:
            df_mostrar = pd.DataFrame({
                "Hora": labels,
                "Lluvia (mm/h)": lluvias_val,
                "Prob. (%)": probs_val
            })
            st.markdown("<p style='font-size:0.8rem; color:#666; margin-bottom:5px;'>Pronóstico a 6 horas</p>", unsafe_allow_html=True)
            st.dataframe(df_mostrar, use_container_width=True, hide_index=True)

@st.fragment(run_every="5m") 
def tablero_realtime():
    hora_ec = datetime.now(pytz.timezone('America/Guayaquil')).strftime('%Y-%m-%d %H:%M:%S')
    st.caption(f"Última actualización: **{hora_ec}** | Refresco automático cada 5 min")
    
    # Selector de todas las regiones
    ciudad_sel = st.radio("Selecciona la región operativa:", list(COBERTURA_PEYA.keys()), horizontal=True)
    st.divider()
    
    zonas = COBERTURA_PEYA[ciudad_sel]
    cols = st.columns(2)
    
    for i, (nombre, coords) in enumerate(zonas.items()):
        lluvia, labels, lluvias_val, probs_val = obtener_clima_realtime(coords["lat"], coords["lon"])
        with cols[i % 2]: 
            renderizar_tarjeta_tabla(nombre, lluvia, labels, lluvias_val, probs_val)

# 3. DATA Y FORECAST BI (EXCEL)
def clasificar_ocasion(hora):
    if 0 <= hora < 7: return "1.Madrugada"
    elif 7 <= hora < 10: return "2.Mañana"
    elif 10 <= hora < 12: return "3.Media mañana"
    elif 12 <= hora < 15: return "4.Lunch Peak"
    elif 15 <= hora < 18: return "5.Tarde"
    elif 18 <= hora < 21: return "6.Dinner Peak"
    elif 21 <= hora < 23: return "7.Post Peak - Noche"
    else: return "8.Noche"

@st.cache_data(show_spinner=False, ttl="1h")
def generar_dataset_nacional():
    registros = []
    for region, locaciones in COBERTURA_PEYA.items():
        for zona, coords in locaciones.items():
            ciudad = region if region in ["Quito", "Guayaquil"] else zona
            zona_nom = zona if region in ["Quito", "Guayaquil"] else ciudad
            
            url = f"https://api.open-meteo.com/v1/forecast?latitude={coords['lat']}&longitude={coords['lon']}&hourly=precipitation,precipitation_probability&timezone=America%2FGuayaquil&past_days=14&forecast_days=7"
            try:
                resp = requests.get(url, timeout=10).json()
                tiempos = resp["hourly"]["time"]
                lluvias = resp["hourly"]["precipitation"]
                probs = resp["hourly"].get("precipitation_probability", [])
                
                for i in range(len(tiempos)):
                    dt = datetime.strptime(tiempos[i], "%Y-%m-%dT%H:%M")
                    # Protección contra nulos en días históricos
                    precip = lluvias[i] if lluvias[i] is not None else 0.0
                    prob = probs[i] if (i < len(probs) and probs[i] is not None) else 0
                    
                    registros.append({
                        "fecha": dt.strftime("%Y-%m-%d"), 
                        "city_name": ciudad, 
                        "zone_name": zona_nom, 
                        "hora_int": dt.hour, 
                        "lluvia_mm": precip,
                        "probabilidad_lluvia_%": prob
                    })
            except: 
                continue

    df = pd.DataFrame(registros)
    if not df.empty:
        df["ocasion"] = df["hora_int"].apply(clasificar_ocasion)
        # Agrupación segura
        df_agr = df.groupby(["fecha", "city_name", "zone_name", "ocasion"]).agg({
            "lluvia_mm": "sum",
            "probabilidad_lluvia_%": "max"
        }).reset_index()
        
        df_agr["lluvia_mm"] = df_agr["lluvia_mm"].round(2)
        df_agr = df_agr.rename(columns={"lluvia_mm": "lluvia_acumulada_mm"}).sort_values(by=["fecha", "city_name", "ocasion"])
        return df_agr
    return pd.DataFrame()

# 4. RENDERIZADO PRINCIPAL
st.title("Weather Ops & Data - PedidosYa Ecuador")

tab1, tab2 = st.tabs(["🔴 Radar Operativo (Tiempo Real)", "📊 Data Histórica & Forecast (Excel)"])

with tab1:
    tablero_realtime()

with tab2:
    st.markdown("### Matriz Nacional: 14 Días Histórico + 7 Días Forecast")
    if st.button("Generar y Descargar Reporte"):
        with st.spinner("Procesando histórico y calculando probabilidad forecast (tomará ~15 seg)..."):
            df_final = generar_dataset_nacional()
            if not df_final.empty:
                st.success(f"¡Data lista! {len(df_final)} filas procesadas.")
                st.dataframe(df_final, use_container_width=True, hide_index=True)
                
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    df_final.to_excel(writer, index=False, sheet_name='Weather_PeYa')
                
                st.download_button(
                    label="📥 Descargar Archivo Excel (.xlsx)",
                    data=buffer.getvalue(),
                    file_name=f"PeYa_Weather_Data_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary"
                )
            else:
                st.error("Error descargando la data. Intenta de nuevo.")
