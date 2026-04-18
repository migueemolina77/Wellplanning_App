import streamlit as st

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

# 3. Sidebar - Identidad Corporativa
with st.sidebar:
    st.markdown("<h1 style='text-align: center; color: #2E7D32;'>ECOPETROL 🦎</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-weight: bold;'>Energía que Transforma</p>", unsafe_allow_html=True)

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
    st.title("⚙️ Retiro y/o Mantenimiento BES")
    st.write("Plan operativo para extracción de sistemas de bombeo electrosumergible.")
    # Aquí irá tu lógica de BES...

elif st.session_state.menu_actual == "SLA":
    st.title("📊 Rediseño SLA")
    st.write("Optimización de levantamiento artificial (Sucker Rod Pumping).")

elif st.session_state.menu_actual == "Workover":
    st.title("🛠️ Módulo de Workover")
    st.write("Intervención mayor al pozo para reacondicionamiento.")
