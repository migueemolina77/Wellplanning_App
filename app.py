import streamlit as st
import google.generativeai as genai
from PIL import Image
import io
import time

# ==========================================
# 1. CONFIGURACIÓN DE SEGURIDAD Y CONEXIÓN
# ==========================================

# Pegar aquí tu llave AIza...
API_KEY = AIzaSyCseXPIrBYZtrTW6NdCpqIKm_5j3WHG1dU 

def skill_vision_well_plan(imagen_pil, instruccion_especifica):
    """
    Versión blindada contra Error 404 y optimizada para redes lentas.
    """
    try:
        if API_KEY == "TU_API_KEY_AQUÍ" or not API_KEY:
            return "⚠️ ERROR: Configura la API KEY en la línea 12."

        # Configuración forzada para evitar conflictos de versión (v1beta vs v1)
        genai.configure(api_key=API_KEY, transport='rest')
        
        # Usamos la denominación 'gemini-1.5-flash' que es la versión estable
        model = genai.GenerativeModel(model_name='gemini-1.5-flash')
        
        # Compresión de imagen para asegurar el paso por Firewalls industriales
        buf = io.BytesIO()
        imagen_pil.save(buf, format='JPEG', quality=50)
        img_bytes = buf.getvalue()
        
        prompt_tecnico = f"""
        Actúa como un experto en ingeniería de subsuelo (Ecopetrol).
        Extrae del recorte: {instruccion_especifica}.
        Responde solo con datos. Si no hay datos, indica 'No detectado'.
        """
        
        # Envío mediante 'inline_data' para máxima compatibilidad REST
        response = model.generate_content(
            contents=[
                {
                    "role": "user", 
                    "parts": [
                        {"inline_data": {"mime_type": "image/jpeg", "data": img_bytes}},
                        {"text": prompt_tecnico}
                    ]
                }
            ],
            request_options={"timeout": 60} 
        )
        
        if response and response.text:
            return response.text
        else:
            return "⚠️ El servidor respondió pero el análisis quedó vacío."

    except Exception as e:
        error_msg = str(e)
        # Manejo específico del error 404 visto anteriormente
        if "404" in error_msg:
            return "⚠️ ERROR 404: El modelo no fue encontrado. Intenta actualizar la librería con: pip install -U google-generativeai"
        if "403" in error_msg:
            return "⚠️ ERROR 403: La API KEY no tiene permisos o es inválida."
        return f"⚠️ ERROR TÉCNICO: {error_msg}"

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
