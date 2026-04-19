import streamlit as st
import easyocr
from PIL import Image
import numpy as np
import io
from streamlit_paste_button import paste_image_button

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
    st.info("Modo: Procesamiento Local + Smart Paste")
    st.divider()
    if st.button("🏠 Inicio", use_container_width=True):
        st.session_state.menu = "Home"
        st.rerun()

# --- Pantalla Principal ---
if st.session_state.menu == "Home":
    st.title("🚧 Construcción Well Plan - Operaciones CUA")
    st.info("Extracción de datos de subsuelo mediante OCR local y soporte de portapapeles.")
    
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
    
    # --- Lógica común para procesar imágenes ---
    def procesar_captura(label_id, key_suffix):
        col_u, col_p = st.columns(2)
        img_to_process = None
        
        with col_u:
            archivo = st.file_uploader(f"Cargar {label_id}", type=["jpg", "png", "jpeg"], key=f"u_{key_suffix}")
            if archivo: img_to_process = Image.open(archivo)
            
        with col_p:
            st.write(f"O pega el recorte de {label_id}:")
            pasted = paste_image_button(label=f"📋 Clic y Ctrl+V ({label_id})", key=f"p_{key_suffix}")
            if pasted.image_data: img_to_process = pasted.image_data

        if img_to_process:
            st.image(img_to_process, width=400, caption="Imagen cargada/pegada")
            if st.button(f"🔍 Escanear {label_id}", key=f"b_{key_suffix}"):
                with st.status("Analizando localmente...") as s:
                    resultado = skill_extract_text_local(img_to_process)
                    s.update(label="Escaneo completado", state="complete")
                st.success(f"**Resultado {label_id}:**")
                st.code(resultado)

    with tab1:
        st.subheader("Análisis de Cabezal (Sección B)")
        procesar_captura("Cabezal", "head")

    with tab2:
        st.subheader("Análisis de Revestimiento")
        procesar_captura("Liner/Casing", "liner")

    with tab3:
        st.subheader("Análisis de Sarta y Bomba")
        procesar_captura("Sarta", "sarta")

else:
    st.title(f"Módulo {st.session_state.menu}")
    st.warning("Esta sección se encuentra en desarrollo técnico.")
