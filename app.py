import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import pytz
import io

# 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS
st.set_page_config(page_title="Weather LOps - Peya Ecuador", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    .stApp { background-color: #F7F7F7; }
    h1, h2, h3 { color: #EA044E !important; font-family: 'Arial', sans-serif; }
    div[data-testid="stMetricValue"] { color: #EA044E !important; font-weight: bold; }
    div[data-testid="stDataFrame"] { width: 100% !important; }
    .resumen-caja { background-color: #FFFFFF; padding: 10px; border-radius: 8px; border: 1px solid #E0E0E0; text-align: center; margin-bottom: 15px;}
    .resumen-titulo { font-size: 0.85rem; color: #666; margin-bottom: 5px; font-weight: bold;}
    .resumen-dato { font-size: 1.1rem; color: #333; font-weight: bold; }
    .smart-text-box { padding: 15px; border-radius: 8px; color: #333; font-size: 0.95rem; margin-bottom: 20px; }
    .smart-green { background-color: #E8F5E9; border-left: 5px solid #4CAF50; }
    .smart-yellow { background-color: #FFFDE7; border-left: 5px solid #FBC02D; }
    .smart-red { background-color: #FCE4EC; border-left: 5px solid #EA044E; }
</style>
""", unsafe_allow_html=True)

# 2. DICCIONARIO GEOGRÁFICO UNIFICADO
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

CENTROS_MACRO = {
    "Quito": {"lat": -0.18, "lon": -78.48},
    "Guayaquil": {"lat": -2.145, "lon": -79.90}
}

# 3. LÓGICA DE EXTRACCIÓN Y SEMÁFORO SMART TEXT
def obtener_clima_completo(lat, lon):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=precipitation&hourly=precipitation,precipitation_probability&timezone=America%2FGuayaquil&forecast_days=2"
    try:
        resp = requests.get(url, timeout=5).json()
        lluvia_act = resp.get("current", {}).get("precipitation", 0.0)
        horas = resp["hourly"]["time"]
        lluvias = [x if x is not None else 0.0 for x in resp["hourly"]["precipitation"]]
        probs = [x if x is not None else 0 for x in resp["hourly"]["precipitation_probability"]]
        
        hora_actual_str = resp["current"]["time"][:13]
        idx_actual = next((i for i, t in enumerate(horas) if t.startswith(hora_actual_str)), 0)
        
        labels_6h = [h[-5:] for h in horas[idx_actual:idx_actual+6]]
        lluvias_6h = lluvias[idx_actual:idx_actual+6]
        probs_6h = probs[idx_actual:idx_actual+6]
        
        hoy_str = datetime.now(pytz.timezone('America/Guayaquil')).strftime("%Y-%m-%d")
        manana_mm, manana_prob = 0.0, 0
        tarde_mm, tarde_prob = 0.0, 0
        noche_mm, noche_prob = 0.0, 0
        
        for t, rain, prob in zip(horas, lluvias, probs):
            if t.startswith(hoy_str):
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
                    
        resumen_dia = {
            "Mañana": (round(manana_mm, 1), manana_prob),
            "Tarde": (round(tarde_mm, 1), tarde_prob),
            "Noche": (round(noche_mm, 1), noche_prob)
        }
        return lluvia_act, labels_6h, lluvias_6h, probs_6h, resumen_dia
    except Exception: 
        return None, [], [], [], {}

def generar_smart_text(resumen, zonas_riesgo=None):
    m = resumen["Mañana"][0]
    t = resumen["Tarde"][0]
    n = resumen["Noche"][0]
    total = m + t + n

    texto_zonas = ""
    if zonas_riesgo and len(zonas_riesgo) > 0:
        nombres = ", ".join(zonas_riesgo)
        texto_zonas = f" 📍 **Prestar mayor atención operativa en:** {nombres}."

    if total == 0:
        return "✅ **Día Despejado:** Jornada sin probabilidad de lluvia. No se prevén impactos climáticos en la operación y los tiempos de entrega.", "smart-green"
    
    if m >= 3.0 and t >= 3.0 and n >= 3.0:
        return f"🚨 **Alerta General:** Lluvias intensas durante casi todo el día. Se sugiere activar protocolos de contingencia de inmediato.{texto_zonas}", "smart-red"
    
    if t == max(m, t, n) and t >= 2.0:
        return f"⚠️ **Alerta en Lunch Peak / Tarde:** Se pronostican lluvias fuertes ({t}mm) que impactarán el turno de la tarde. Anticipar flota e incrementos en tiempos de entrega.{texto_zonas}", "smart-red"
    
    if n == max(m, t, n) and n >= 2.0:
        return f"⚠️ **Alerta en Dinner Peak / Noche:** Operación estable de día, pero lloverá fuerte en la noche ({n}mm). Reforzar la disponibilidad de repartidores en ese turno.{texto_zonas}", "smart-red"
    
    if m == max(m, t, n) and m >= 2.0:
        return f"🌧️ **Precaución Matutina:** Lluvia moderada en la mañana ({m}mm). Las condiciones mejorarán significativamente para los picos de mayor demanda.{texto_zonas}", "smart-yellow"
    
    return f"🌤️ **Condiciones Manejables:** Jornada mayormente seca. Solo se esperan garúas o chubascos breves que no deberían afectar la logística habitual.{texto_zonas}", "smart-yellow"

# 4. COMPONENTES VISUALES
def renderizar_banner_ciudad(nombre, resumen, zonas_riesgo):
    st.markdown(f"### 📍 Panorama General: {nombre}")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"<div class='resumen-caja'><div class='resumen-titulo'>🌅 Acumulado Mañana</div><div class='resumen-dato'>{resumen['Mañana'][0]}mm | Riesgo: {resumen['Mañana'][1]}%</div></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='resumen-caja'><div class='resumen-titulo'>🌇 Acumulado Tarde</div><div class='resumen-dato'>{resumen['Tarde'][0]}mm | Riesgo: {resumen['Tarde'][1]}%</div></div>", unsafe_allow_html=True)
    with c3:
        st.markdown(f"<div class='resumen-caja'><div class='resumen-titulo'>🌙 Acumulado Noche</div><div class='resumen-dato'>{resumen['Noche'][0]}mm | Riesgo: {resumen['Noche'][1]}%</div></div>", unsafe_allow_html=True)
    
    texto_inteligente, color_class = generar_smart_text(resumen, zonas_riesgo)
    st.markdown(f"<div class='smart-text-box {color_class}'>{texto_inteligente}</div>", unsafe_allow_html=True)
    st.divider()

def renderizar_tarjeta_zona(nombre, lluvia, labels, lluvias_val, probs_val, resumen=None, mostrar_smart_text=False):
    if lluvia is None:
        st.error(f"{nombre} - Sin conexión")
        return
    
    estado = "🚨 Alerta Fuerte" if lluvia >= 7.5 else "🌧️ Lluvia Moderada" if lluvia >= 2.0 else "💧 Garúa" if lluvia > 0 else "☀️ Normal"
    
    with st.container(border=True):
        st.markdown(f"<p style='margin:0; font-weight:bold; color:#333; font-size:1.2rem;'>{nombre}</p>", unsafe_allow_html=True)
        st.metric(label=estado, value=f"{lluvia} mm/h")
        
        if resumen:
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f"<div class='resumen-caja' style='padding:5px;'><div class='resumen-titulo'>🌅</div><div class='resumen-dato' style='font-size:0.9rem;'>{resumen['Mañana'][0]}mm</div></div>", unsafe_allow_html=True)
            with c2:
                st.markdown(f"<div class='resumen-caja' style='padding:5px;'><div class='resumen-titulo'>🌇</div><div class='resumen-dato' style='font-size:0.9rem;'>{resumen['Tarde'][0]}mm</div></div>", unsafe_allow_html=True)
            with c3:
                st.markdown(f"<div class='resumen-caja' style='padding:5px;'><div class='resumen-titulo'>🌙</div><div class='resumen-dato' style='font-size:0.9rem;'>{resumen['Noche'][0]}mm</div></div>", unsafe_allow_html=True)
            
            if mostrar_smart_text:
                texto_inteligente, color_class = generar_smart_text(resumen)
                st.markdown(f"<div class='smart-text-box {color_class}' style='padding:10px; font-size:0.85rem; margin-bottom:10px;'>{texto_inteligente}</div>", unsafe_allow_html=True)
        
        if labels:
            st.markdown("<p style='font-size:0.8rem; color:#666; margin: 15px 0 5px 0;'>Pronóstico a 6 horas</p>", unsafe_allow_html=True)
            df_mostrar = pd.DataFrame({"Hora": labels, "Lluvia (mm/h)": lluvias_val, "Prob. (%)": probs_val})
            st.dataframe(df_mostrar, use_container_width=True, hide_index=True)

@st.fragment(run_every="5m") 
def tablero_realtime():
    hora_ec = datetime.now(pytz.timezone('America/Guayaquil')).strftime('%Y-%m-%d %H:%M:%S')
    st.caption(f"Última actualización: **{hora_ec}** | Refresco automático cada 5 min")
    
    ciudad_sel = st.radio("📍 Selecciona la región operativa:", list(COBERTURA_PEYA.keys()), horizontal=True, label_visibility="collapsed")
    st.divider()
    
    zonas = COBERTURA_PEYA[ciudad_sel]
    
    # Pre-calcular data de zonas para saber cuáles tienen riesgo (umbral >= 1.5mm)
    datos_zonas = {}
    zonas_riesgo = []
    
    for nombre, coords in zonas.items():
        lluvia, labels, lluvias_val, probs_val, resumen = obtener_clima_completo(coords["lat"], coords["lon"])
        datos_zonas[nombre] = (lluvia, labels, lluvias_val, probs_val, resumen)
        if resumen:
            total_mm = resumen["Mañana"][0] + resumen["Tarde"][0] + resumen["Noche"][0]
            if total_mm >= 1.5:  
                zonas_riesgo.append(nombre)
    
    # 1. Banner Macro (Solo Quito y Guayaquil)
    if ciudad_sel in ["Quito", "Guayaquil"]:
        coords_macro = CENTROS_MACRO[ciudad_sel]
        _, _, _, _, resumen_macro = obtener_clima_completo(coords_macro["lat"], coords_macro["lon"])
        if resumen_macro:
            renderizar_banner_ciudad(ciudad_sel, resumen_macro, zonas_riesgo)
    
    # 2. Desglose Operativo
    st.markdown("#### 🎯 Radar Táctico por Locación")
    cols = st.columns(2)
    
    for i, (nombre, data) in enumerate(datos_zonas.items()):
        lluvia, labels, lluvias_val, probs_val, resumen = data
        mostrar_smart = True if ciudad_sel == "Potential Cities" else False
        with cols[i % 2]: 
            renderizar_tarjeta_zona(nombre, lluvia, labels, lluvias_val, probs_val, resumen, mostrar_smart)

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
        df_agr = df.groupby(["fecha", "city_name", "zone_name", "ocasion"]).agg({
            "lluvia_mm": "sum",
            "probabilidad_lluvia_%": "max"
        }).reset_index()
        
        df_agr["lluvia_mm"] = df_agr["lluvia_mm"].round(2)
        df_agr = df_agr.rename(columns={"lluvia_mm": "lluvia_acumulada_mm"}).sort_values(by=["fecha", "city_name", "ocasion"])
        return df_agr
    return pd.DataFrame()

# 5. MENÚ LATERAL Y NAVEGACIÓN
st.sidebar.title("☁️ LOps Tools")
st.sidebar.markdown("---")
seccion = st.sidebar.radio("Navegación:", ["Radar Operativo (En vivo)", "Data Histórica (Excel)"])

st.title("Weather LOps & Data - Peya Ecuador")

if seccion == "Radar Operativo (En vivo)":
    tablero_realtime()

elif seccion == "Data Histórica (Excel)":
    st.markdown("### 📊 Extracción de Datos Base")
    st.markdown("Genera la matriz nacional consolidada (14 días de histórico real + 7 días de pronóstico).")
    
    if st.button("Procesar y Descargar Reporte"):
        with st.spinner("Conectando con estaciones meteorológicas... (tomará ~15 seg)"):
            df_final = generar_dataset_nacional()
            if not df_final.empty:
                st.success(f"¡Data lista! {len(df_final)} filas procesadas.")
                st.dataframe(df_final, use_container_width=True, hide_index=True)
                
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    df_final.to_excel(writer, index=False, sheet_name='Weather_PeYa')
                
                st.download_button(
                    label="📥 Descargar Excel (.xlsx)",
                    data=buffer.getvalue(),
                    file_name=f"PeYa_Weather_Data_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary"
                )
            else:
                st.error("Error descargando la data. Intenta de nuevo.")
