import streamlit as st
import pandas as pd
from io import StringIO
import re

# ==========================================
# CONFIGURACIÓN DE PÁGINA Y ESTILO
# ==========================================
st.set_page_config(page_title="Well Planning Hub - CUA", page_icon="🦎", layout="wide")

# Inyectar CSS para un look más profesional (Ecopetrol colors)
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #2E7D32; color: white; }
    .stTextArea>div>div>textarea { font-family: monospace; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# MOTOR DE PROCESAMIENTO INTERNO (POST-COPILOT)
# ==========================================

def smart_data_classifier(df):
    """
    Toma la tabla masiva de Copilot y la divide automáticamente 
    en las secciones del pozo basado en palabras clave.
    """
    secciones = {
        "Cabezal": pd.DataFrame(),
        "Liner": pd.DataFrame(),
        "Sarta": pd.DataFrame()
    }
    
    # Lógica de clasificación basada en la descripción del componente
    if not df.empty:
        # Ejemplo: Filtrar por OD o nombres comunes
        secciones["Sarta"] = df[df['Descripción del Componente'].str.contains('TUBING|PUP JOINT|ESP|INTAKE|SENSOR', case=False, na=False)]
        secciones["Liner"] = df[df['Descripción del Componente'].str.contains('LINER|CASING|HOLE', case=False, na=False)]
        secciones["Cabezal"] = df[df['Descripción del Componente'].str.contains('HANGER|WELLHEAD|FLANGE', case=False, na=False)]
        
    return secciones

# ==========================================
# INTERFAZ UNIFICADA
# ==========================================

with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/f/f6/Ecopetrol_logo.svg", width=150) # Logo placeholder
    st.title("Well Planning Hub")
    st.divider()
    menu = st.radio("Seleccione Módulo:", ["🏗️ Estado Mecánico Unificado", "🌑 Abandonos", "📊 Rediseño SLA", "🛠️ Workover"])

if menu == "🏗️ Estado Mecánico Unificado":
    st.title("🚀 Carga Masiva de Estado Mecánico (vía Copilot)")
    
    # --- GUÍA PARA EL USUARIO ---
    with st.expander("💡 ¿Cómo usar Copilot para esta extracción? (Haz clic aquí)"):
        st.markdown("""
        1. Abre **Microsoft Copilot** en tu navegador o Teams.
        2. Sube el PDF del pozo.
        3. Escribe este prompt: 
           > *"Extrae todas las tablas del estado mecánico (Cabezal, Liner y Sarta de Producción). Entrégame los datos en un formato de tabla limpia con estas columnas: Long(ft), OD(in), Descripción del Componente, MD Top(ft), Base MD(ft)."*
        4. Copia la tabla resultante y pégala abajo.
        """)

    # --- ÁREA DE ENTRADA ---
    col_input, col_preview = st.columns([1, 1])
    
    with col_input:
        st.subheader("📥 Entrada de Datos")
        raw_data = st.text_area("Pega aquí la tabla generada por Copilot:", height=400, placeholder="Pega los datos aquí...")
        
        btn_procesar = st.button("⚡ Procesar Estado Mecánico Completo")

    with col_preview:
        st.subheader("📋 Validación de Datos")
        if btn_procesar and raw_data:
            try:
                # Convertir el texto pegado en DataFrame (maneja tabs de Excel/Copilot o comas)
                df_input = pd.read_csv(StringIO(raw_data.replace('\t', ',')), sep=None, engine='python')
                
                # Almacenar en session_state
                st.session_state.master_df = df_input
                st.success(f"Se detectaron {len(df_input)} componentes correctamente.")
                st.dataframe(df_input, use_container_width=True)
            except Exception as e:
                st.error("Error al leer el formato. Asegúrate de copiar la tabla completa desde Copilot.")

    # --- SECCIÓN DE RESULTADOS CLASIFICADOS ---
    if 'master_df' in st.session_state:
        st.divider()
        st.header("🔍 Desglose por Secciones")
        
        datos_divididos = smart_data_classifier(st.session_state.master_df)
        
        tab_sarta, tab_liner, tab_cabezal = st.tabs(["🔌 Production String", "🕳️ Liner", "🏗️ Cabezal"])
        
        with tab_sarta:
            st.dataframe(datos_divididos["Sarta"], use_container_width=True)
            if not datos_divididos["Sarta"].empty:
                st.download_button("📥 Descargar Sarta CSV", datos_divididos["Sarta"].to_csv(index=False), "sarta.csv")
                
        with tab_liner:
            st.dataframe(datos_divididos["Liner"], use_container_width=True)
            
        with tab_cabezal:
            st.dataframe(datos_divididos["Cabezal"], use_container_width=True)

# --- OTROS MÓDULOS ---
else:
    st.title(menu)
    st.info("Módulo conectado al flujo de datos unificado. Pendiente de configuración de ingeniería.")
