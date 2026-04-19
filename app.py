import streamlit as st
import easyocr
from PIL import Image
import numpy as np
import pandas as pd
import re
import io
from streamlit_paste_button import paste_image_button

# ==========================================
# 1. MOTOR DE EXTRACCIÓN OPTIMIZADO (ZONIFICACIÓN + RESCATE + DIVISIÓN)
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
        tolerancia_y = 14  

        for res in results:
            box, texto, conf = res
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
        
        # Procesamos cada fila detectada
        for y in sorted(filas_dict.keys()):
            elementos = sorted(filas_dict[y], key=lambda x: x[0])
            
            c_long, c_od, c_desc, c_top, c_base = [], [], [], [], []

            for x, txt in elementos:
                pct_x = x / ancho_total
                
                # --- Clasificación por Eje X (Ajustado para evitar solapamiento) ---
                if pct_x < 0.08:           # Zona: Long(ft)
                    c_long.append(txt)
                elif 0.08 <= pct_x < 0.16: # Zona: OD(in)
                    if any(char.isdigit() for char in txt): c_od.append(txt)
                    else: c_desc.append(txt)
                elif 0.16 <= pct_x < 0.70: # Zona Central: Descripción (Se reduce para proteger Top/Base)
                    c_desc.append(txt)
                elif 0.70 <= pct_x < 0.88: # Zona: MD Top
                    c_top.append(txt)
                else:                      # Zona Derecha: MD Base
                    c_base.append(txt)

            desc_raw = " ".join(c_desc).strip()
            od_raw = "".join(c_od).strip()
            top_raw = "".join(c_top).strip()
            base_raw = "".join(c_base).strip()

            # --- ESTRATEGIA 1: Rescate de OD (in) desde la descripción ---
            if not od_raw and desc_raw:
                match_od = re.match(r'^(\d+[\.,]\d{2,3})[\s|]*(.*)', desc_raw)
                if match_od:
                    od_raw = match_od.group(1)
                    desc_raw = match_od.group(2)

            # --- ESTRATEGIA 2: División de MD Top y Base MD pegados ---
            # Si MD Top parece contener dos números o MD Base está vacío
            if not base_raw and top_raw:
                # Busca patrones de números decimales (ej: 25.43362. o 3.362.83.370.8)
                parts = re.findall(r'\d+\.\d+|\d+\.', top_raw)
                if len(parts) >= 2:
                    top_raw = parts[0]
                    base_raw = parts[1]

            # Filtro de Calidad: Ignorar encabezados y basura
            if len(desc_raw) > 3 and not any(p in desc_raw for p in ["Descripción", "Componente", "PROD", "Long"]):
                
                def clean_numeric(val):
                    # Limpieza total: solo números y un solo punto decimal
                    raw = re.sub(r'[^0-9.]', '', val.replace(",", "."))
                    return raw

                linea_data = {
                    "Long(ft)": clean_numeric("".join(c_long)),
                    "OD(in)": clean_numeric(od_raw),
                    "Descripción del Componente": desc_raw.lstrip('| ').strip(),
                    "MD Top(ft)": clean_numeric(top_raw),
                    "Base MD(ft)": clean_numeric(base_raw)
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
            st.write(f"O pega el recorte:")
            pasted = paste_image_button(label=f"📋 Clic y Ctrl+V", key=f"p_{key_suffix}")
            if pasted.image_data: img_to_process = pasted.image_data

        if img_to_process:
            st.image(img_to_process, width=800, caption="Recorte a procesar")
            if st.button(f"🚀 Extraer Tabla", key=f"b_{key_suffix}"):
                with st.status("Analizando geometría de la tabla...") as s:
                    df = skill_extract_tabular_data(img_to_process)
                    s.update(label="Análisis completado", state="complete")
                
                if df is not None and not df.empty:
                    st.success("**Datos organizados:**")
                    st.dataframe(df, use_container_width=True)
                    
                    csv = df.to_csv(index=False).encode('utf-8')
                    st.download_button("📥 Descargar Tabla (CSV)", csv, f"{label_id}.csv", "text/csv")
                else:
                    st.error("No se detectaron datos. Intenta un recorte más nítido.")

    with tab1: procesar_seccion("Cabezal", "head")
    with tab2: procesar_seccion("Liner", "liner")
    with tab3: procesar_seccion("Sarta", "sarta")

else:
    st.title(f"Módulo {st.session_state.menu}")
    st.warning("Sección en desarrollo técnico.")
