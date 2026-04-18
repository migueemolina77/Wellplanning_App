import streamlit as st
import google.generativeai as genai
from PIL import Image

def skill_vision_well_plan(imagen_em):
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = """
    Analiza este Estado Mecánico de un pozo petrolero y extrae los siguientes datos en formato JSON:
    1. Sección B (Tubing Head)
    2. OD del Tubing de producción
    3. Profundidad de asentamiento de la bomba BES (ESP)
    4. OD del Casing de producción
    
    Si no encuentras un dato, pon 'No detectado'.
    """
    
    response = model.generate_content([prompt, imagen_em])
    return response.text

# 1. Configuración de página de alto nivel
st.set_page_config(
    page_title="Well Planning - Operaciones CLO",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo personalizado para mejorar la estética
st.markdown("""
    <style>
    .main {
        background-color: #f5f7f9;
    }
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 4em;
        background-color: #004a99;
        color: white;
        font-weight: bold;
        border: none;
    }
    .stButton>button:hover {
        background-color: #005bc5;
        border: 2px solid #ffffff;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. Inicialización del estado de navegación
if 'menu_actual' not in st.session_state:
    st.session_state.menu_actual = "Home"

# 3. Sidebar - Identidad Corporativa (Actualizado)
with st.sidebar:
  
    st.markdown("<h1 style='text-align: center; color: #2E7D32;'>ECOPETROL 🦎</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-weight: bold;'>Energía que Transforma</p>", unsafe_allow_html=True)
    
    st.title("Panel de Control")
    if st.button("🏠 Home"):
        st.session_state.menu_actual = "Home"
    st.markdown("---")
    st.info("Coordinación de Subsuelo")

# 4. Lógica de Navegación (Home)
if st.session_state.menu_actual == "Home":
    st.title("🚧 Construcción Well Plan - Operaciones CUA")
    st.subheader("Seleccione el tipo de operación para iniciar el diseño técnico:")
    
    st.markdown("---")
    
    # Creación de cuadrícula de botones tipo Dashboard
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🌑 1. Abandonos"):
            st.session_state.menu_actual = "Abandonos"
            st.rerun()
        
        if st.button("⚙️ 2. Retiro y/o Mantenimiento BES"):
            st.session_state.menu_actual = "BES"
            st.rerun()

    with col2:
        if st.button("📊 3. Rediseño SLA"):
            st.session_state.menu_actual = "SLA"
            st.rerun()
            
        if st.button("🛠️ 4. Workover"):
            st.session_state.menu_actual = "Workover"
            st.rerun()

# 5. Vistas de cada Módulo
elif st.session_state.menu_actual == "Abandonos":
    st.title("🌑 Módulo de Abandonos")
    st.write("Configuración de barreras, tapones de cemento y pruebas de integridad.")
    # Aquí irá tu lógica de abandonos...

elif st.session_state.menu_actual == "BES":
    st.title("⚙️ Retiro y/o Mantenimiento de BES")
    st.markdown("---")

    elif st.session_state.menu_actual == "BES":
    st.title("⚙️ Módulo de Extracción Inteligente")
    
    subida = st.file_uploader("Carga la imagen del Estado Mecánico", type=["jpg", "png", "jpeg"])
    
    if subida:
        img = Image.open(subida)
        st.image(img, caption="Estado Mecánico Cargado", width=400)
        
        if st.button("🔍 Ejecutar Skill de Visión"):
            with st.spinner("Gemini analizando esquema mecánico..."):
                # Aquí la IA lee el documento como el que me enviaste
                resultado = skill_vision_well_plan(img)
                st.markdown("### Datos Extraídos Automáticamente:")
                st.code(resultado)
                
                st.info("💡 Ahora estos datos alimentarán automáticamente los cálculos de BOP y Herramientas.")

    # 2. DETALLES DE LA BES
    st.header("2. Configuración de la BES")
    col_c, col_d = st.columns(2)
    
    with col_c:
        depth_pump = st.number_input("Profundidad de asentamiento (ft MD)", value=8500)
        cable_tipo = st.selectbox("Tipo de Cable de Potencia", ["#4 Flat", "#2 Round", "Lead Sheath"])
    
    with col_d:
        proteccion_cable = st.multiselect("Protección de Cable", ["Protectores de Acero", "Bandas de Monel", "Cross-coupling protectors"])
        sensor_fondo = st.checkbox("¿Cuenta con sensor de fondo?")

    # 3. BOTÓN DE CÁLCULO DE BARRERAS
    st.markdown("---")
    if st.button("🔄 Validar y Generar Secuencia Operativa"):
        st.success("Configuración validada exitosamente.")
        st.write(f"**Resumen para Well Plan:** Operación de retiro de BES en pozo con Tubing de {tubing_od} y Sección B {seccion_b}. Asegurar BOP de {bop_sugerida}.")

elif st.session_state.menu_actual == "SLA":
    st.title("📊 Rediseño SLA")
    st.write("Optimización de levantamiento artificial (Sucker Rod Pumping).")

elif st.session_state.menu_actual == "Workover":
    st.title("🛠️ Módulo de Workover")
    st.write("Intervención mayor al pozo para reacondicionamiento.")
