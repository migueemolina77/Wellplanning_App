import streamlit as st
import google.generativeai as genai
from PIL import Image
import io
import time

# ==========================================
# 1. CONFIGURACIÓN DE SEGURIDAD Y CONEXIÓN
# ==========================================
# Reemplaza 'TU_API_KEY' con tu clave real
API_KEY = "TU_API_KEY_AQUI" 

def skill_vision_well_plan(imagen_pil, instruccion_especifica):
    """
    Versión 'Field-Ready': Convierte imagen a bytes ultra-ligeros 
    y usa transporte REST para redes inestables.
    """
    try:
        # Configuración forzada en cada llamada para evitar desconexiones
        genai.configure(api_key=API_KEY, transport='rest')
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # OPTIMIZACIÓN DE IMAGEN: Convertimos a JPEG calidad 50% (Suficiente para texto)
        buf = io.BytesIO()
        imagen_pil.save(buf, format='JPEG', quality=50)
        img_bytes = buf.getvalue()
        
        prompt_tecnico = f"""
        CONTEXTO: Ingeniería de Petróleos - Well Planning.
        TAREA: Extraer exactamente: {instruccion_especifica}.
        REGLA: Responde solo con los datos. Si no los ves, di 'Dato no visible'.
        """
        
        # ENVÍO CRUDO (Más rápido y compatible con Firewalls)
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
            request_options={"timeout": 60} # Espera hasta 1 minuto
        )
        
        if response and response.text:
            return response.text
        else:
            return "⚠️ La IA procesó la imagen pero la respuesta llegó vacía."

    except Exception as e:
        error_str = str(e).lower()
        if "deadline" in error_str or "timeout" in error_str:
            return "⚠️ TIEMPO AGOTADO: La red en Rubiales está muy lenta. Intenta con un recorte más pequeño."
        if "api_key" in error_str or "403" in error_str:
            return "⚠️ ERROR DE LLAVE: Verifica que la API KEY sea correcta."
        return f"⚠️ ERROR TÉCNICO: {str(e)}"

# ==========================================
# 2. INTERFAZ DE USUARIO (STREAMLIT)
# ==========================================
st.set_page_config(page_title="Well Planning CLO", page_icon="🏗️", layout="wide")

if 'menu_actual' not in st.session_state:
    st.session_state.menu_actual = "Home"

# Sidebar
with st.sidebar:
    st.markdown("<h1 style='text-align: center; color: #2E7D32;'>ECOPETROL 🦎</h1>", unsafe_allow_html=True)
    st.write(f"**Usuario:** {st.experimental_user.email if hasattr(st, 'experimental_user') else 'Ingeniero'}")
    if st.button("🏠 Inicio"):
        st.session_state.menu_actual = "Home"
        st.rerun()

# Lógica de Navegación
if st.session_state.menu_actual == "Home":
    st.title("🚧 Construcción Well Plan - Operaciones")
    if st.button("⚙️ Ir a Mantenimiento BES", use_container_width=True):
        st.session_state.menu_actual = "BES"
        st.rerun()

elif st.session_state.menu_actual == "BES":
    st.title("⚙️ Módulo de Extracción BES")
    
    # Función de Interfaz para cada Pestaña
    def ui_extractor(label, instruccion, key_id):
        archivo = st.file_uploader(f"Cargar recorte: {label}", type=["jpg", "png", "jpeg"], key=f"up_{key_id}")
        if archivo:
            img = Image.open(archivo)
            st.image(img, width=350, caption="Recorte para analizar")
            
            if st.button(f"🔍 Escanear {label}", key=f"btn_{key_id}"):
                status = st.empty()
                bar = st.progress(20)
                
                with st.spinner("Comunicando con Gemini..."):
                    status.info("📡 Enviando paquete de datos optimizado...")
                    resultado = skill_vision_well_plan(img, instruccion)
                    
                    bar.progress(100)
                    status.success("✅ Proceso terminado")
                    st.markdown(f"**Resultado:**\n{resultado}")

    tabs = st.tabs(["🏗️ Cabezal", "🕳️ Liner", "🔌 Sarta"])
    
    with tabs[0]:
        ui_extractor("Sección B", "Tipo de Cabezal y Presión Nominal", "head")
    with tabs[1]:
        ui_extractor("Revestimiento", "OD, Peso y Grado del Casing", "liner")
    with tabs[2]:
        ui_extractor("BES", "Profundidad de la bomba y OD Tubing", "sarta")

    # Formulario Manual (Persistente)
    st.divider()
    st.subheader("📝 Validación Manual")
    col1, col2 = st.columns(2)
    with col1:
        st.text_input("Profundidad MD", placeholder="Ej: 3450 ft")
    with col2:
        st.selectbox("Tipo de Equipo", ["BES - Etapas estándar", "BES - Alto Volumen", "SLA"])
