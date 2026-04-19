import streamlit as st
import pandas as pd
from io import StringIO
import re

# ==========================================
# 1. CONFIGURACIÓN Y ESTILO CORPORATIVO
# ==========================================
st.set_page_config(page_title="Well Planning Hub - CUA", page_icon="🏗️", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { border-radius: 8px; height: 3em; transition: 0.3s; }
    .stButton>button:hover { background-color: #1b5e20; color: white; border: 1px solid #1b5e20; }
    div[data-testid="stExpander"] { border: 1px solid #e0e0e0; border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. LOGICA DE PROCESAMIENTO (EL MOTOR)
# ==========================================

def procesar_tabla_copilot(texto):
    """Convierte el pegado de Copilot en un DataFrame limpio."""
    try:
        # Reemplazamos tabulaciones comunes de Copilot/Excel por comas para lectura
        clean_text = texto.replace('\t', ',')
        df = pd.read_csv(StringIO(clean_text), sep=None, engine='python')
        
        # Estandarización de nombres de columnas (por si Copilot varía un poco)
        mapeo = {
            'Long': 'Long(ft)', 'OD': 'OD(in)', 'Desc': 'Descripción del Componente',
            'Top': 'MD Top(ft)', 'Base': 'Base MD(ft)'
        }
        for col in df.columns:
            for clave, valor in mapeo.items():
                if clave.lower() in col.lower():
                    df.rename(columns={col: valor}, inplace=True)
        return df
    except Exception as e:
        st.error(f"Error en formato: {e}")
        return None

# ==========================================
# 3. NAVEGACIÓN PRINCIPAL (SIDEBAR)
# ==========================================

with st.sidebar:
    st.markdown("<h1 style='text-align: center; color: #2E7D32;'>ECOPETROL 🦎</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Operaciones CUA</p>", border=True)
    st.divider()
    
    # Mantenemos el estado de navegación
    if 'menu' not in st.session_state:
        st.session_state.menu = "Home"
        
    if st.button("🏠 Inicio", use_container_width=True): st.session_state.menu = "Home"
    
    st.markdown("### 🛠️ Módulos de Operación")
    if st.button("🌑 Abandono de Pozo", use_container_width=True): st.session_state.menu = "Abandono"
    if st.button("⚙️ Mantenimiento / Cambio BES", use_container_width=True): st.session_state.menu = "BES"
    if st.button("🛠️ Workover", use_container_width=True): st.session_state.menu = "Workover"
    if st.button("📊 Rediseño SLA", use_container_width=True): st.session_state.menu = "SLA"

# ==========================================
# 4. CONTENIDO DE LOS MÓDULOS
# ==========================================

if st.session_state.menu == "Home":
    st.title("🚧 Sistema Integrado de Well Planning")
    st.info("Seleccione un módulo operativo en el panel izquierdo para comenzar la ingeniería.")

elif st.session_state.menu == "BES":
    st.title("⚙️ Módulo: Mantenimiento / Cambio BES")
    st.subheader("1. Carga del Estado Mecánico Actual")
    
    # Contenedor para Copilot
    with st.container(border=True):
        col_inst, col_data = st.columns([1, 2])
        
        with col_inst:
            st.markdown("### 🤖 Instrucciones Copilot")
            st.write("1. Sube el PDF a Copilot.")
            st.write("2. Pide la tabla de estado mecánico en formato plano.")
            st.info("Copilot procesará el PDF internamente y te entregará la data limpia.")
        
        with col_data:
            input_copilot = st.text_area("Pega aquí los datos entregados por Copilot:", height=250, placeholder="Componente, Long, OD, Top, Base...")
            if st.button("🚀 Procesar e Iniciar Ingeniería"):
                if input_copilot:
                    df_resultado = procesar_tabla_copilot(input_copilot)
                    if df_resultado is not None:
                        st.session_state.df_bes = df_resultado
                        st.success("¡Datos cargados exitosamente!")

    # Si hay datos, mostramos el desglose operativo
    if 'df_bes' in st.session_state:
        st.divider()
        st.subheader("2. Revisión de Componentes Detectados")
        
        tab_full, tab_sarta = st.tabs(["📋 Vista Completa", "🔌 Análisis de Sarta BES"])
        
        with tab_full:
            st.dataframe(st.session_state.df_bes, use_container_width=True)
            
        with tab_sarta:
            # Filtro simple para mostrar solo lo relevante a BES (Sumergible)
            sarta = st.session_state.df_bes[st.session_state.df_bes['Descripción del Componente'].str.contains('ESP|MOTOR|INTAKE|CABLE|SENSOR', case=False, na=False)]
            st.dataframe(sarta, use_container_width=True)
            st.button("💾 Confirmar sarta para rediseño")

elif st.session_state.menu == "Abandono":
    st.title("🌑 Módulo: Abandono de Pozo")
    st.warning("Sección en desarrollo: Cálculo de tapones de cemento y retenedores.")

elif st.session_state.menu == "Workover":
    st.title("🛠️ Módulo: Workover")
    st.warning("Sección en desarrollo: Optimización de tiempos y pesca (fishing).")

elif st.session_state.menu == "SLA":
    st.title("📊 Módulo: Rediseño SLA")
    st.warning("Sección en desarrollo: Análisis de fatiga de varillas.")
