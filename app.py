import streamlit as st
import easyocr
from PIL import Image
import numpy as np
import io

# ==========================================
# 1. MOTOR DE EXTRACCIÓN LOCAL (EasyOCR)
# ==========================================

@st.cache_resource
def load_ocr_model():
    # Cargamos el modelo en memoria una sola vez (Español e Inglés)
    return easyocr.Reader(['es', 'en'], gpu=False)

def skill_extract_text_local(imagen_pil):
    try:
        reader = load_ocr_model()
        
        # Convertir imagen PIL a formato compatible (numpy array)
        img_array = np.array(imagen_pil.convert('RGB'))
        
        # Leer texto de la imagen
        results = reader.readtext(img_array, detail=0)
        
        if results:
            # Unimos los textos encontrados con saltos de línea
            return "\n".join(results)
        else:
            return "⚠️ No se detectó texto en el recorte. Intenta con una imagen más clara."
            
    except Exception as e:
        return f"❌ Error en el motor local: {str(e)}"

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
    st.info("Modo: Procesamiento Local (Sin API)")
    st.divider()
    if st.button("🏠 Inicio", use_container_width=True):
        st.session_state.menu = "Home"
        st.rerun()

# --- Pantalla Principal ---
if st.session_state.menu == "Home":
    st.title("🚧 Construcción Well Plan - Operaciones CUA")
    st.info("Extracción de datos de subsuelo mediante OCR local.")
    
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
                with st.status("Analizando imagen localmente...") as s:
                    resultado = skill_extract_text_local(img)
                    s.update(label="Escaneo completado", state="complete")
                st.success("**Texto detectado en Cabezal:**")
                st.code(resultado)

    with tab2:
        st.subheader("Análisis de Revestimiento")
        archivo2 = st.file_uploader("Cargar recorte de Liner/Casing", type=["jpg", "png", "jpeg"], key="u_liner")
        if archivo2:
            img2 = Image.open(archivo2)
            st.image(img2, width=400)
            if st.button("🔍 Escanear Liner"):
                with st.spinner("Leyendo datos..."):
                    resultado = skill_extract_text_local(img2)
                    st.info("**Datos de Liner detectados:**")
                    st.code(resultado)

    with tab3:
        st.subheader("Análisis de Sarta y Bomba")
        archivo3 = st.file_uploader("Cargar recorte de Sarta", type=["jpg", "png", "jpeg"], key="u_sarta")
        if archivo3:
            img3 = Image.open(archivo3)
            st.image(img3, width=400)
            if st.button("🔍 Escanear Sarta"):
                with st.spinner("Procesando..."):
                    resultado = skill_extract_text_local(img3)
                    st.info("**Datos de Sarta detectados:**")
                    st.code(resultado)

else:
    st.title(f"Módulo {st.session_state.menu}")
    st.warning("Esta sección se encuentra en desarrollo técnico.")
