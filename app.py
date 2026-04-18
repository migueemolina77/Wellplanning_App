import streamlit as st
import google.generativeai as genai
from PIL import Image

# Configuración de la IA (Asegúrate de configurar tu API Key si es necesario)
def skill_vision_well_plan(imagen_em):
    # Nota: Aquí deberías configurar genai.configure(api_key="TU_KEY") si lo usas fuera de un entorno con acceso directo
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

# 1. Configuración de página
st.set_page_config(
    page_title="Well Planning - Operaciones CLO",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo personalizado
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 3.5em;
        background-color: #004a99;
        color: white;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. Inicialización del estado
if 'menu_actual' not in st.session_state:
    st.session_state.menu_actual = "Home"

# 3. Sidebar
with st.sidebar:
    st.markdown("<h1 style='text-align: center; color: #2E7D32;'>ECOPETROL 🦎</h1>", unsafe_allow_html=True)
    if st.button("🏠 Volver al Home"):
        st.session_state.menu_actual = "Home"
    st.markdown("---")
    st.info("Coordinación de Subsuelo")

# 4. Navegación
if st.session_state.menu_actual == "Home":
    st.title("🚧 Construcción Well Plan - Operaciones CUA")
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

elif st.session_state.menu_actual == "BES":
    st.title("⚙️ Módulo de Extracción por Secciones")
    st.info("💡 Haz clic en el recuadro y presiona **Ctrl + V** para pegar tu recorte del Estado Mecánico.")

    tab1, tab2, tab3 = st.tabs(["🏗️ Cabezal (BOP)", "🕳️ Liner / Casing", "🔌 Sarta / BES"])

    with tab1:
        st.subheader("Información de Sección B / Cabezal")
        # El componente de pegado directo
        img_paste_head = st.image_paste_button(label="📋 Pegar recorte del Cabezal", key="paste_head")
        
        if img_paste_head:
            st.image(img_paste_head, caption="Imagen pegada", width=300)
            if st.button("🔍 Extraer Cabezal", key="btn_head"):
                with st.spinner("Analizando..."):
                    res = skill_vision_well_plan(img_paste_head, "Extrae tipo de Sección B y presiones")
                    st.success(res)

    with tab2:
        st.subheader("Información de Revestimiento")
        img_paste_liner = st.image_paste_button(label="📋 Pegar recorte del Liner", key="paste_liner")
        
        if img_paste_liner:
            st.image(img_paste_liner, caption="Imagen pegada", width=300)
            if st.button("🔍 Extraer Liner", key="btn_liner"):
                with st.spinner("Analizando..."):
                    res = skill_vision_well_plan(img_paste_liner, "Extrae OD Casing, Grado y Conexión")
                    st.success(res)

    with tab3:
        st.subheader("Información de Sarta y BES")
        img_paste_string = st.image_paste_button(label="📋 Pegar recorte de la Sarta", key="paste_string")
        
        if img_paste_string:
            st.image(img_paste_string, caption="Imagen pegada", width=300)
            if st.button("🔍 Extraer Sarta", key="btn_string"):
                with st.spinner("Analizando..."):
                    res = skill_vision_well_plan(img_paste_string, "Extrae OD Tubing y Profundidad ESP")
                    st.success(res)

    st.markdown("---")
    
    # SECCIÓN 2: DETALLES (MANUAL O COMPLEMENTARIO)
    st.header("2. Configuración de la Operación")
    col_c, col_d = st.columns(2)
    with col_c:
        depth_pump = st.number_input("Profundidad de asentamiento (ft MD)", value=3433)
        tubing_od = st.selectbox("Diámetro de Tubing", ["3 1/2", "4 1/2"])
    with col_d:
        seccion_b = st.selectbox("Sección B", ["11\" 2K", "11\" 3K", "11\" 5K"])
        sensor_fondo = st.checkbox("¿Cuenta con sensor de fondo?")

    if st.button("🔄 Validar Plan Operativo"):
        st.success(f"Plan validado para Tubing {tubing_od} en Sección B {seccion_b}")

elif st.session_state.menu_actual == "Abandonos":
    st.title("🌑 Módulo de Abandonos")

elif st.session_state.menu_actual == "SLA":
    st.title("📊 Rediseño SLA")

elif st.session_state.menu_actual == "Workover":
    st.title("🛠️ Módulo de Workover")
