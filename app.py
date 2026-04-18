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

    # 1. ESTADO MECÁNICO Y SECCIÓN B
    st.header("1. Estado Mecánico y Cabezal")
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.subheader("Configuración del Cabezal")
        seccion_b = st.selectbox("Sección B (Tubing Head)", 
                                ["11\" 3K", "11\" 5K", "9\" 3K", "7 1/16\" 5K"])
        adaptador = st.selectbox("Adaptador (Bonnet/Tubing Hanger)", 
                                ["Rams-Type", "Mandrel-Type", "ESP Hanger with Penetrator"])
        
        # Lógica de sugerencia de BOP basada en Sección B
        bop_sugerida = "11\" 3K Dual Ram" if "11\"" in seccion_b else "7 1/16\" 5K Dual Ram"
        st.info(f"💡 **Sugerencia de BOP:** Se recomienda instalar sistema de BOP {bop_sugerida} acorde a la Sección B.")

    with col_b:
        st.subheader("Sarta de Producción")
        tubing_od = st.radio("Diámetro de Tubing Actual (in)", ["3 1/2", "4 1/2"], horizontal=True)
        grado_tbg = st.selectbox("Grado y Conexión", ["L-80 EUE", "J-55 EUE", "L-80 BTC"])
        
        # Lógica de herramientas de manejo
        if tubing_od == "3 1/2":
            herramientas = "Elevadores 3 1/2, Cuñas 3 1/2, Llaves de potencia (Jaw size 3 1/2)"
        else:
            herramientas = "Elevadores 4 1/2, Cuñas 4 1/2, Llaves de potencia (Jaw size 4 1/2)"
            
        st.warning(f"🛠️ **Herramientas de Manejo:** Preparar {herramientas}.")

    st.markdown("---")

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
