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
# 1. MOTOR DE IA REFINADO (CON CIRUGÍA DE STRINGS)
# ==========================================

@st.cache_resource
def load_ocr_model():
    return easyocr.Reader(['es', 'en'], gpu=False)

def preprocess_image(imagen_pil):
    img = np.array(imagen_pil.convert('RGB'))
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    gris = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    alto, ancho = gris.shape
    img_res = cv2.resize(gris, (ancho * 3, alto * 3), interpolation=cv2.INTER_CUBIC)
    
    blurred = cv2.GaussianBlur(img_res, (3, 3), 0)
    _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    return thresh

def skill_extract_tabular_data(imagen_pil):
    try:
        reader = load_ocr_model()
        img_pre = preprocess_image(imagen_pil)
        ancho_total = img_pre.shape[1]
        
        results = reader.readtext(img_pre, detail=1, paragraph=False)
        if not results: return None

        filas_dict = {}
        tolerancia_y = 25 

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
                if pct_x < 0.07: c_long.append(txt)
                elif 0.07 <= pct_x < 0.14: c_od.append(txt)
                elif 0.14 <= pct_x < 0.78: c_desc.append(txt)
                elif 0.78 <= pct_x < 0.89: c_top.append(txt)
                else: c_base.append(txt)

            # --- CIRUGÍA DE DATOS ---
            desc_raw = " ".join(c_desc).strip()
            od_raw = "".join(c_od).strip()
            
            # Si el OD está vacío pero la descripción empieza por un número (ej: 3.500|...)
            if od_raw == "":
                match_od = re.match(r'^(\d+\.\d+|\d+)', desc_raw)
                if match_od:
                    od_raw = match_od.group(1)
                    # Limpiamos la descripción del número extraído y caracteres basura
                    desc_raw = re.sub(r'^[\d.|/ ]+', '', desc_raw).strip()

            def clean_n(v):
                v = v.replace(",", ".")
                res = re.findall(r'\d+\.\d+|\d+', v)
                return res[0] if res else ""

            long_val = clean_n("".join(c_long))
            od_val = clean_n(od_raw)
            top_val = clean_n("".join(c_top))
            base_val = clean_n("".join(c_base))

            if len(desc_raw) > 3 and not any(p in desc_raw for p in ["PROD", "STRING", "Base", "Componente"]):
                datos_tabla.append({
                    "Long(ft)": long_val,
                    "OD(in)": od_val,
                    "Descripción del Componente": desc_raw,
                    "MD Top(ft)": top_val,
                    "Base MD(ft)": base_val
                })

        df = pd.DataFrame(datos_tabla)
        
        # Auto-relleno de Base MD basado en el Top siguiente
        for i in range(len(df) - 1):
            if df.loc[i, "Base MD(ft)"] == "" and df.loc[i+1, "MD Top(ft)"] != "":
                df.loc[i, "Base MD(ft)"] = df.loc[i+1, "MD Top(ft)"]
                
        return df
    except Exception as e:
        st.error(f"Error en el motor: {str(e)}")
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
    pasted = paste_image_button(label=f"📋 Pegar imagen de {label}", key=f"p_{label}")
    if pasted.image_data:
        col1, col2 = st.columns([1, 2])
        with col1:
            st.image(pasted.image_data, caption="Imagen detectada", use_container_width=True)
        with col2:
            if st.button(f"🚀 Procesar {label}", key=f"b_{label}"):
                df = skill_extract_tabular_data(pasted.image_data)
                if df is not None and not df.empty:
                    # Usamos data_editor para permitir ajustes manuales finales
                    df_final = st.data_editor(df, use_container_width=True, num_rows="dynamic")
                    csv = df_final.to_csv(index=False).encode('utf-8')
                    st.download_button("📥 Descargar CSV", csv, f"{label}.csv")
                else:
                    st.warning("No se detectaron datos. Intenta capturar las líneas divisorias de la tabla.")

if st.session_state.menu == "Home":
    st.title("🚧 Sistema Unificado Well Planning")
    st.info("Utilice el menú lateral para navegar entre los módulos operativos.")

elif st.session_state.menu == "BES":
    st.title("⚙️ Módulo: Mantenimiento BES")
    t1, t2, t3 = st.tabs(["🏗️ Cabezal", "🕳️ Liner de Producción", "🔌 Production String (Sarta)"])
    with t1: render_extractor("Cabezal")
    with t2: render_extractor("Liner")
    with t3: render_extractor("Sarta")

else:
    st.title(f"Módulo {st.session_state.menu}")
    st.warning("Sección en construcción técnica.")
