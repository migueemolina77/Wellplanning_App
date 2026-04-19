import streamlit as st
import easyocr
from PIL import Image
import numpy as np
import pandas as pd
import re
import io
from streamlit_paste_button import paste_image_button

# ==========================================
# 1. MOTOR DE EXTRACCIÓN LOCAL Y LÓGICA TABULAR
# ==========================================

@st.cache_resource
def load_ocr_model():
    return easyocr.Reader(['es', 'en'], gpu=False)

def skill_extract_tabular_data(imagen_pil):
    try:
        reader = load_ocr_model()
        img_array = np.array(imagen_pil.convert('RGB'))
        
        # Obtenemos resultados con coordenadas (detail=1)
        results = reader.readtext(img_array, detail=1)
        
        if not results:
            return None

        # --- Lógica de Agrupamiento por Filas (Eje Y) ---
        # Tolerancia de píxeles para considerar que texto está en la misma fila
        tolerancia_y = 15 
        filas = []
        
        # Ordenamos por la posición Y (arriba hacia abajo)
        results.sort(key=lambda x: x[0][0][1])
        
        if results:
            fila_actual = []
            y_referencia = results[0][0][0][1]
            
            for res in results:
                pos_y = res[0][0][1]
                texto = res[1]
                
                if abs(pos_y - y_referencia) <= tolerancia_y:
                    fila_actual.append(texto)
                else:
                    filas.append(fila_actual)
                    fila_actual = [texto]
                    y_referencia = pos_y
            filas.append(fila_actual) # Añadir la última fila

        # Limpiamos y estructuramos las filas detectadas
        datos_limpios = []
        for f in filas:
            texto_fila = " ".join(f)
            # Buscamos números (Long, OD, Tops)
            nums = re.findall(r'[-+]?\d*[.,]\d+|\d+', texto_fila)
            # Intentamos rescatar la descripción (texto largo)
            desc = re.sub(r'\d+[.,]\d+', '', texto_fila).strip()
            
            if len(nums) >= 2:
                datos_limpios.append({
                    "Long(ft)": nums[0] if len(nums) > 0 else "",
                    "OD(in)": nums[1] if len(nums) > 1 else "",
                    "Descripción del Componente": desc,
                    "MD Top": nums[-2] if len(nums) > 3 else "",
                    "MD Base": nums[-1] if len(nums) > 2 else ""
                })
        
        return pd.DataFrame(datos_limpios)
            
    except Exception as e:
        st.error(f"Error en OCR: {str(e)}")
        return None

# ==========================================
# 2. INTERFAZ DE USUARIO (STREAMLIT)
# ==========================================
st.set_page_config(page_title="Well Planning - Operaciones CUA", page_icon="🏗️", layout="wide")

if 'menu' not in st.session_state:
    st.session_state.menu = "Home"

# Sidebar
with st.sidebar:
    st.markdown("<h1 style='text-align: center; color: #2E7D32;'>ECOPETROL 🦎</h1>", unsafe_allow_html=True)
    st.info("Modo: Extracción Tabular Local")
    st.divider()
    if st.button("🏠 Inicio", use_container_width=True):
        st.session_state.menu = "Home"
        st.rerun()

# --- Pantalla Principal ---
if st.session_state.menu == "Home":
    st.title("🚧 Construcción Well Plan - Operaciones CUA")
    st.info("Plataforma optimizada para lectura de Tablas de Estado Mecánico.")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🌑 1. Abandonos", use_container_width=True): st.session_state.menu = "Abandonos"
        if st.button("⚙️ 2. Mantenimiento BES", use_container_width=True): st.session_state.menu = "BES"
    with col2:
        if st.button("📊 3. Rediseño SLA", use_container_width=True): st.session_state.menu = "SLA"
        if st.button("🛠️ 4. Workover", use_container_width=True): st.session_state.menu = "Workover"

# --- Módulo BES ---
elif st.session_state.menu == "BES":
    st.title("⚙️ Módulo de Extracción BES")
    tab1, tab2, tab3 = st.tabs(["🏗️ Cabezal", "🕳️ Liner", "🔌 Sarta"])
    
    def procesar_captura_tabular(label_id, key_suffix):
        col_u, col_p = st.columns(2)
        img_to_process = None
        
        with col_u:
            archivo = st.file_uploader(f"Cargar {label_id}", type=["jpg", "png", "jpeg"], key=f"u_{key_suffix}")
            if archivo: img_to_process = Image.open(archivo)
        with col_p:
            st.write(f"O pega el recorte de {label_id}:")
            pasted = paste_image_button(label=f"📋 Clic y Ctrl+V ({label_id})", key=f"p_{key_suffix}")
            if pasted.image_data: img_to_process = pasted.image_data

        if img_to_process:
            st.image(img_to_process, width=600, caption="Imagen para análisis")
            if st.button(f"🚀 Extraer Tabla de {label_id}", key=f"b_{key_suffix}"):
                with st.status("Agrupando filas y detectando columnas...") as s:
                    df = skill_extract_tabular_data(img_to_process)
                    s.update(label="Análisis finalizado", state="complete")
                
                if df is not None and not df.empty:
                    st.success(f"**Componentes Detectados:**")
                    st.dataframe(df, use_container_width=True)
                    
                    # Botón de descarga para Excel/CSV
                    csv = df.to_csv(index=False).encode('utf-8')
                    st.download_button("📥 Descargar Tabla", csv, f"{label_id}.csv", "text/csv")
                else:
                    st.warning("No se pudo tabular la información. Verifica que el recorte incluya los números de las columnas.")

    with tab1:
        st.subheader("Análisis de Cabezal (Sección B)")
        procesar_captura_tabular("Cabezal", "head")
    with tab2:
        st.subheader("Análisis de Revestimiento")
        procesar_captura_tabular("Liner", "liner")
    with tab3:
        st.subheader("Análisis de Sarta y Bomba")
        procesar_captura_tabular("Sarta", "sarta")

else:
    st.title(f"Módulo {st.session_state.menu}")
    st.warning("Sección en desarrollo.")
