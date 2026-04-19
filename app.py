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
# 1. MOTOR DE EXTRACCIÓN (NÚCLEO DE IA)
# ==========================================

@st.cache_resource
def load_ocr_model():
    return easyocr.Reader(['es', 'en'], gpu=False)

def preprocess_image(imagen_pil):
    """Mejora visual para evitar casillas vacías y errores de lectura."""
    img = np.array(imagen_pil.convert('RGB'))
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    gris = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Upscaling para capturar decimales pequeños
    alto, ancho = gris.shape
    img_res = cv2.resize(gris, (ancho * 2, alto * 2), interpolation=cv2.INTER_LANCZOS4)
    
    # Binarización para eliminar ruido de fondo
    binaria = cv2.adaptiveThreshold(
        img_res, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )
    return binaria

def skill_extract_tabular_data(imagen_pil):
    try:
        reader = load_ocr_model()
        img_pre = preprocess_image(imagen_pil)
        ancho_total = img_pre.shape[1]
        
        results = reader.readtext(img_pre, detail=1)
        if not results: return None

        filas_dict = {}
        tolerancia_y = 20 

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
                if pct_x < 0.08: c_long.append(txt)
                elif 0.08 <= pct_x < 0.15: 
                    if any(char.isdigit() for char in txt): c_od.append(txt)
                    else: c_desc.append(txt)
                elif 0.15 <= pct_x < 0.72: c_desc.append(txt)
                elif 0.72 <= pct_x < 0.86: c_top.append(txt)
                else: c_base.append(txt)

            desc_raw = " ".join(c_desc).strip()
            def clean_numeric(val_list):
                v = "".join(val_list).replace(",", ".")
                return re.sub(r'[^0-9.]', '', v)

            long_raw, od_raw, top_raw, base_raw = clean_numeric(c_long), clean_numeric(c_od), clean_numeric(c_top), clean_numeric(c_base)

            # Estrategia de división de pegados
            if top_raw and not base_raw:
                parts = re.findall(r'\d+\.\d+|\d+', top_raw)
                if len(parts) >= 2:
                    top_raw, base_raw = parts[0], parts[1]

            if len(desc_raw) > 3 and not any(p in desc_raw for p in ["Descripción", "Componente", "MD", "PROD"]):
                datos_tabla.append({
                    "Long(ft)": long_raw, "OD(in)": od_raw,
                    "Descripción del Componente": desc_raw.lstrip('|/ ').strip(),
                    "MD Top(ft)": top_raw, "Base MD(ft)": base_raw
                })

        df = pd.DataFrame(datos_tabla)
        # Lógica de Continuidad
        for i in range(len(df) - 1):
            if not df.loc[i, "Base MD(ft)"]:
                df.loc[i, "Base MD(ft)"] = df.loc[i+1, "MD Top(ft)"]
        return df
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

# ==========================================
# 2. INTERFAZ MULTI-MÓDULO (RECUPERADA)
# ==========================================
st.set_page_config(page_title="Well Planning CUA", page_icon="🏗️", layout="wide")

if 'menu' not in st.session_state:
    st.session_state.menu = "Home"

with st.sidebar:
    st.markdown("<h1 style='text-align: center; color: #2E7D32;'>ECOPETROL 🦎</h1>", unsafe_allow_html=True)
    st.divider()
    if st.button("🏠 Inicio / Dashboard", use_container_width=True):
        st.session_state.menu = "Home"
    st.markdown("### 🛠️ Operaciones")
    if st.button("🌑 1. Abandonos", use_container_width=True): st.session_state.menu = "Abandonos"
    if st.button("⚙️ 2. Mantenimiento BES", use_container_width=True): st.session_state.menu = "BES"
    if st.button("📊 3. Rediseño SLA", use_container_width=True): st.session_state.menu = "SLA"
    if st.button("🛠️ 4. Workover", use_container_width=True): st.session_state.menu = "Workover"

# --- LÓGICA DE NAVEGACIÓN ---

if st.session_state.menu == "Home":
    st.title("🚧 Well Planning - Operaciones CUA")
    st.info("Bienvenido al sistema unificado de extracción de datos para Ingeniería de Pozos.")
    # Resumen visual o métricas podrían ir aquí

elif st.session_state.menu == "BES":
    st.title("⚙️ Módulo: Mantenimiento BES")
    tab1, tab2 = st.tabs(["🏗️ Estado Mecánico", "📈 Histórico"])
    with tab1:
        pasted = paste_image_button(label="📋 Pegar recorte de la Sarta de Producción", key="bes_paster")
        if pasted.image_data:
            st.image(pasted.image_data, caption="Recorte detectado", width=800)
            if st.button("🚀 Extraer Datos"):
                df = skill_extract_tabular_data(pasted.image_data)
                if df is not None:
                    st.dataframe(df, use_container_width=True)
                    st.download_button("📥 Descargar CSV", df.to_csv(index=False), "sarta_bes.csv")

elif st.session_state.menu == "Abandonos":
    st.title("🌑 Módulo: Abandonos de Pozo")
    st.write("Cargue los datos de tapones y cortes de tubería.")
    # Aquí irá la lógica específica de Abandonos

elif st.session_state.menu == "SLA":
    st.title("📊 Módulo: Rediseño SLA")
    st.write("Análisis de sartas de varillas y bombeo mecánico.")

elif st.session_state.menu == "Workover":
    st.title("🛠️ Módulo: Workover")
    st.write("Optimización de tiempos y movimientos de intervención.")
