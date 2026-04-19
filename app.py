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
# 1. MOTOR DE EXTRACCIÓN CON MEJORA VISUAL (OPENCV)
# ==========================================

@st.cache_resource
def load_ocr_model():
    # Cargamos el modelo en memoria una sola vez
    return easyocr.Reader(['es', 'en'], gpu=False)

def preprocess_image(imagen_pil):
    """Optimiza la imagen para que el OCR detecte mejor los caracteres pequeños."""
    # Convertir PIL a formato OpenCV (BGR)
    img = np.array(imagen_pil.convert('RGB'))
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    
    # 1. Escala de grises
    gris = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 2. Reescalado (Upscaling x2)
    # EasyOCR funciona mucho mejor con caracteres de mayor tamaño
    alto, ancho = gris.shape
    gris = cv2.resize(gris, (ancho * 2, alto * 2), interpolation=cv2.INTER_CUBIC)
    
    # 3. Binarización Adaptativa
    # Convierte a blanco y negro puro para resaltar los números
    binaria = cv2.adaptiveThreshold(
        gris, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )
    
    return binaria

def skill_extract_tabular_data(imagen_pil):
    try:
        reader = load_ocr_model()
        
        # --- Preprocesamiento ---
        img_pre = preprocess_image(imagen_pil)
        ancho_total = img_pre.shape[1]
        
        # Lectura con OCR
        results = reader.readtext(img_pre, detail=1)
        if not results:
            return None

        # --- Lógica de Agrupamiento por Filas ---
        filas_dict = {}
        tolerancia_y = 25  # Aumentada por el reescalado x2

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
        
        for y in sorted(filas_dict.keys()):
            elementos = sorted(filas_dict[y], key=lambda x: x[0])
            c_long, c_od, c_desc, c_top, c_base = [], [], [], [], []

            for x, txt in elementos:
                pct_x = x / ancho_total
                
                # Clasificación por columnas (ajustada para imagen preprocesada)
                if pct_x < 0.10: c_long.append(txt)
                elif 0.10 <= pct_x < 0.18: 
                    if any(c.isdigit() for c in txt): c_od.append(txt)
                    else: c_desc.append(txt)
                elif 0.18 <= pct_x < 0.72: c_desc.append(txt)
                elif 0.72 <= pct_x < 0.86: c_top.append(txt)
                else: c_base.append(txt)

            desc_raw = " ".join(c_desc).strip()
            od_raw = "".join(c_od).strip()
            top_raw = "".join(c_top).strip()
            base_raw = "".join(c_base).strip()

            # --- DIVISIÓN INTELIGENTE DE PROFUNDIDADES ---
            # Si el Top detectado tiene múltiples puntos (ej: 3.402.13.402.6)
            total_profundidad = top_raw + base_raw
            puntos = [m.start() for m in re.finditer(r'\.', total_profundidad)]
            
            if len(puntos) >= 2:
                # Caso crítico: OCR pegó las dos columnas
                # Dividimos por el punto medio de los decimales
                punto_corte = puntos[len(puntos)//2]
                top_raw = total_profundidad[:punto_corte+2]
                base_raw = total_profundidad[punto_corte+2:]

            # --- RESCATE DE OD ---
            if not od_raw and desc_raw:
                match_od = re.match(r'^(\d+[\.,]\d{2,3})[\s|]*(.*)', desc_raw)
                if match_od:
                    od_raw = match_od.group(1)
                    desc_raw = match_od.group(2)

            # --- FILTRADO DE FILAS VÁLIDAS ---
            if len(desc_raw) > 3 and not any(p in desc_raw for p in ["Descripción", "Componente", "MD"]):
                
                def clean_val(v):
                    # Limpia caracteres extraños pero mantiene el punto decimal
                    v = re.sub(r'[^0-9.]', '', v.replace(",", "."))
                    # Evita múltiples puntos por errores de OCR
                    parts = v.split('.')
                    return f"{parts[0]}.{parts[1]}" if len(parts) > 1 else v

                datos_tabla.append({
                    "Long(ft)": clean_val("".join(c_long)),
                    "OD(in)": clean_val(od_raw),
                    "Descripción del Componente": desc_raw.lstrip('| ').strip(),
                    "MD Top(ft)": clean_val(top_raw),
                    "Base MD(ft)": clean_val(base_raw)
                })

        return pd.DataFrame(datos_tabla)
            
    except Exception as e:
        st.error(f"Error en el motor: {str(e)}")
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
    st.info("Extracción optimizada con preprocesamiento OpenCV.")
    
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
            st.image(img_to_process, width=800, caption="Imagen cargada")
            if st.button(f"🚀 Extraer Tabla", key=f"b_{key_suffix}"):
                with st.status("Procesando imagen con OpenCV...") as s:
                    df = skill_extract_tabular_data(img_to_process)
                    s.update(label="Extracción finalizada", state="complete")
                
                if df is not None and not df.empty:
                    st.success("**Resultados de la extracción:**")
                    st.dataframe(df, use_container_width=True)
                    csv = df.to_csv(index=False).encode('utf-8')
                    st.download_button("📥 Descargar CSV", csv, f"{label_id}.csv", "text/csv")
                else:
                    st.error("No se detectaron datos legibles. Intenta un recorte más cercano.")

    with tab1: procesar_seccion("Cabezal", "head")
    with tab2: procesar_seccion("Liner", "liner")
    with tab3: procesar_seccion("Sarta", "sarta")

else:
    st.title(f"Módulo {st.session_state.menu}")
    st.warning("Sección en desarrollo.")
