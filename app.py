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
# 1. MOTOR DE IA (PREPROCESAMIENTO + OCR + LÓGICA)
# ==========================================

@st.cache_resource
def load_ocr_model():
    return easyocr.Reader(['es', 'en'], gpu=False)

def preprocess_image(imagen_pil):
    """Mejora la nitidez para capturar todos los caracteres de la tabla."""
    img = np.array(imagen_pil.convert('RGB'))
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    gris = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Reescalado x2 para números pequeños
    alto, ancho = gris.shape
    img_res = cv2.resize(gris, (ancho * 2, alto * 2), interpolation=cv2.INTER_LANCZOS4)
    
    # Filtro adaptativo para eliminar sombras del reporte
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
        tolerancia_y = 22 

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
                elif 0.15 <= pct_x < 0.70: c_desc.append(txt)
                elif 0.70 <= pct_x < 0.86: c_top.append(txt)
                else: c_base.append(txt)

            desc_raw = " ".join(c_desc).strip()
            def clean_n(v_list):
                v = "".join(v_list).replace(",", ".")
                return re.sub(r'[^0-9.]', '', v)

            long_n, od_n, top_n, base_n = clean_n(c_long), clean_n(c_od), clean_n(c_top), clean_n(c_base)

            # Dividir si Top y Base se pegaron
            if top_n and not base_n:
                parts = re.findall(r'\d+\.\d+|\d+', top_n)
                if len(parts) >= 2: top_n, base_n = parts[0], parts[1]

            if len(desc_raw) > 3 and not any(p in desc_raw for p in ["Descripción", "Componente", "MD", "PROD"]):
                datos_tabla.append({
                    "Long(ft)": long_n, "OD(in)": od_n,
                    "Descripción del Componente": desc_raw.lstrip('|/ ').strip(),
                    "MD Top(ft)": top_n, "Base MD(ft)": base_n
                })

        df = pd.DataFrame(datos_tabla)
        # Relleno por continuidad (Base n = Top n+1)
        for i in range(len(df) - 1):
            if not df.loc[i, "Base MD(ft)"]:
                df.loc[i, "Base MD(ft)"] = df.loc[i+1, "MD Top(ft)"]
        return df
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

# ==========================================
# 2. INTERFAZ Y NAVEGACIÓN (CABEZAL, LINER, SARTA)
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
        st.image(pasted.image_data, caption=f"Imagen {label}", width=700)
        if st.button(f"🚀 Procesar {label}", key=f"btn_{label}"):
            df = skill_extract_tabular_data(pasted.image_data)
            if df is not None:
                st.success("Extracción completada")
                st.dataframe(df, use_container_width=True)
                st.download_button("📥 Descargar CSV", df.to_csv(index=False), f"{label}.csv")

if st.session_state.menu == "Home":
    st.title("🚧 Well Planning - Operaciones CUA")
    st.info("Seleccione un módulo en el menú lateral para comenzar.")

elif st.session_state.menu == "BES":
    st.title("⚙️ Módulo: Mantenimiento BES")
    t1, t2, t3 = st.tabs(["🏗️ Cabezal", "🕳️ Liner de Producción", "🔌 Production String (Sarta)"])
    with t1: render_extractor("Cabezal")
    with t2: render_extractor("Liner")
    with t3: render_extractor("Sarta")

else:
    st.title(f"Módulo {st.session_state.menu}")
    st.warning("Esta sección se encuentra en configuración técnica.")
