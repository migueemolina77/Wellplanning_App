import streamlit as st
import google.generativeai as genai
from PIL import Image
import io
import time

import streamlit as st
import google.generativeai as genai
from PIL import Image
import io
import time

# ==========================================
# 1. CONFIGURACIÓN DE SEGURIDAD
# ==========================================
# Asegúrate de mantener las COMILLAS
API_KEY = "AIzaSyCOefR18ZH-muHc8dlvHHOqmkuCvfkHxDE" 

def skill_vision_well_plan(imagen_pil, instruccion_especifica):
    try:
        # Forzamos la configuración con transporte REST
        genai.configure(api_key=API_KEY, transport='rest')
        
        # CAMBIO CLAVE: Probamos con el nombre técnico completo para evitar el 404
        model = genai.GenerativeModel(model_name='models/gemini-1.5-flash')
        
        # Compresión para asegurar que pase por la red de Rubiales
        buf = io.BytesIO()
        imagen_pil.save(buf, format='JPEG', quality=40)
        img_bytes = buf.getvalue()
        
        prompt_tecnico = f"Analiza este Estado Mecánico y extrae: {instruccion_especifica}. Solo datos técnicos."
        
        # Envío simplificado
        response = model.generate_content(
            contents=[
                {"parts": [
                    {"inline_data": {"mime_type": "image/jpeg", "data": img_bytes}},
                    {"text": prompt_tecnico}
                ]}
            ]
        )
        
        if response.text:
            return response.text
        else:
            return "No se detectó información clara."

    except Exception as e:
        error_msg = str(e)
        if "404" in error_msg:
            # Si el anterior falla, intentamos con la versión pro que a veces tiene rutas más estables
            return "⚠️ Error 404 persistente. Por favor, actualiza la librería o intenta con un recorte más pequeño."
        return f"⚠️ Error: {error_msg}"

# ==========================================
# 2. INTERFAZ DE USUARIO (STREAMLIT)
# ==========================================
st.set_page_config(page_title="Well Planning - CUA", page_icon="🏗️", layout="wide")

if 'menu_actual' not in st.session_state:
    st.session_state.menu_actual = "Home"

# Sidebar
with st.sidebar:
    st.markdown("<h1 style='text-align: center; color: #2E7D32;'>ECOPETROL 🦎</h1>", unsafe_allow_html=True)
    st.divider()
    if st.button("🏠 Inicio"):
        st.session_state.menu_actual = "Home"
        st.rerun()

# --- NAVEGACIÓN ---

if st.session_state.menu_actual == "Home":
    st.title("🚧 Construcción Well Plan - Operaciones CUA")
    st.info("Plataforma de extracción automática de datos para Estados Mecánicos.")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🌑 1. Abandonos", use_container_width=True):
            st.session_state.menu_actual = "Abandonos"
            st.rerun()
        if st.button("⚙️ 2. Mantenimiento BES", use_container_width=True):
            st.session_state.menu_actual = "BES"
            st.rerun()
    with col2:
        if st.button("📊 3. Rediseño SLA", use_container_width=True):
            st.session_state.menu_actual = "SLA"
            st.rerun()
        if st.button("🛠️ 4. Workover", use_container_width=True):
            st.session_state.menu_actual = "Workover"
            st.rerun()

elif st.session_state.menu_actual == "BES":
    st.title("⚙️ Extracción Secciones BES")
    
    def ui_seccion(titulo, prompt_inst, k_id):
        file = st.file_uploader(f"Recorte de {titulo}", type=["jpg", "png", "jpeg"], key=f"f_{k_id}")
        if file:
            img_pil = Image.open(file)
            st.image(img_pil, width=350)
            if st.button(f"🔍 Escanear {titulo}", key=f"b_{k_id}"):
                status = st.empty()
                bar = st.progress(10)
                with st.spinner("Analizando..."):
                    status.info("📡 Conectando con Gemini via REST...")
                    bar.progress(50)
                    res = skill_vision_well_plan(img_pil, prompt_inst)
                    bar.progress(100)
                    status.success("Listo")
                    st.success(f"**Datos:** {res}")

    t1, t2, t3 = st.tabs(["🏗️ Cabezal", "🕳️ Liner", "🔌 Sarta"])
    with t1:
        ui_seccion("Sección B", "Tipo de Tubing Head y PSI nominal", "head")
    with t2:
        ui_seccion("Revestimiento", "OD, Peso y Grado de Casing", "liner")
    with t3:
        ui_seccion("Sarta", "Profundidad bomba BES y Tubing", "sarta")

    st.divider()
    st.subheader("📝 Carga Manual de Control")
    c1, c2 = st.columns(2)
    with c1:
        st.number_input("Profundidad (ft)", value=3000)
    with c2:
        st.selectbox("Sección B", ["11 2K", "11 3K", "11 5K"])

else:
    st.title(f"Módulo {st.session_state.menu_actual}")
    st.warning("Sección en construcción...")
