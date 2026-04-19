import streamlit as st
import easyocr
from PIL import Image
import numpy as np
import pandas as pd
import re
import cv2
from streamlit_paste_button import paste_image_button

# ==========================================
# 1. MOTOR DE EXTRACCIÓN CON LÓGICA DE SECUENCIA
# ==========================================

@st.cache_resource
def load_ocr_model():
    return easyocr.Reader(['es', 'en'], gpu=False)

def preprocess_image(imagen_pil):
    img = np.array(imagen_pil.convert('RGB'))
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    gris = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Aumentamos el contraste para separar números pegados
    alto, ancho = gris.shape
    gris = cv2.resize(gris, (ancho * 2, alto * 2), interpolation=cv2.INTER_LANCZOS4)
    
    # Binarización más fina para no "engrosar" los números
    binaria = cv2.adaptiveThreshold(
        gris, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, 3
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
                
                # REFINAMIENTO DE COLUMNAS (Basado en tu última imagen)
                if pct_x < 0.12: c_long.append(txt)
                elif 0.12 <= pct_x < 0.22: 
                    if any(c.isdigit() for c in txt): c_od.append(txt)
                    else: c_desc.append(txt)
                elif 0.22 <= pct_x < 0.68: c_desc.append(txt)
                elif 0.68 <= pct_x < 0.84: c_top.append(txt) # MD Top
                else: c_base.append(txt) # Base MD

            desc_raw = " ".join(c_desc).strip()
            # Limpieza rápida de ruidos comunes de OCR en descripciones
            desc_raw = desc_raw.replace("/", "").replace("|", "").strip()
            
            # --- PROCESAMIENTO NUMÉRICO ---
            def clean_n(v_list):
                v = "".join(v_list).replace(",", ".")
                return re.sub(r'[^0-9.]', '', v)

            val_top = clean_n(c_top)
            val_base = clean_n(c_base)

            # LÓGICA DE RESCATE: Si Top tiene muchos dígitos y Base está vacío
            # Ejemplo: "24.525.4" -> Top: 24.5, Base: 25.4
            if val_top and not val_base:
                puntos = [m.start() for m in re.finditer(r'\.', val_top)]
                if len(puntos) >= 2:
                    corte = puntos[1] # Cortamos en el segundo punto
                    val_base = val_top[corte:]
                    val_top = val_top[:corte]
                elif len(val_top) > 6: # Si es un número muy largo sin puntos extra
                    mitad = len(val_top) // 2
                    val_base = val_top[mitad:]
                    val_top = val_top[:mitad]

            if len(desc_raw) > 2 and not any(p in desc_raw for p in ["Descripción", "Componente", "PROD"]):
                datos_tabla.append({
                    "Long(ft)": clean_n(c_long),
                    "OD(in)": clean_n(c_od),
                    "Descripción del Componente": desc_raw,
                    "MD Top(ft)": val_top,
                    "Base MD(ft)": val_base
                })

        df = pd.DataFrame(datos_tabla)

        # --- LÓGICA FINAL: RELLENO POR CONTINUIDAD ---
        # En Well Planning, Base(n) = Top(n+1). Si falta la base, la inferimos.
        for i in range(len(df) - 1):
            if not df.loc[i, "Base MD(ft)"] or df.loc[i, "Base MD(ft)"] == "":
                siguiente_top = df.loc[i+1, "MD Top(ft)"]
                if siguiente_top:
                    df.loc[i, "Base MD(ft)"] = siguiente_top

        return df
            
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

# ==========================================
# 2. INTERFAZ (Sin cambios significativos)
# ==========================================
st.set_page_config(page_title="Well Planning - Operaciones CUA", page_icon="🏗️", layout="wide")

if 'menu' not in st.session_state:
    st.session_state.menu = "Home"

with st.sidebar:
    st.markdown("<h1 style='text-align: center; color: #2E7D32;'>ECOPETROL 🦎</h1>", unsafe_allow_html=True)
    if st.button("🏠 Inicio", use_container_width=True):
        st.session_state.menu = "Home"
        st.rerun()

if st.session_state.menu == "Home":
    st.title("🚧 Construcción Well Plan - Operaciones CUA")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⚙️ 2. Mantenimiento BES", use_container_width=True): st.session_state.menu = "BES"
    with col2:
        if st.button("🛠️ 4. Workover", use_container_width=True): st.session_state.menu = "Workover"

elif st.session_state.menu == "BES":
    st.title("⚙️ Módulo de Extracción BES")
    tab1, tab2, tab3 = st.tabs(["🏗️ Cabezal", "🕳️ Liner", "🔌 Sarta"])
    
    def procesar(label, key):
        pasted = paste_image_button(label=f"📋 Pegar Tabla de {label}", key=key)
        if pasted.image_data:
            st.image(pasted.image_data, caption="Imagen detectada", width=700)
            if st.button(f"🚀 Extraer {label}", key=f"btn_{key}"):
                df = skill_extract_tabular_data(pasted.image_data)
                if df is not None:
                    st.success("Extracción completada con lógica de continuidad.")
                    st.dataframe(df, use_container_width=True)
                    st.download_button("📥 Descargar CSV", df.to_csv(index=False), f"{label}.csv")

    with tab3: procesar("Sarta", "sarta_paste")

else:
    st.warning("Sección en desarrollo.")
