import streamlit as st
import pandas as pd
from io import StringIO

# ==========================================
# 1. CONFIGURACIÓN Y ESTILO
# ==========================================
st.set_page_config(page_title="Well Planning Hub - CUA", page_icon="🏗️", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { border-radius: 8px; height: 3em; background-color: #2E7D32; color: white; }
    .stFileUploader { border: 2px dashed #2E7D32; border-radius: 10px; padding: 10px; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. MOTOR DE CONEXIÓN CON COPILOT (IA)
# ==========================================
def procesar_pdf_con_ia(archivo_pdf):
    """
    Esta función envía el PDF al motor de Copilot/Azure 
    y retorna la tabla ya estructurada.
    """
    # Aquí iría el protocolo de conexión (API Key) de la compañía
    # Por ahora, simulamos el procesamiento exitoso de la IA
    with st.spinner("🤖 Copilot está analizando las capas del PDF..."):
        # En una implementación real, aquí se envía el archivo al endpoint de Azure
        # resultado = cliente_azure.analyze_document(archivo_pdf)
        
        # Simulación de respuesta estructurada que devuelve la IA
        data_simulada = """Componente,Long(ft),OD(in),MD Top(ft),Base MD(ft)
        TUBING HANGER 7 1/16,0.83,7.125,24.5,25.4
        TUBING 3 1/2,3337.45,3.500,25.4,3362.8
        PUP JOINT 3 1/2,7.97,3.500,3362.8,3370.8
        """
        df = pd.read_csv(StringIO(data_simulada))
        return df

# ==========================================
# 3. NAVEGACIÓN (SIDEBAR)
# ==========================================
with st.sidebar:
    st.markdown("<h1 style='text-align: center; color: #2E7D32;'>ECOPETROL 🦎</h1>", unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown("<p style='text-align: center; margin-bottom: 0;'>Operaciones CUA</p>", unsafe_allow_html=True)
    st.divider()
    
    if 'menu' not in st.session_state: st.session_state.menu = "Home"
        
    if st.button("🏠 Inicio", use_container_width=True): st.session_state.menu = "Home"
    st.markdown("### 🛠️ Módulos de Operación")
    if st.button("🌑 Abandono de Pozo", use_container_width=True): st.session_state.menu = "Abandono"
    if st.button("⚙️ Mantenimiento / Cambio BES", use_container_width=True): st.session_state.menu = "BES"
    if st.button("🛠️ Workover", use_container_width=True): st.session_state.menu = "Workover"
    if st.button("📊 Rediseño SLA", use_container_width=True): st.session_state.menu = "SLA"

# ==========================================
# 4. CONTENIDO - MÓDULO BES
# ==========================================
if st.session_state.menu == "Home":
    st.title("🚧 Sistema Integrado de Well Planning")
    st.info("Bienvenido. Cargue el estado mecánico dentro del módulo BES para iniciar.")

elif st.session_state.menu == "BES":
    st.title("⚙️ Mantenimiento / Cambio BES")
    
    # NUEVO PROTOCOLO: CARGA DIRECTA DE PDF
    with st.container(border=True):
        st.subheader("📁 Carga de Estado Mecánico")
        st.write("Suba el archivo PDF original. El motor de Copilot extraerá la información automáticamente.")
        
        uploaded_file = st.file_uploader("Arrastre el PDF aquí", type=["pdf"])
        
        if uploaded_file is not None:
            st.success("Archivo recibido.")
            if st.button("🚀 Procesar con IA de Copilot"):
                # Llamamos a la función que conecta con la IA
                df_final = procesar_pdf_con_ia(uploaded_file)
                st.session_state.df_bes = df_final

    # Resultados post-procesamiento
    if 'df_bes' in st.session_state:
        st.divider()
        st.subheader("📊 Datos Extraídos del PDF")
        st.dataframe(st.session_state.df_bes, use_container_width=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.button("✅ Confirmar y Seguir a Diseño de Sarta")
        with col2:
            if st.button("❌ Borrar y Reintentar"):
                del st.session_state.df_bes
                st.rerun()

# Mantener los otros módulos para no perder la estructura
elif st.session_state.menu in ["Abandono", "Workover", "SLA"]:
    st.title(f"Módulo {st.session_state.menu}")
    st.warning("Sección en configuración técnica.")
