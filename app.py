import streamlit as st
import google.generativeai as genai
from PIL import Image
import io
import time

# ==========================================
# 1. CONFIGURACIÓN DE ACCESO
# ==========================================
# RECOMENDACIÓN: Genera una llave nueva, la anterior ya expiró por seguridad.
API_KEY = "AIzaSyClGFm_2nBWYGPJQ9YD1_249NHmnKAVUbA" 

def skill_vision_well_plan(imagen_pil, instruccion):
    try:
        # Configuración con transporte REST para estabilidad en campo
        genai.configure(api_key=API_KEY.strip(), transport='rest')
        
        # Selección del modelo (Ruta estable)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Compresión de imagen (Optimizado para ancho de banda limitado)
        buf = io.BytesIO()
        imagen_pil.save(buf, format='JPEG', quality=40)
        img_bytes = buf.getvalue()
        
        prompt_tecnico = f"""
        Actúa como experto en Well Planning de Ecopetrol.
        Tarea: Extraer {instruccion} del Estado Mecánico adjunto.
        Formato: Respuesta técnica, corta y directa.
        """
        
        # Ejecución del análisis
        response = model.generate_content(
            contents=[{
                "parts": [
                    {"inline_data": {"mime_type": "image/jpeg", "data": img_bytes}},
                    {"text": prompt_tecnico}
                ]
            }]
        )
        
        return response.text if response.text else "No se detectaron datos en el recorte."

    except Exception as e:
        error_msg = str(e)
        if "404" in error_msg:
            return "❌ ERROR 404: El servidor aún usa una versión vieja. Verifica el archivo requirements.txt."
        if "400" in error_msg:
            return "❌ ERROR 400: API Key inválida. Por favor usa una llave nueva de AI Studio."
        return f"⚠️ Error Técnico: {error_msg}"

# ==========================================
# 2. INTERFAZ DE USUARIO (STREAMLIT)
# ==========================================
st.set_page_config(page_title="Well Planning - Operaciones", page_icon="🏗️", layout="wide")

if 'menu' not in st.session_state:
    st.session_state.menu = "Home"

# Sidebar de navegación
with st.sidebar:
    st.markdown("<h1 style='text-align: center; color: #2E7D32;'>ECOPETROL 🦎</h1>", unsafe_allow_html=True)
    st.divider()
    if st.button("🏠 Inicio", use_container_width=True):
        st.session_state.menu = "Home"
        st.rerun()

# --- Lógica de Pantallas ---

if st.session_state.menu == "Home":
    st.title("🚧 Construcción Well Plan - Operaciones CUA")
    st.subheader("Seleccione el módulo para iniciar:")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🌑 1. Abandonos", use_container_width=True):
            st.session_state.menu = "Abandonos"
            st.rerun()
        if st.button("⚙️ 2. Mantenimiento BES", use_container_width=True):
            st.session_state.menu = "BES"
            st.rerun()
    with col2:
        if st.button("📊 3. Rediseño SLA", use_container_width=True):
            st.session_state.menu = "SLA"
            st.rerun()
        if st.button("🛠️ 4. Workover", use_container_width=True):
            st.session_state.menu = "Workover"
            st.rerun()

elif st.session_state.menu == "BES":
    st.title("⚙️ Módulo de Extracción BES")
    
    tabs = st.tabs(["🏗️ Cabezal", "🕳️ Liner", "🔌 Sarta"])
    
    with tabs[0]:
        seccion = "Cabezal (Sección B)"
        instr = "Tipo de Tubing Head y Presión Nominal (PSI)"
        
        archivo = st.file_uploader("Sube recorte del Cabezal", type=["jpg", "png", "jpeg"], key="u1")
        if archivo:
            img = Image.open(archivo)
            st.image(img, width=400)
            if st.button("🔍 Escanear Cabezal", key="b1"):
                with st.status("Analizando datos técnicos...") as s:
                    res = skill_vision_well_plan(img, instr)
                    s.update(label="Análisis finalizado", state="complete")
                st.info(f"**Resultado:** {res}")

    with tabs[1]:
        st.write("Módulo de Liner listo para carga de imagen.")
        # Aquí puedes repetir la lógica del uploader para Liner

    with tabs[2]:
        st.write("Módulo de Sarta listo para carga de imagen.")

else:
    st.title(f"Módulo {st.session_state.menu}")
    st.warning("Esta sección se encuentra en desarrollo.")
