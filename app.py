import streamlit as st
import requests

st.set_page_config(page_title="Test de Diagnóstico API")

st.title("🧪 Test de Conexión: Open-Meteo vs Streamlit")
st.markdown("Esta herramienta hace un 'ping' directo a la API para ver si la IP de Streamlit está bloqueada.")

url = "https://api.open-meteo.com/v1/forecast?latitude=-0.18&longitude=-78.48&current=precipitation&timezone=America%2FGuayaquil"

if st.button("Ejecutar Test de Red"):
    with st.spinner("Consultando a Open-Meteo..."):
        try:
            resp = requests.get(url, timeout=10)
            
            # Mostrar el código de estado HTTP
            if resp.status_code == 200:
                st.success(f"✅ Conexión Exitosa (Status Code: {resp.status_code})")
            elif resp.status_code == 429:
                st.warning(f"⚠️ Bloqueo por Saturación (Status Code: {resp.status_code}) - 'Too Many Requests'")
            elif resp.status_code == 403:
                st.error(f"🚨 Bloqueo Permanente de IP (Status Code: {resp.status_code}) - 'Forbidden'")
            else:
                st.error(f"❌ Error Desconocido (Status Code: {resp.status_code})")
                
            # Mostrar la respuesta cruda del servidor
            st.markdown("### Respuesta Cruda del Servidor:")
            try:
                st.json(resp.json())
            except:
                st.write(resp.text)
                
        except Exception as e:
            st.error(f"Fallo crítico de red: {e}")
