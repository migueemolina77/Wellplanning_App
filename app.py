import streamlit as st
import pandas as pd
from io import StringIO

# ==========================================
# 1. MOTOR DE EXTRACCIÓN DETALLADA (PROTOTIPO)
# ==========================================
def motor_extraccion_ecopetrol(archivo):
    """
    Simula la extracción siguiendo el orden exacto del documento Rubiales 2218H.
    """
    with st.spinner("🧠 Analizando estructura: Header -> Casings -> Liner -> Prod String"):
        
        # 1. Info del Pozo (Header)
        info_pozo = {
            "Pozo": "RUBIALES 2218H",
            "Prof Final MD": "3,923.0 ft",
            "TVD": "2,548.9 ft",
            "Mesa Rotaria": "538.9 ft"
        }

        # 2. Bloque: PRODUCTION STRING + ESP (El que más te importa)
        # Extraído de la última tabla de la imagen image_c0f0c3.png
        data_prod = """Componente,Long(ft),OD(in),Top MD(ft),Base MD(ft)
        TUBING HANGER FMC TC-B-EC,0.92,7.060,20.5,21.4
        TUBING 3 1/2 9.3# N-80,31.47,3.500,21.4,52.9
        CROSSOVER 3 1/2 x 4 1/2,1.61,4.500,52.9,54.5
        TUBING 4-1/2 11.6# N-80,2189.95,4.500,54.5,2244.4
        CHECK VALVE POPPET TYPE,0.57,3.500,2326.2,2326.8
        HEAD DISCHARGE ESP,0.58,5.380,2358.1,2358.7
        PUMP LOWER ESP B 538,17.35,5.380,2371.9,2389.3
        MOTOR PMM ESP 300 HP,12.92,5.620,2405.8,2418.8
        """
        
        # 3. Bloque: CASINGS & LINERS
        data_casing = """Sección,Item,OD(in),Top Set(ft),MD Base(ft)
        Conductor,CASING 20 IN 94#,20.000,0.0,22.5
        Surface,CASING 9 5/8 K55 36#,9.625,22.5,450.0
        Intermediate,CSG 7 23# P-110,7.000,225.0,4496.0
        Production Liner,LINER RANURADO 4 1/2,4.500,4514.1,5487.9
        """

        return info_pozo, pd.read_csv(StringIO(data_prod)), pd.read_csv(StringIO(data_casing))

# ==========================================
# 2. INTERFAZ DE USUARIO (STREMLIT)
# ==========================================
st.title("🏗️ Well Planning Hub: Extractor Rubiales")

if 'menu' not in st.session_state: st.session_state.menu = "BES"

# Módulo BES
if st.session_state.menu == "BES":
    with st.container(border=True):
        uploaded_file = st.file_uploader("Subir Estado Mecánico (Esquemático)", type=["pdf", "png", "jpg"])
        
        if uploaded_file:
            if st.button("🔍 Ejecutar Análisis por Secciones"):
                header, df_prod, df_casing = motor_extraccion_ecopetrol(uploaded_file)
                st.session_state.header = header
                st.session_state.df_prod = df_prod
                st.session_state.df_casing = df_casing

    # DESPLIEGE DE INFORMACIÓN ORDENADA
    if 'header' in st.session_state:
        # Fila 1: Encabezado del Pozo
        st.subheader(f"📍 Información General: {st.session_state.header['Pozo']}")
        cols = st.columns(3)
        cols[0].metric("Profundidad MD", st.session_state.header['Prof Final MD'])
        cols[1].metric("TVD", st.session_state.header['TVD'])
        cols[2].metric("Mesa Rotaria", st.session_state.header['Mesa Rotaria'])

        # Fila 2: Pestañas para no saturar la pantalla
        tab1, tab2, tab3 = st.tabs(["🚀 Production String + ESP", "🛡️ Casings & Liners", "🎯 Intervalos"])

        with tab1:
            st.markdown("### Tabla Maestra de Completamiento (BES)")
            st.dataframe(st.session_state.df_prod, use_container_width=True)
            st.info("💡 Esta información alimentará automáticamente el cálculo de sarta.")

        with tab2:
            st.markdown("### Arquitectura del Pozo")
            st.table(st.session_state.df_casing)

        with tab3:
            st.write("Datos de intervalos cañoneados detectados en la base del documento.")
            st.caption("Intervalos: Areniscas Basales Zona 1, 2 y 3.")
