import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
import pytz
import io

# 1. CONFIGURACIÓN Y ESTILOS
st.set_page_config(page_title="Weather LOps - Peya Ecuador", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    .stApp { background-color: #F7F7F7; }
    /* Solo el título principal h1 será rojo Peya */
    h1 { color: #EA044E !important; font-family: 'Arial', sans-serif; }
    /* Los subtítulos h2, h3, h4 serán gris oscuro */
    h2, h3, h4 { color: #333333 !important; font-family: 'Arial', sans-serif; }
    /* Los números de las métricas (mm/h) ahora son oscuros, NO rojos */
    div[data-testid="stMetricValue"] { color: #333333 !important; font-weight: bold; }
    
    .resumen-caja { background-color: #FFFFFF; padding: 10px; border-radius: 8px; border: 1px solid #E0E0E0; text-align: center; margin-bottom: 10px;}
    .resumen-titulo { font-size: 0.8rem; color: #666; margin-bottom: 5px; font-weight: bold;}
    .resumen-dato { font-size: 1rem; color: #333; font-weight: bold; }
    .smart-text-box { padding: 12px; border-radius: 8px; color: #333; font-size: 0.95rem; margin-bottom: 15px; line-height: 1.4; }
    .smart-green { background-color: #E8F5E9; border-left: 5px solid #4CAF50; }
    .smart-yellow { background-color: #FFFDE7; border-left: 5px solid #FBC02D; }
    .smart-red { background-color: #FCE4EC; border-left: 5px solid #EA044E; }
    .mini-banner { font-size: 0.85rem; padding: 5px 8px; border-radius: 4px; margin-bottom: 10px; font-weight: 500; }
</style>
""", unsafe_allow_html=True)

# 2. DICCIONARIO GEOGRÁFICO
COBERTURA_PEYA = {
    "Quito": { 
        "Norte": {"lat": -0.045, "lon": -78.46}, 
        "Carapungo": {"lat": -0.095, "lon": -78.44}, 
        "Centro": {"lat": -0.18, "lon": -78.48}, 
        "Sur": {"lat": -0.28, "lon": -78.54}, 
        "Cumbaya Tumbaco": {"lat": -0.21, "lon": -78.40}, 
        "Valle Chillos": {"lat": -0.29, "lon": -78.45} 
    },
    "Guayaquil": { 
        "Centro Norte": {"lat": -2.145, "lon": -79.90}, 
        "Oeste": {"lat": -2.185, "lon": -79.95}, 
        "Samborondon Aurora": {"lat": -2.115, "lon": -79.87}, 
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
CENTROS_MACRO = {"Quito": {"lat": -0.18, "lon": -78.48}, "Guayaquil": {"lat": -2.145, "lon": -79.90}}

tz_ec = pytz.timezone('America/Guayaquil')
hoy_dt = datetime.now(tz_ec)
DIAS_MAP = {
    0: "Hoy",
    1: "Mañana",
    2: (hoy_dt + timedelta(days=2)).strftime("%d/%m"),
    3: (hoy_dt + timedelta(days=3)).strftime("%d/%m")
}

# 3. EXTRACCIÓN CON MEMORIA CACHÉ
@st.cache_data(ttl=300, show_spinner=False)
def fetch_weather_api(lat, lon):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=precipitation&hourly=precipitation,precipitation_probability&timezone=America%2FGuayaquil&forecast_days=4"
    return requests.get(url, timeout=5).json()

def obtener_clima_completo(lat, lon, offset_dias):
    try:
        resp = fetch_weather_api(lat, lon)
        lluvia_act = resp.get("current", {}).get("precipitation", 0.0) if offset_dias == 0 else None
        
        horas = resp["hourly"]["time"]
        lluvias = [x if x is not None else 0.0 for x in resp["hourly"]["precipitation"]]
        probs = [x if x is not None else 0 for x in resp["hourly"]["precipitation_probability"]]
        
        fecha_objetivo = (hoy_dt + timedelta(days=offset_dias)).strftime("%Y-%m-%d")
        hora_actual_str = hoy_dt.strftime("%Y-%m-%dT%H")
        
        tabla_data = []
        manana_mm, manana_prob = 0.0, 0
        tarde_mm, tarde_prob = 0.0, 0
        noche_mm, noche_prob = 0.0, 0
        
        for t, rain, prob in zip(horas, lluvias, probs):
            if t.startswith(fecha_objetivo):
                h = int(t[11:13])
                
                if 6 <= h < 12:
                    manana_mm += rain
                    manana_prob = max(manana_prob, prob)
                elif 12 <= h < 18:
                    tarde_mm += rain
                    tarde_prob = max(tarde_prob, prob)
                elif 18 <= h < 24:
                    noche_mm += rain
                    noche_prob = max(noche_prob, prob)
                
                if offset_dias == 0 and t < hora_actual_str:
                    continue
                
                hora_label = f"{h:02d}:00"
                if 12 <= h <= 14: hora_label += " 🍔"
                elif 19 <= h <= 21: hora_label += " 🍕"
                
                tabla_data.append({"Hora": hora_label, "Lluvia (mm)": round(rain, 2), "Prob. (%)": prob})
                
        resumen_dia = {
            "Mañana": (round(manana_mm, 2), manana_prob),
            "Tarde": (round(tarde_mm, 2), tarde_prob),
            "Noche": (round(noche_mm, 2), noche_prob)
        }
        return lluvia_act, tabla_data, resumen_dia
    except Exception: 
        return None, [], {}

def generar_smart_text(resumen, zonas_riesgo=None):
    m, t, n = resumen["Mañana"][0], resumen["Tarde"][0], resumen["Noche"][0]
    total = m + t + n
    texto_zonas = f"<br>📍 <b>Atención en:</b> {', '.join(zonas_riesgo)}." if zonas_riesgo else ""

    if total == 0: 
        return "✅ <b>Día Despejado:</b> Jornada sin probabilidad de lluvia en esta locación.", "smart-green"
    if m >= 3.0 and t >= 3.0 and n >= 3.0: 
        return f"🚨 <b>Alerta General:</b> Se registran lluvias fuertes y sostenidas durante casi todo el día.{texto_zonas}", "smart-red"
    if t == max(m, t, n) and t >= 2.0: 
        return f"⚠️ <b>Alerta Lunch / Tarde:</b> Se pronostican lluvias fuertes ({t:.2f}mm) en el turno de la tarde.{texto_zonas}", "smart-red"
    if n == max(m, t, n) and n >= 2.0: 
        return f"⚠️ <b>Alerta Dinner / Noche:</b> Condiciones estables de día, pero lloverá fuerte en la noche ({n:.2f}mm).{texto_zonas}", "smart-red"
    if m == max(m, t, n) and m >= 2.0: 
        return f"🌧️ <b>Precaución Matutina:</b> Lluvia moderada en la mañana ({m:.2f}mm). Mejoran las condiciones para los picos de demanda.{texto_zonas}", "smart-yellow"
    
    return f"🌤️ <b>Condiciones Manejables:</b> Jornada mayormente seca con posibles garúas aisladas.{texto_zonas}", "smart-yellow"

def generar_mini_banner(resumen):
    m, t, n = resumen["Mañana"][0], resumen["Tarde"][0], resumen["Noche"][0]
    if m+t+n == 0: return "<div class='mini-banner smart-green'>✅ Sin lluvia prevista</div>"
    pico_mm = max(m, t, n)
    turno = "Mañana" if pico_mm == m else "Tarde" if pico_mm == t else "Noche"
    clase = "smart-red" if pico_mm >= 2.0 else "smart-yellow"
    icono = "⚠️" if pico_mm >= 2.0 else "💧"
    return f"<div class='mini-banner {clase}'>{icono} Riesgo en {turno} ({pico_mm:.2f}mm)</div>"

# Estilos Pandas
def color_lluvia(val):
    if val >= 5.0: return 'background-color: #ffcdd2; color: #b71c1c'
    elif val >= 1.5: return 'background-color: #ffe0b2; color: #e65100'
    elif val > 0: return 'background-color: #f1f8e9; color: #336600'
    return ''

# 4. COMPONENTES VISUALES
def renderizar_tarjeta_zona(nombre, lluvia_act, tabla_data, resumen, mostrar_smart):
    with st.container(border=True):
        st.markdown(f"<p style='margin:0; font-weight:bold; color:#333; font-size:1.2rem;'>{nombre}</p>", unsafe_allow_html=True)
        
        if lluvia_act is not None:
            estado = "🚨 Alerta Fuerte" if lluvia_act >= 7.5 else "🌧️ Lluvia Moderada" if lluvia_act >= 2.0 else "💧 Garúa" if lluvia_act > 0 else "☀️ Normal"
            st.metric(label=estado, value=f"{lluvia_act:.2f} mm/h")
        if resumen:
            st.markdown(generar_mini_banner(resumen), unsafe_allow_html=True)
            if mostrar_smart:
                txt, color = generar_smart_text(resumen)
                st.markdown(f"<div class='smart-text-box {color}' style='padding:8px; font-size:0.8rem;'>{txt}</div>", unsafe_allow_html=True)

        if tabla_data:
            df = pd.DataFrame(tabla_data)
            styled_df = df.style.map(color_lluvia, subset=['Lluvia (mm)']).format({
                "Lluvia (mm)": "{:.2f}",
                "Prob. (%)": "{:.0f}%"
            })
            st.dataframe(styled_df, use_container_width=True, hide_index=True, height=210)

@st.fragment(run_every="5m") 
def tablero_realtime():
    st.caption(f"Última actualización: **{hoy_dt.strftime('%H:%M:%S')}** | Refresco 5 min")
    
    col_sel1, col_sel2 = st.columns([1, 1])
    with col_sel1:
        ciudad_sel = st.radio("📍 Locación:", list(COBERTURA_PEYA.keys()), horizontal=True, label_visibility="collapsed")
    with col_sel2:
        dia_nombre = st.radio("🗓️ Horizonte:", list(DIAS_MAP.values()), horizontal=True, label_visibility="collapsed")
    
    offset_dias = list(DIAS_MAP.keys())[list(DIAS_MAP.values()).index(dia_nombre)]
    st.divider()
    
    zonas = COBERTURA_PEYA[ciudad_sel]
    datos_zonas, zonas_riesgo = {}, []
    
    for nombre, coords in zonas.items():
        lluvia_act, tabla_data, resumen = obtener_clima_completo(coords["lat"], coords["lon"], offset_dias)
        datos_zonas[nombre] = (lluvia_act, tabla_data, resumen)
        if resumen and (resumen["Mañana"][0] + resumen["Tarde"][0] + resumen["Noche"][0]) >= 1.5:  
            zonas_riesgo.append(nombre)
    
    if ciudad_sel in ["Quito", "Guayaquil"]:
        _, _, resumen_macro = obtener_clima_completo(CENTROS_MACRO[ciudad_sel]["lat"], CENTROS_MACRO[ciudad_sel]["lon"], offset_dias)
        if resumen_macro:
            st.markdown(f"### 📍 Panorama General: {ciudad_sel} ({dia_nombre})")
            c1, c2, c3 = st.columns(3)
            c1.markdown(f"<div class='resumen-caja'>🌅 Mañana<br><span class='resumen-dato'>{resumen_macro['Mañana'][0]:.2f}mm | {resumen_macro['Mañana'][1]}%</span></div>", unsafe_allow_html=True)
            c2.markdown(f"<div class='resumen-caja'>🌇 Tarde<br><span class='resumen-dato'>{resumen_macro['Tarde'][0]:.2f}mm | {resumen_macro['Tarde'][1]}%</span></div>", unsafe_allow_html=True)
            c3.markdown(f"<div class='resumen-caja'>🌙 Noche<br><span class='resumen-dato'>{resumen_macro['Noche'][0]:.2f}mm | {resumen_macro['Noche'][1]}%</span></div>", unsafe_allow_html=True)
            txt, col = generar_smart_text(resumen_macro, zonas_riesgo)
            st.markdown(f"<div class='smart-text-box {col}'>{txt}</div>", unsafe_allow_html=True)
            st.divider()
    
    cols = st.columns(2)
    for i, (nombre, data) in enumerate(datos_zonas.items()):
        lluvia_act, tabla_data, resumen = data
        with cols[i % 2]: 
            renderizar_tarjeta_zona(nombre, lluvia_act, tabla_data, resumen, ciudad_sel=="Potential Cities")

# 5. MENÚ LATERAL Y EXCEL (Histórico)
def clasificar_ocasion(hora):
    if 0 <= hora < 7: return "1.Madrugada"
    elif 7 <= hora < 10: return "2.Mañana"
    elif 10 <= hora < 12: return "3.Media mañana"
    elif 12 <= hora < 15: return "4.Lunch Peak"
    elif 15 <= hora < 18: return "5.Tarde"
    elif 18 <= hora < 21: return "6.Dinner Peak"
    else: return "7.Post Peak - Noche"

@st.cache_data(show_spinner=False, ttl="1h")
def generar_dataset_nacional():
    registros = []
    for region, locaciones in COBERTURA_PEYA.items():
        for zona, coords in locaciones.items():
            ciudad, zona_nom = (region, zona) if region in ["Quito", "Guayaquil"] else (zona, region)
            try:
                url = f"https://api.open-meteo.com/v1/forecast?latitude={coords['lat']}&longitude={coords['lon']}&hourly=precipitation,precipitation_probability&timezone=America%2FGuayaquil&past_days=14&forecast_days=7"
                resp = requests.get(url, timeout=10).json()
                for i, t in enumerate(resp["hourly"]["time"]):
                    dt = datetime.strptime(t, "%Y-%m-%dT%H:%M")
                    rain = resp["hourly"]["precipitation"][i] or 0.0
                    prob = resp["hourly"].get("precipitation_probability", [])
                    p = prob[i] if i < len(prob) and prob[i] else 0
                    registros.append({"fecha": dt.strftime("%Y-%m-%d"), "city_name": ciudad, "zone_name": zona_nom, "hora_int": dt.hour, "lluvia_mm": rain, "probabilidad_%": p})
            except: continue
    
    df = pd.DataFrame(registros)
    if not df.empty:
        df["ocasion"] = df["hora_int"].apply(clasificar_ocasion)
        df_agr = df.groupby(["fecha", "city_name", "zone_name", "ocasion"]).agg({"lluvia_mm": "sum", "probabilidad_%": "max"}).reset_index()
        df_agr["lluvia_mm"] = df_agr["lluvia_mm"].round(2)
        return df_agr.sort_values(by=["fecha", "city_name", "ocasion"])
    return pd.DataFrame()

st.sidebar.title("☁️ LOps Tools")
seccion = st.sidebar.radio("Navegación:", ["Radar Táctico (4 Días)", "Centro de Datos (Excel)"])
st.title("Weather LOps - Peya Ecuador")

if seccion == "Radar Táctico (4 Días)":
    tablero_realtime()
else:
    st.markdown("### 📊 Data Completa por Ciudad y Zona: 14 Días Histórico y 7 Días Forecast")
    st.markdown("Genera la matriz de datos base para modelar incentivos logísticos y analizar performance.")
    if st.button("Procesar y Descargar Matriz"):
        with st.spinner("Procesando millones de puntos de data..."):
            df_final = generar_dataset_nacional()
            if not df_final.empty:
                st.success("Data lista.")
                st.dataframe(df_final, use_container_width=True, hide_index=True)
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as w: df_final.to_excel(w, index=False)
                st.download_button("📥 Descargar Excel", buffer.getvalue(), f"PeYa_Weather_{hoy_dt.strftime('%Y%m%d')}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", type="primary")
