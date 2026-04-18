import streamlit as st
import google.generativeai as genai
from PIL import Image

# 1. Función de IA Optimizada
def skill_vision_well_plan(imagen_em, instruccion_especifica):
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt_turbo = f"""
    Actúa como un experto en Well Planning. 
    Analiza este recorte y extrae únicamente: {instruccion_especifica}.
    Respuesta corta y directa. Si no lo ves, di 'No detectado'.
    """
    try:
        response = model.generate_content([prompt_turbo, imagen_em])
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"

# 2. Configuración de página
st.set_page_config(page_title="Well Planning CLO", page_icon="🏗️", layout="wide")

# 3. Inicialización del estado
if 'menu_actual' not in st.session_state:
    st.session_state.menu_actual = "Home"

# 4. Sidebar
with st.sidebar:
    st.markdown("<h1 style='text-align: center; color: #2E7D32;'>ECOPETROL 🦎</h1>", unsafe_allow_html=True)
    if st.button("🏠 Volver al Home"):
        st.session_state.menu_actual = "Home"
        st.rerun()

# 5. Lógica de Navegación
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
    st.info("💡 Haz clic en 'Browse files' y presiona Ctrl+V para pegar tu captura.")

    tab1, tab2, tab3 = st.tabs(["🏗️ Cabezal", "🕳️ Liner", "🔌 Sarta / BES"])

    with tab1:
        file_head = st.file_uploader("Pega recorte del Cabezal", type=["jpg", "png", "jpeg"], key="u_head")
        if file_head:
            img_head = Image.open(file_head)
            img_head.thumbnail((800, 800))
            st.image(img_head, width=300)
            if st.button("🔍 Extraer Cabezal"):
                with st.spinner("Analizando..."):
                    res = skill_vision_well_plan(img_head, "Tipo de Sección B y presión nominal")
                    st.success(res)

    with tab2:
        file_liner = st.file_uploader("Pega recorte del Liner", type=["jpg", "png", "jpeg"], key="u_liner")
        if file_liner:
            img_liner = Image.open(file_liner)
            img_liner.thumbnail((800, 800))
            st.image(img_liner, width=300)
            if st.button("🔍 Extraer Liner"):
                with st.spinner("Analizando..."):
                    res = skill_vision_well_plan(img_liner, "OD Casing, peso y grado")
                    st.success(res)

    with tab3:
        file_string = st.file_uploader("Pega recorte de la Sarta", type=["jpg", "png", "jpeg"], key="u_string")
        if file_string:
            img_string = Image.open(file_string)
            img_string.thumbnail((800, 800))
            st.image(img_string, width=300)
            if st.button("🔍 Extraer Sarta"):
                with st.spinner("Analizando..."):
                    res = skill_vision_well_plan(img_string, "OD Tubing y profundidad ESP")
                    st.success(res)

elif st.session_state.menu_actual == "Abandonos":
    st.title("🌑 Módulo de Abandonos")

elif st.session_state.menu_actual == "SLA":
    st.title("📊 Rediseño SLA")

elif st.session_state.menu_actual == "Workover":
    st.title("🛠️ Módulo de Workover")
