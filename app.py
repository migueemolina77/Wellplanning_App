import streamlit as st
import google.generativeai as genai
from PIL import Image

# 1. Función de IA Corregida (Ahora acepta el prompt dinámico)
def skill_vision_well_plan(imagen_em, instruccion_especifica):
    # Usamos flash-lite o configuraciones de bajo consumo de tokens para velocidad
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # Prompt optimizado para velocidad: Le pedimos solo el dato, sin explicaciones
    prompt_turbo = f"""
    Actúa como un experto en Well Planning de Rubiales. 
    Analiza este recorte y extrae únicamente: {instruccion_especifica}.
    Respuesta corta y directa. Si no lo ves, di 'No detectado'.
    """
    
    try:
        response = model.generate_content([prompt_turbo, imagen_em])
        return response.text
    except Exception as e:
        return f"Error de conexión: {str(e)}"

# 2. Configuración de página
st.set_page_config(
    page_title="Well Planning - Operaciones CLO",
    page_icon="🏗️",
    layout="wide"
)

# 2. Inicialización del estado
if 'menu_actual' not in st.session_state:
    st.session_state.menu_actual = "Home"

# 3. Sidebar
with st.sidebar:
    st.markdown("<h1 style='text-align: center; color: #2E7D32;'>ECOPETROL 🦎</h1>", unsafe_allow_html=True)
    if st.button("🏠 Volver al Home"):
        st.session_state.menu_actual = "Home"
        st.rerun()

# 4. Lógica de Navegación
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
    st.info("💡 **Tip de agilidad:** Haz clic en 'Browse files' y presiona **Ctrl + V** para pegar tu captura directamente.")

    tab1, tab2, tab3 = st.tabs(["🏗️ Cabezal (BOP)", "🕳️ Liner / Casing", "🔌 Sarta / BES"])

    with tab1:
        st.subheader("Información de Sección B / Cabezal")
        # El uploader nativo acepta Ctrl+V si haces clic en él
        file_head = st.file_uploader("Pega o sube el recorte del Cabezal", type=["jpg", "png", "jpeg"], key="u_head")
        if file_head:
            img_head = Image.open(file_head)
            st.image(img_head, width=300)
            if st.button("🔍 Extraer Cabezal"):
                with st.spinner("Analizando cabezal..."):
                    res = skill_vision_well_plan(img_head, "Identifica el tipo de Sección B (Tubing Head) y su presión nominal.")
                    st.success(res)

    with tab2:
        st.subheader("Información de Revestimiento")
        file_liner = st.file_uploader("Pega o sube el recorte del Liner", type=["jpg", "png", "jpeg"], key="u_liner")
        if file_liner:
            img_liner = Image.open(file_liner)
            st.image(img_liner, width=300)
            if st.button("🔍 Extraer Liner"):
                with st.spinner("Analizando revestimiento..."):
                    res = skill_vision_well_plan(img_liner, "Extrae el OD del Casing de producción, su peso y grado.")
                    st.success(res)

    with tab3:
        st.subheader("Información de Sarta y BES")
        file_string = st.file_uploader("Pega o sube el recorte de la Sarta", type=["jpg", "png", "jpeg"], key="u_string")
        if file_string:
            img_string = Image.open(file_string)
            st.image(img_string, width=300)
            if st.button("🔍 Extraer Sarta"):
                with st.spinner("Analizando sarta..."):
                    res = skill_vision_well_plan(img_string, "Extrae el OD del Tubing y la profundidad de asentamiento de la bomba BES.")
                    st.success(res)

    st.markdown("---")
    st.header("2. Configuración Manual de Verificación")
    col_c, col_d = st.columns(2)
    with col_c:
        depth_pump = st.number_input("Profundidad de asentamiento (ft MD)", value=3433)
        tubing_od = st.selectbox("Diámetro de Tubing", ["3 1/2", "4 1/2"])
    with col_d:
        seccion_b = st.selectbox("Sección B", ["11\" 2K", "11\" 3K", "11\" 5K"])
        sensor_fondo = st.checkbox("¿Cuenta con sensor de fondo?")
