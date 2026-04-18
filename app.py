import streamlit as st
import google.generativeai as genai
from PIL import Image
import io

# ==========================================
# 1. CONFIGURACIÓN DE ACCESO (ACTUALIZADA)
# ==========================================
API_KEY = "AIzaSyAeGSLMzgyWohox06qXtJR7fFbUyMjeZA0"

def skill_vision_well_plan(imagen_pil, instruccion):
    try:
        # Configuración limpia
        genai.configure(api_key=API_KEY.strip())
        
        # Selección del modelo estable
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Optimización de imagen para red de campo (Calidad 50%)
        buf = io.BytesIO()
        imagen_pil.save(buf, format='JPEG', quality=50)
        img_bytes = buf.getvalue()
        
        # Prompt técnico para ingeniería
        prompt_final = f"Como experto en ingeniería de petróleos, extrae del Estado Mecánico: {instruccion}. Responde solo con datos técnicos."
        
        # Envío simplificado (Formato compatible con >= 0.8.0)
        response = model.generate_content([
            prompt_final,
            {"mime_type": "image/jpeg", "data": img_bytes}
        ])
        
        if response.text:
            return response.text
        else:
            return "⚠️ No se detectaron datos legibles en el recorte."

    except Exception as e:
        error_msg = str(e)
        if "404" in error_msg:
            return "❌ ERROR 404: El servidor aún no reconoce el modelo. Por favor, reinicia la App en Streamlit Cloud (Reboot) para que instale las librerías del requirements.txt."
        if "400" in error_msg:
            return "❌ ERROR 400: La API Key no es válida. Verifica que no falten caracteres."
        return f"⚠️ Error Técnico: {error_msg}"

# ==========================================
# 2. INTERFAZ DE USUARIO (STREAMLIT)
# ==========================================
st.set_page_config(page_title="Well Planning - Operaciones CUA", page_icon="🏗️", layout="wide")

# Gestión de navegación
if 'menu' not in st.session_state:
    st.session_state.menu = "Home"

# Sidebar
with st.sidebar:
    st.markdown("<h1 style='text-align: center; color: #2E7D32;'>ECOPETROL 🦎</h1>", unsafe_allow_html=True)
    st.divider()
    if st.button("🏠 Inicio", use_container_width=True):
        st.session_state.menu = "Home"
        st.rerun()

# --- Pantalla Principal ---
if st.session_state.menu == "Home":
    st.title("🚧 Construcción Well Plan - Operaciones CUA")
    st.info("Plataforma de extracción automática de datos de subsuelo.")
    
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

# --- Módulo BES ---
elif st.session_state.menu == "BES":
    st.title("⚙️ Módulo de Extracción BES")
    
    tab1, tab2, tab3 = st.tabs(["🏗️ Cabezal", "🕳️ Liner", "🔌 Sarta"])
    
    with tab1:
        st.subheader("Análisis de Cabezal (Sección B)")
        archivo = st.file_uploader("Cargar recorte de Cabezal", type=["jpg", "png", "jpeg"], key="u_head")
        if archivo:
            img = Image.open(archivo)
            st.image(img, width=400, caption="Recorte seleccionado")
            if st.button("🔍 Escanear Cabezal"):
                with st.status("Procesando con Gemini 1.5 Flash...") as s:
                    resultado = skill_vision_well_plan(img, "Tipo de Cabezal, Serie y Presión Nominal")
                    s.update(label="Análisis finalizado", state="complete")
                st.success(f"**Datos Extraídos:**\n{resultado}")

    with tab2:
        st.subheader("Análisis de Revestimiento")
        archivo2 = st.file_uploader("Cargar recorte de Liner/Casing", type=["jpg", "png", "jpeg"], key="u_liner")
        if archivo2:
            img2 = Image.open(archivo2)
            st.image(img2, width=400)
            if st.button("🔍 Escanear Liner"):
                with st.spinner("Analizando..."):
                    resultado = skill_vision_well_plan(img2, "Diámetro (OD), Peso y Grado del Casing")
                    st.info(f"**Datos Extraídos:**\n{resultado}")

    with tab3:
        st.subheader("Análisis de Sarta y Bomba")
        archivo3 = st.file_uploader("Cargar recorte de Sarta", type=["jpg", "png", "jpeg"], key="u_sarta")
        if archivo3:
            img3 = Image.open(archivo3)
            st.image(img3, width=400)
            if st.button("🔍 Escanear Sarta"):
                with st.spinner("Analizando..."):
                    resultado = skill_vision_well_plan(img3, "Profundidad de la bomba BES y OD del Tubing")
                    st.info(f"**Datos Extraídos:**\n{resultado}")

else:
    st.title(f"Módulo {st.session_state.menu}")
    st.warning("Esta sección se encuentra en desarrollo técnico.")
