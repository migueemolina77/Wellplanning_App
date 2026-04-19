import streamlit as st
import easyocr
from PIL import Image
import numpy as np
import pandas as pd
import re
import cv2
import io
from streamlit_paste_button import paste_image_button

# ==========================================
# 1. MOTOR DE EXTRACCIÓN ULTRA-PRECISO
# ==========================================

@st.cache_resource
def load_ocr_model():
    return easyocr.Reader(['es', 'en'], gpu=False)

def preprocess_image(imagen_pil):
    """
    Usa OpenCV para mejorar el enfoque. Esto ayuda a que el OCR vea 
    los puntos decimales y no deje casillas vacías.
    """
    img = np.array(imagen_pil.convert('RGB'))
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    gris = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Aumentamos el tamaño para detectar mejor números pequeños
    alto, ancho = gris.shape
    img_res = cv2.resize(gris, (ancho * 2, alto * 2), interpolation=cv2.INTER_LANCZOS4)
    
    # Binarización para limpiar el ruido del fondo
    binaria = cv2.adaptiveThreshold(
        img_res, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )
    return binaria

def skill_extract_tabular_data(imagen_pil):
    try:
        reader = load_ocr_model()
        
        # --- PREPROCESAMIENTO ---
        img_pre = preprocess_image(imagen_pil)
        ancho_total = img_pre.shape[1]
        
        # Obtenemos resultados
        results = reader.readtext(img_pre, detail=1)
        if not results:
            return None

        # --- Lógica de Agrupamiento por Filas (Eje Y) ---
        filas_dict = {}
        tolerancia_y = 20  # Ajustada por el escalado x2

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
                
                # --- Clasificación por Eje X REFINADA ---
                if pct_x < 0.08:           # Zona: Long(ft)
                    c_long.append(txt)
                elif 0.08 <= pct_x < 0.15: # Zona: OD(in)
                    if any(char.isdigit() for char in txt): c_od.append(txt)
                    else: c_desc.append(txt)
                elif 0.15 <= pct_x < 0.72: # Zona Central: Descripción
                    c_desc.append(txt)
                elif 0.72 <= pct_x < 0.86: # Zona: MD Top
                    c_top.append(txt)
                else:                      # Zona Derecha: MD Base
                    c_base.append(txt)

            desc_raw = " ".join(c_desc).strip()
            
            def clean_numeric(val_list):
                v = "".join(val_list).replace(",", ".")
                # Mantenemos solo números y puntos
                return re.sub(r'[^0-9.]', '', v)

            long_raw = clean_numeric(c_long)
            od_raw = clean_numeric(c_od)
            top_raw = clean_numeric(c_top)
            base_raw = clean_numeric(c_base)

            # --- RESCATE 1: Si OD está en la descripción ---
            if not od_raw and desc_raw:
                match_od = re.match(r'^(\d+[\.,]\d{2,3})[\s|]*(.*)', desc_raw)
                if match_od:
                    od_raw = clean_numeric([match_od.group(1)])
                    desc_raw = match_od.group(2)

            # --- RESCATE 2: Si Top y Base están pegados (Detección de doble decimal) ---
            if top_raw and not base_raw:
                # Busca si hay dos números con punto decimal pegados
                parts = re.findall(r'\d+\.\d+|\d+', top_raw)
                if len(parts) >= 2:
                    top_raw = parts[0]
                    base_raw = parts[1]

            # Filtro de Calidad: Ignorar encabezados
            if len(desc_raw) > 3 and not any(p in desc_raw for p in ["Descripción", "Componente", "MD", "PROD"]):
                datos_tabla.append({
                    "Long(ft)": long_raw,
                    "OD(in)": od_raw,
                    "Descripción del Componente": desc_raw.lstrip('|/ ').strip(),
                    "MD Top(ft)": top_raw,
                    "Base MD(ft)": base_raw
                })

        df = pd.DataFrame(datos_tabla)

        # --- LÓGICA DE CONTINUIDAD (RELLENO DE CASILLAS VACÍAS) ---
        # En Well Planning: Base(fila n) = Top(fila n+1). 
        # Si el OCR perdió una base, la calculamos por lógica.
        for i in range(len(df) - 1):
            if not df.loc[i, "Base MD(ft)"] or df.loc[i, "Base MD(ft)"] == "":
                df.loc[i, "Base MD(ft)"] = df.loc[i+1, "MD Top(ft)"]

        return df
            
    except Exception as e:
        st.error(f"Error técnico: {str(e)}")
        return None

# ==========================================
# 2. INTERFAZ DE USUARIO (Se mantiene tu estilo)
# ==========================================
st.set_page_config(page_title="Well Planning CUA", page_icon="🏗️", layout="wide")

if 'menu' not in st.session_state:
    st.session_state.menu = "Home"

with st.sidebar:
    st.markdown("<h1 style='text-align: center; color: #2E7D32;'>ECOPETROL 🦎</h1>", unsafe_allow_html=True)
    if st.button("🏠 Inicio", use_container_width=True):
        st.session_state.menu = "Home"
        st.rerun()

if st.session_state.menu == "Home":
    st.title("🚧 Construcción Well Plan - Operaciones CUA")
    st.info("Sistema de extracción de estados mecánicos optimizado.")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⚙️ Mantenimiento BES", use_container_width=True): st.session_state.menu = "BES"
    with col2:
        if st.button("🛠️ Workover", use_container_width=True): st.session_state.menu = "Workover"

elif st.session_state.menu == "BES":
    st.title("⚙️ Módulo de Extracción BES")
    
    pasted = paste_image_button(label="📋 Pegar aquí recorte de la tabla", key="paster")
    
    if pasted.image_data:
        st.image(pasted.image_data, caption="Imagen cargada", width=800)
        if st.button("🚀 Extraer Información"):
            with st.status("Aplicando visión artificial y lógica de pozo...") as s:
                df = skill_extract_tabular_data(pasted.image_data)
                s.update(label="¡Extracción completa!", state="complete")
            
            if df is not None and not df.empty:
                st.success("**Tabla Extraída con Éxito:**")
                st.dataframe(df, use_container_width=True)
                
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Descargar Tabla (CSV)", csv, "estado_mecanico.csv", "text/csv")
            else:
                st.error("No se detectaron datos. Asegúrate de que el recorte incluya los números de profundidad.")
