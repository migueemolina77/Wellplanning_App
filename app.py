import streamlit as st
import pandas as pd
from io import StringIO

# ==========================================
# 1. CONFIGURACIÓN Y ESTILO
# ==========================================
st.set_page_config(page_title="Well Planning Hub - CUA", page_icon="🏗️", layout="wide")

# Estilo para que se vea profesional
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { border-radius: 8px; height: 3em; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. MOTOR DE PROCESAMIENTO
# ==========================================
def procesar_tabla_copilot(texto):
    try:
        # Copilot suele entregar tablas separadas por tabs o comas
        clean_text = texto.replace('\t', ',')
        df = pd.read_csv(StringIO(clean_text), sep=None, engine='python')
        return df
    except Exception as e:
        st.error(f"Error al procesar los datos de Copilot: {e}")
        return None

# ==========================================
# 3. NAVEGACIÓN PRINCIPAL (CORREGIDA)
# ==========================================
with st.sidebar:
    st.markdown("<h1 style='text-align: center; color: #2E7D32;'>ECOPETROL 🦎</h1>", unsafe_allow_html=True)
    
    # SOLUCIÓN AL ERROR: Usamos un container para el borde en vez de st.markdown directamente
    with st.container(border=True):
        st.markdown("<p style='text-align: center; margin-bottom: 0;'>Operaciones CLO</p>", unsafe_allow_html=True)
    
    st.divider()
    
    if 'menu' not in st.session_state:
        st.session_state.menu = "Home"
        
    if st.button("🏠 Inicio", use_container_width=True): st.session_state.menu = "Home"
    
    st.markdown("### 🛠️ Módulos de Operación")
    if st.button("🌑 Abandono de Pozo", use_container_width=True): st.session_state.menu = "Abandono"
    if st.button("⚙️ Mantenimiento / Cambio BES", use_container_width=True): st.session_state.menu = "BES"
    if st.button("🛠️ Workover", use_container_width=True): st.session_state.menu = "Workover"
    if st.button("📊 Rediseño SLA", use_container_width=True): st.session_state.menu = "SLA"

# ==========================================
# 4. CONTENIDO POR MÓDULO
# ==========================================
if st.session_state.menu == "Home":
    st.title("🚧 Sistema Integrado de Well Planning")
    st.info("Seleccione un módulo operativo para comenzar la ingeniería.")

elif st.session_state.menu == "BES":
    st.title("⚙️ Módulo: Mantenimiento / Cambio BES")
    
    # Sección de carga de datos vía Copilot
    with st.container(border=True):
        st.markdown("#### 📥 Carga de Estado Mecánico (vía Copilot)")
        st.write("Copia la tabla del PDF procesada por Copilot y pégala aquí:")
        input_data = st.text_area("Datos de Copilot:", height=200, placeholder="Componente, Long, OD, Top, Base...")
        
        if st.button("🚀 Procesar e Iniciar"):
            if input_data:
                df = procesar_tabla_copilot(input_data)
                if df is not None:
                    st.session_state.df_bes = df
                    st.success("Tabla cargada correctamente.")

    if 'df_bes' in st.session_state:
        st.divider()
        st.subheader("Ingeniería de Sarta")
        st.dataframe(st.session_state.df_bes, use_container_width=True)

# Módulos vacíos para mantener la estructura solicitada
elif st.session_state.menu == "Abandono":
    st.title("🌑 Módulo: Abandono de Pozo")
    st.info("Área de configuración de tapones.")

elif st.session_state.menu == "Workover":
    st.title("🛠️ Módulo: Workover")
    st.info("Optimización de intervenciones.")

elif st.session_state.menu == "SLA":
    st.title("📊 Módulo: Rediseño SLA")
    st.info("Análisis de bombeo mecánico.")
