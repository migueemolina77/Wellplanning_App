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
# 1. MOTOR DE IA REFINADO (ALTA FIDELIDAD)
# ==========================================

@st.cache_resource
def load_ocr_model():
    return easyocr.Reader(['es', 'en'], gpu=False)

def preprocess_image(imagen_pil):
    """
    Optimización específica para tablas con líneas claras como image_421969.png.
    """
    img = np.array(imagen_pil.convert('RGB'))
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    gris = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Escalado para asegurar que los puntos decimales se vean como pixeles sólidos
    alto, ancho = gris.shape
    img_res = cv2.resize(gris, (ancho * 3, alto * 3), interpolation=cv2.INTER_CUBIC)
    
    # Suavizado leve para quitar artefactos de compresión del pegado
    blurred = cv2.GaussianBlur(img_res, (3, 3), 0)
    
    # Umbralizado binario inverso (hace que el texto resalte más sobre el fondo)
    _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    return thresh

def skill_extract_tabular_data(imagen_pil):
    try:
        reader = load_ocr_model()
        img_pre = preprocess_image(imagen_pil)
        ancho_total = img_pre.shape[1]
        
        # Usamos paragraph=False para no perder precisión en celdas individuales
        results = reader.readtext(img_pre, detail=1, paragraph=False)
        if not results: return None

        filas_dict = {}
        tolerancia_y = 25 # Mayor tolerancia por el reescalado x3

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
                
                # Ajuste milimétrico de columnas basado en image_421969.png
                if pct_x < 0.07: c_long.append(txt)
                elif 0.07 <= pct_x < 0.14: c_od.append(txt)
                elif 0.14 <= pct_x < 0.78: c_desc.append(txt)
                elif 0.78 <= pct_x < 0.89: c_top.append(txt)
                else: c_base.append(txt)

            desc_raw = " ".join(c_desc).strip()
            
            def clean_n(v_list):
                v = "".join(v_list).replace(",", ".")
                # Captura números con puntos decimales
                res = re.findall(r'\d+\.\d+|\d+', v)
                return res[0] if res else ""

            top_val = clean_n(c_top)
            base_val = clean_n(c_base)

            # Validación de limpieza para la descripción
            if len(desc_raw) > 3 and not any(p in desc_raw for p in ["PROD", "STRING", "Base"]):
                datos_tabla.append({
                    "Long(ft)": clean_n(c_long),
                    "OD(in)": clean_n(c_od),
                    "Descripción del Componente": desc_raw.lstrip('|/ ').strip(),
                    "MD Top(ft)": top_val,
                    "Base MD(ft)": base_val
                })

        df = pd.DataFrame(datos_tabla)
        
        # --- LÓGICA DE AUTO-RELLENO ---
        # Si Base MD está vacía, toma el Top de la siguiente fila
        for i in range(len(df) - 1):
            if df.loc[i, "Base MD(ft)"] == "" and df.loc[i+1, "MD Top(ft)"] != "":
                df.loc[i, "Base MD(ft)"] = df.loc[i+1, "MD Top(ft)"]
                
        return df
    except Exception as e:
        st.error(f"Error en el motor: {str(e)}")
        return None

# ==========================================
# 2. INTERFAZ (MENÚ IZQUIERDO + PESTAÑAS)
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
        st.image(pasted.image_data, caption="Calidad de imagen detectada", width=800)
        if st.button(f"🚀 Procesar {label}", key=f"b_{label}"):
            df = skill_extract_tabular_data(pasted.image_data)
            if df is not None and not df.empty:
                st.dataframe(df, use_container_width=True)
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Descargar CSV", csv, f"{label}.csv")
            else:
                st.warning("El motor no pudo leer las celdas. Asegúrate de capturar las cabeceras.")

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
