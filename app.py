import streamlit as st
import google.generativeai as genai
from PIL import Image
import io
import time

# ==========================================
# 1. CONFIGURACIÓN DE SEGURIDAD Y CONEXIÓN
# ==========================================

# OPCIÓN A: Pegar la llave directamente (Para pruebas locales)
API_KEY = "AIzaSyCseXPIrBYZtrTW6NdCpqIKm_5j3WHG1dU" 

# OPCIÓN B: Usar Secrets de Streamlit (Para cuando subas la app a la web)
# API_KEY = st.secrets["GEMINI_KEY"]

def skill_vision_well_plan(imagen_pil, instruccion_especifica):
    """
    Versión optimizada para redes de campo (Rubiales/CUA).
    Usa transporte REST y compresión agresiva.
    """
    try:
        # Validar que la llave no esté vacía
        if API_KEY == "TU_API_KEY_AQUÍ" or not API_KEY:
            return "⚠️ ERROR: No has configurado la API KEY en el código."

        # Configuración del modelo con protocolo REST (más estable que gRPC)
        genai.configure(api_key=API_KEY, transport='rest')
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Reducción de peso de imagen (JPEG al 50% de calidad)
        buf = io.BytesIO()
        imagen_pil.save(buf, format='JPEG', quality=50)
        img_bytes = buf.getvalue()
        
        prompt_tecnico = f"""
        Actúa como un experto en Well Planning de Ecopetrol.
        Analiza este recorte técnico y extrae: {instruccion_especifica}.
        REGLA: Responde solo con los datos técnicos encontrados.
        """
        
        # Envío de contenido en formato 'inline_data' (binario puro)
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
            return "⚠️ La IA no detectó texto claro. Intenta con un recorte más nítido."

    except Exception as e:
        error_msg = str(e)
        if "403" in error_msg or "API_KEY_INVALID" in error_msg:
            return "⚠️ ERROR DE LLAVE: La API KEY es incorrecta o no tiene permisos."
        if "429" in error_msg:
            return "⚠️ LÍMITE ALCANZADO: Demasiadas peticiones. Espera un momento."
        return f"⚠️ ERROR TÉCNICO: {error_msg}"

# ==========================================
# 2. INTERFAZ DE USUARIO (STREAMLIT)
# ==========================================
st.set_page_config(page_title="Well Planning - Operaciones", page_icon="🏗️", layout="wide")

# Inicializar navegación
if 'menu_actual' not in st.session_state:
    st.session_state.menu_actual = "Home"

# Sidebar
with st.sidebar:
    st.markdown("<h1 style='text-align: center; color: #2E7D32;'>ECOPETROL 🦎</h1>", unsafe_allow_html=True)
    st.divider()
    if st.button("🏠 Volver al Inicio", use_container_width=True):
        st.session_state.menu_actual = "Home"
        st.rerun()

# --- LÓGICA DE NAVEGACIÓN ---

if st.session_state.menu_actual == "Home":
    st.title("🚧 Construcción Well Plan - Operaciones CUA")
    st.subheader("Seleccione el módulo de trabajo:")
    
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
    st.title("⚙️ Módulo de Extracción por Secciones (BES)")
    st.info("💡 Pega o sube el recorte del Estado Mecánico (EM) en la pestaña correspondiente.")

    # Función interna para procesar pestañas y evitar repetir código
    def ejecutar_analisis_tab(label, instruccion, key_id):
        archivo = st.file_uploader(f"Subir recorte de {label}", type=["jpg", "png", "jpeg"], key=f"f_{key_id}")
        if archivo:
            img = Image.open(archivo)
            st.image(img, width=400, caption=f"Recorte: {label}")
            
            if st.button(f"🔍 Analizar {label}", key=f"b_{key_id}"):
                status = st.empty()
                progreso = st.progress(10)
                
                with st.spinner(f"Escaneando {label}..."):
                    status.info("📡 Conectando con servidor de IA (Protocolo REST)...")
                    progreso.progress(50)
                    
                    resultado = skill_vision_well_plan(img, instruccion)
                    
                    progreso.progress(100)
                    status.success("✅ Análisis completado")
                    st.markdown(f"### Datos Extraídos:\n{resultado}")

    tab1, tab2, tab3 = st.tabs(["🏗️ Cabezal (BOP)", "🕳️ Liner / Casing", "🔌 Sarta / BES"])

    with tab1:
        ejecutar_analisis_tab("Cabezal", "Sección B, Tubing Head y Presión Nominal", "head")
    with tab2:
        ejecutar_analisis_tab("Casing", "OD del Casing, Peso y Grado del acero", "liner")
    with tab3:
        ejecutar_analisis_tab("Sarta", "Profundidad bomba BES y OD Tubing", "sarta")

    st.divider()
    st.subheader("2. Verificación y Ajustes Manuales")
    c1, c2 = st.columns(2)
    with c1:
        st.number_input("Profundidad de asentamiento (ft MD)", value=3433)
        st.selectbox("Diámetro de Tubing", ["3 1/2\"", "4 1/2\""])
    with c2:
        st.selectbox("Sección B", ["11\" 2K", "11\" 3K", "11\" 5K"])
        st.checkbox("¿Cuenta con sensor de fondo?")

# Módulos en desarrollo
else:
    st.title(f"Módulo {st.session_state.menu_actual}")
    st.warning("Esta sección se encuentra actualmente en desarrollo técnico.")
