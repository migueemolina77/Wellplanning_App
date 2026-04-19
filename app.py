import streamlit as st
import easyocr
from PIL import Image
import numpy as np
import pandas as pd
import re
import io
from streamlit_paste_button import paste_image_button

# ==========================================
# 1. MOTOR DE EXTRACCIÓN CON ZONIFICACIÓN X
# ==========================================

@st.cache_resource
def load_ocr_model():
    # Cargamos el modelo en memoria una sola vez
    return easyocr.Reader(['es', 'en'], gpu=False)

def skill_extract_tabular_data(imagen_pil):
    try:
        reader = load_ocr_model()
        img_array = np.array(imagen_pil.convert('RGB'))
        ancho_total = img_array.shape[1]
        
        # Obtenemos resultados con coordenadas detalladas
        results = reader.readtext(img_array, detail=1)
        if not results:
            return None

        # --- Lógica de Agrupamiento por Filas (Eje Y) ---
        filas_dict = {}
        tolerancia_y = 12  # Sensibilidad para agrupar texto en la misma línea

        for res in results:
            box, texto, conf = res
            # Calculamos el centro geométrico del bloque de texto
            centro_y = (box[0][1] + box[2][1]) / 2
            centro_x = (box[0][0] + box[1][0]) / 2
            
            encontrado = False
            for y_ref in filas_dict.keys():
                if abs(centro_y - y_ref) < tolerancia_y:
                    filas_dict[y_ref].append((centro_x, texto))
                    encontrado = True
                    break
            if not encontrado:
                filas_dict[centro_y] = [(centro_x, texto)]

        datos_tabla = []
        
        # Procesamos cada fila detectada de arriba hacia abajo
        for y in sorted(filas_dict.keys()):
            # Ordenamos los elementos de la fila de izquierda a derecha
            elementos = sorted(filas_dict[y], key=lambda x: x[0])
            
            # --- Clasificación por Zonas (Eje X) ---
            # Basado en la estructura estándar de reportes de Ecopetrol
            col_long = []
            col_od = []
            col_desc = []
            col_top = []
            col_base = []

            for x, txt in elementos:
                pct_x = x / ancho_total
                
                if pct_x < 0.09:        # Zona Izquierda: Long(ft)
                    col_long.append(txt)
                elif pct_x < 0.16:      # Zona: OD(in)
                    col_od.append(txt)
                elif pct_x < 0.78:      # Zona Central: Descripción
                    col_desc.append(txt)
                elif pct_x < 0.89:      # Zona: MD Top
                    col_top.append(txt)
                else:                   # Zona Derecha: MD Base
                    col_base.append(txt)

            # Limpiamos y unimos los fragmentos
            desc_final = " ".join(col_desc).strip()
            
            # Filtro: Ignorar filas vacías o que sean solo encabezados
            if desc_final and not any(palabra in desc_final for palabra in ["Descripción", "Componente", "PROD"]):
                linea_data = {
                    "Long(ft)": " ".join(col_long).strip(),
                    "OD(in)": " ".join(col_od).strip(),
                    "Descripción del Componente": desc_final,
                    "MD Top(ft)": " ".join(col_top).strip(),
                    "Base MD(ft)": " ".join(col_base).strip()
                }
                datos_tabla.append(linea_data)

        return pd.DataFrame(datos_tabla)
            
    except Exception as e:
        st.error(f"Error en el procesamiento: {str(e)}")
        return None

# ==========================================
# 2. INTERFAZ DE USUARIO (STREAMLIT)
# ==========================================
st.set_page_config(page_title="Well Planning - Operaciones CUA", page_icon="🏗️", layout="wide")

if 'menu' not in st.session_state:
    st.session_state.menu = "Home"

with st.sidebar:
    st.markdown("<h1 style='text-align: center; color: #2E7D32;'>ECOPETROL 🦎</h1>", unsafe_allow_html=True)
    st.info("Modo: Análisis Geométrico de Tablas")
    st.divider()
    if st.button("🏠 Inicio", use_container_width=True):
        st.session_state.menu = "Home"
        st.rerun()

if st.session_state.menu == "Home":
    st.title("🚧 Construcción Well Plan - Operaciones CUA")
    st.info("Extracción optimizada de Estados Mecánicos mediante zonificación X-Y.")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🌑 1. Abandonos", use_container_width=True): st.session_state.menu = "Abandonos"
        if st.button("⚙️ 2. Mantenimiento BES", use_container_width=True): st.session_state.menu = "BES"
    with col2:
        if st.button("📊 3. Rediseño SLA", use_container_width=True): st.session_state.menu = "SLA"
        if st.button("🛠️ 4. Workover", use_container_width=True): st.session_state.menu = "Workover"

elif st.session_state.menu == "BES":
    st.title("⚙️ Módulo de Extracción BES")
    tab1, tab2, tab3 = st.tabs(["🏗️ Cabezal", "🕳️ Liner", "🔌 Sarta"])
    
    def procesar_seccion(label_id, key_suffix):
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
            st.image(img_to_process, width=800, caption="Recorte a procesar")
            if st.button(f"🚀 Extraer Tabla de {label_id}", key=f"b_{key_suffix}"):
                with st.status("Analizando geometría de la tabla...") as s:
                    df = skill_extract_tabular_data(img_to_process)
                    s.update(label="Análisis completado", state="complete")
                
                if df is not None and not df.empty:
                    st.success("**Datos organizados por columnas:**")
                    st.dataframe(df, use_container_width=True)
                    
                    csv = df.to_csv(index=False).encode('utf-8')
                    st.download_button("📥 Descargar Tabla (CSV)", csv, f"{label_id}.csv", "text/csv")
                else:
                    st.error("No se detectaron datos tabulares. Intenta un recorte más nítido.")

    with tab1: procesar_seccion("Cabezal", "head")
    with tab2: procesar_seccion("Liner", "liner")
    with tab3: procesar_seccion("Sarta", "sarta")

else:
    st.title(f"Módulo {st.session_state.menu}")
    st.warning("Sección en desarrollo técnico.")
