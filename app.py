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
# 1. MOTOR DE IA: LIMPIEZA RADICAL + REGEX
# ==========================================

@st.cache_resource
def load_ocr_model():
    # Cargamos solo 'en' para maximizar precisión en números
    return easyocr.Reader(['en'], gpu=False)

def preprocess_radical(imagen_pil):
    """
    Elimina líneas de tablas y resalta el texto para evitar confusiones.
    """
    img = np.array(imagen_pil.convert('RGB'))
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    
    # Aumentar tamaño para mejorar lectura de decimales
    img = cv2.resize(img, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
    
    gris = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Umbralización adaptativa inversa (Texto blanco sobre fondo negro ayuda al OCR)
    thresh = cv2.adaptiveThreshold(gris, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                   cv2.THRESH_BINARY_INV, 11, 2)
    
    # Eliminar líneas horizontales
    h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
    remove_h = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, h_kernel, iterations=2)
    thresh = cv2.subtract(thresh, remove_h)
    
    # Eliminar líneas verticales
    v_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
    remove_v = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, v_kernel, iterations=2)
    thresh = cv2.subtract(thresh, remove_v)
    
    return thresh

def heal_well_data(df):
    """Lógica de Ingeniería: Base = Top + Long"""
    for col in ["Long(ft)", "OD(in)", "MD Top(ft)", "Base MD(ft)"]:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    ods_comunes = [2.375, 2.875, 3.500, 4.500, 5.500, 7.000, 9.625]
    def fix_od(val):
        if pd.isna(val): return val
        return min(ods_comunes, key=lambda x: abs(x - val)) if any(abs(x - val) < 0.25 for x in ods_comunes) else val
    
    if "OD(in)" in df.columns:
        df["OD(in)"] = df["OD(in)"].apply(fix_od)

    for i in range(len(df)):
        if pd.isna(df.loc[i, "Base MD(ft)"]) and not pd.isna(df.loc[i, "MD Top(ft)"]) and not pd.isna(df.loc[i, "Long(ft)"]):
            df.loc[i, "Base MD(ft)"] = round(df.loc[i, "MD Top(ft)"] + df.loc[i, "Long(ft)"], 2)
        if i > 0 and pd.isna(df.loc[i, "MD Top(ft)"]) and not pd.isna(df.loc[i-1, "Base MD(ft)"]):
            df.loc[i, "MD Top(ft)"] = df.loc[i-1, "Base MD(ft)"]
    return df

def skill_extract_tabular_data(imagen_pil):
    try:
        reader = load_ocr_model()
        img_clean = preprocess_radical(imagen_pil)
        
        # Lectura de texto con la imagen sin líneas
        results = reader.readtext(img_clean, paragraph=False)
        if not results: return None

        filas_dict = {}
        tolerancia_y = 25 

        for (bbox, texto, conf) in results:
            centro_y = (bbox[0][1] + bbox[2][1]) / 2
            centro_x = (bbox[0][0] + bbox[1][0]) / 2
            
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
            # Unimos todo para aplicar Regex sobre la fila completa
            raw_line = " ".join([e[1] for e in elementos]).replace(",", ".")
            
            # Buscamos todos los números (enteros o decimales)
            nums = re.findall(r'\d+\.\d+|\d+', raw_line)
            # Buscamos la descripción (texto que no sea solo números)
            desc = " ".join([e[1] for e in elementos if not re.match(r'^\d', e[1])]).strip()

            if len(nums) >= 2 and len(desc) > 3:
                datos_tabla.append({
                    "Long(ft)": nums[0] if len(nums) > 0 else "",
                    "OD(in)": nums[1] if len(nums) > 1 else "",
                    "Descripción del Componente": desc,
                    "MD Top(ft)": nums[-2] if len(nums) >= 4 else (nums[2] if len(nums) > 2 else ""),
                    "Base MD(ft)": nums[-1] if len(nums) >= 2 else ""
                })

        df = pd.DataFrame(datos_tabla)
        if not df.empty:
            df = heal_well_data(df)
        return df
    except Exception as e:
        st.error(f"Error técnico: {str(e)}")
        return None

# ==========================================
# 2. INTERFAZ Y NAVEGACIÓN
# ==========================================
st.set_page_config(page_title="Well Planning CUA", page_icon="🏗️", layout="wide")

if 'menu' not in st.session_state:
    st.session_state.menu = "Home"

with st.sidebar:
    st.markdown("<h1 style='text-align: center; color: #2E7D32;'>ECOPETROL 🦎</h1>", unsafe_allow_html=True)
    st.divider()
    if st.button("🏠 Inicio", use_container_width=True): st.session_state.menu = "Home"
    st.markdown("### 🛠️ Operaciones")
    if st.button("🌑 1. Abandonos", use_container_width=True): st.session_state.menu = "Abandonos"
    if st.button("⚙️ 2. Mantenimiento BES", use_container_width=True): st.session_state.menu = "BES"
    if st.button("📊 3. Rediseño SLA", use_container_width=True): st.session_state.menu = "SLA"
    if st.button("🛠️ 4. Workover", use_container_width=True): st.session_state.menu = "Workover"

def render_extractor(label):
    st.subheader(f"Extracción de {label}")
    pasted = paste_image_button(label=f"📋 Pegar recorte de {label}", key=f"paste_{label}")
    
    if pasted.image_data:
        col1, col2 = st.columns([1, 1.2])
        with col1:
            st.image(pasted.image_data, caption=f"Recorte {label}", use_container_width=True)
        
        with col2:
            if st.button(f"🚀 Procesar {label}", key=f"btn_{label}"):
                with st.spinner("Limpiando imagen y extrayendo..."):
                    df = skill_extract_tabular_data(pasted.image_data)
                    if df is not None and not df.empty:
                        st.success("Extracción lista. Puedes editar antes de descargar:")
                        # EDITOR DE DATOS para corregir errores manuales rápidamente
                        df_edit = st.data_editor(df, use_container_width=True, num_rows="dynamic")
                        
                        csv = df_edit.to_csv(index=False).encode('utf-8')
                        st.download_button("📥 Descargar CSV", csv, f"{label}.csv", "text/csv")
                    else:
                        st.warning("No se detectaron datos claros. Intenta un recorte más nítido.")

if st.session_state.menu == "Home":
    st.title("🚧 Well Planning - Operaciones CUA")
    st.info("Sistema de Extracción Radical: Ahora con eliminación de líneas de tabla y editor manual integrado.")

elif st.session_state.menu == "BES":
    st.title("⚙️ Módulo: Mantenimiento BES")
    t1, t2, t3 = st.tabs(["🏗️ Cabezal", "🕳️ Liner de Producción", "🔌 Production String (Sarta)"])
    with t1: render_extractor("Cabezal")
    with t2: render_extractor("Liner")
    with t3: render_extractor("Sarta")

else:
    st.title(f"Módulo {st.session_state.menu}")
    st.warning("Esta sección se encuentra en configuración técnica.")
