import streamlit as st
import pandas as pd
from io import StringIO

# ==========================================
# 1. CONFIGURACIÓN Y ESTILO
# ==========================================
st.set_page_config(page_title="Well Planning Hub - CUA", page_icon="🏗️", layout="wide")

# ==========================================
# 2. MOTOR DE IA CON "SUPER PROMPT"
# ==========================================
def procesar_pdf_con_ia_total(archivo_pdf):
    """
    Simulación del motor enviando un Super Prompt a Copilot/Azure.
    El objetivo es que no se limite a una sola tabla.
    """
    with st.spinner("🔍 Analizando el pozo completo (Cabezales, Liners y Sartas)..."):
        # EL SECRETO: El prompt que se le envía a la IA internamente debe ser:
        # "Analiza el PDF completo. Identifica TODAS las tablas de estado mecánico.
        # Combina la información de: Wellhead, Casing/Liner y Production String.
        # Mantén el formato: Componente, Long(ft), OD(in), MD Top(ft), Base MD(ft).
        # No omitas ningún componente por pequeño que sea."
        
        # Simulación de una extracción integral (incluyendo liners y más sarta)
        data_integral = """Componente,Long(ft),OD(in),MD Top(ft),Base MD(ft)
        TUBING HANGER 7 1/16,0.83,7.125,24.5,25.4
        TUBING 3 1/2,3337.45,3.500,25.4,3362.8
        PUP JOINT 3 1/2,7.97,3.500,3362.8,3370.8
        DRAIN VALVE,0.56,3.500,3370.8,3371.4
        LINER 7 IN,1200.00,7.000,8500.0,9700.0
        CASING 9 5/8,4500.00,9.625,0.0,4500.0
        INTAKE ESP,1.38,5.380,3448.6,3449.9
        MOTOR ESP 250HP,22.50,5.620,3465.1,3487.6
        """
        df = pd.read_csv(StringIO(data_integral))
        return df

# ==========================================
# 3. NAVEGACIÓN (SIDEBAR)
# ==========================================
with st.sidebar:
    st.markdown("<h1 style='text-align: center; color: #2E7D32;'>ECOPETROL 🦎</h1>", unsafe_allow_html=True)
    st.divider()
    if 'menu' not in st.session_state: st.session_state.menu = "Home"
    if st.button("🏠 Inicio", use_container_width=True): st.session_state.menu = "Home"
    if st.button("⚙️ Mantenimiento / Cambio BES", use_container_width=True): st.session_state.menu = "BES"

# ==========================================
# 4. MÓDULO BES - EXTRACCIÓN MASIVA
# ==========================================
if st.session_state.menu == "BES":
    st.title("⚙️ Módulo BES: Extracción Integral")
    
    with st.container(border=True):
        st.subheader("📂 Carga de Documento Maestro")
        st.write("Suba el PDF completo del pozo para una extracción total de componentes.")
        
        uploaded_file = st.file_uploader("PDF del Estado Mecánico", type=["pdf"])
        
        if uploaded_file:
            if st.button("🚀 Iniciar Extracción Total"):
                # Aquí la IA aplica el Super Prompt
                st.session_state.df_total = procesar_pdf_con_ia_total(uploaded_file)

    if 'df_total' in st.session_state:
        st.divider()
        st.header("📊 Resultado de Extracción Multisección")
        
        # Filtros para que el usuario navegue la "Extracción Total"
        tipo_vista = st.radio("Filtrar por tipo de datos:", ["Todo", "Sarta BES (Producción)", "Revestimiento (Liner/Casing)"], horizontal=True)
        
        df_display = st.session_state.df_total
        
        if tipo_vista == "Sarta BES (Producción)":
            df_display = df_display[df_display['Componente'].str.contains('TUBING|PUP|ESP|MOTOR|INTAKE|VALVE', case=False)]
        elif tipo_vista == "Revestimiento (Liner/Casing)":
            df_display = df_display[df_display['Componente'].str.contains('LINER|CASING', case=False)]
            
        st.dataframe(df_display, use_container_width=True)
        
        st.success(f"Se han recuperado {len(df_display)} componentes del pozo.")
        
        if st.button("✅ Confirmar Datos para Diseño"):
            st.balloons()
            st.write("Datos guardados en el sistema de diseño.")

else:
    st.title("Well Planning Hub")
    st.info("Seleccione el módulo BES para probar la extracción total.")
