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
# 1. MOTOR DE EXTRACCIÓN ULTRA-OPTIMIZADO
# ==========================================

@st.cache_resource
def load_ocr_model():
    return easyocr.Reader(['es', 'en'], gpu=False)

def preprocess_image(imagen_pil):
    """Mejora visual para que el OCR no ignore caracteres pequeños."""
    img = np.array(imagen_pil.convert('RGB'))
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    gris = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Upscaling x2: Hace que los números sean más grandes y legibles
    alto, ancho = gris.shape
    gris = cv2.resize(gris, (ancho * 2, alto * 2), interpolation=cv2.INTER_LANCZOS4)
    
    # Binarización adaptativa para eliminar sombras y resaltar el negro
    binaria = cv2.adaptiveThreshold(
        gris, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )
    return binaria

def skill_extract_tabular_data(imagen_pil):
    try:
        reader = load_ocr_model()
        img_pre = preprocess_image(imagen_pil)
        ancho_total = img_pre.shape[1]
        
        results = reader.readtext(img_pre, detail=1)
        if not results: return None

        # --- Agrupamiento por Filas ---
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
                
                # Zonificación corregida para capturar el extremo derecho
                if pct_x < 0.10: c_long.append(txt)
                elif 0.10 <= pct_x < 0.20: 
                    if any(c.isdigit() for c in txt): c_od.append(txt)
                    else: c_desc.append(txt)
                elif 0.20 <= pct_x < 0.70: c_desc.append(txt)
                elif 0.70 <= pct_x < 0.86: c_top.append(txt)
                else: c_base.append(txt)

            desc_raw = " ".join(c_desc).replace("/", "").replace("|", "").strip()
            
            # --- Limpieza de Números ---
            def clean_numeric(v_list):
                v = "".join(v_list).replace(",", ".")
                return re.sub(r'[^0-9.]', '', v)

            val_top = clean_numeric(c_top)
            val_base = clean_numeric(c_base)

            # --- ESTRATEGIA: Divisor de Emergencia ---
            # Si el Top tiene dos puntos (ej: 24.525.4) lo dividimos
            if val_top and not val_base:
                parts = re.findall(r'\d+\.\d+|\d+', val_top)
                if len(parts) >= 2:
                    val_top = parts[0]
                    val_base = parts[1]

            if len(desc_raw) > 3 and not any(p in desc_raw for p in ["Descripción", "Componente", "PROD"]):
                datos_tabla.append({
                    "Long(ft)": clean_numeric(c_long),
                    "OD(in)": clean_numeric(c_od),
                    "Descripción del Componente": desc_raw,
                    "MD Top(ft)": val_top,
                    "Base MD(ft)": val_base
                })

        df = pd.DataFrame(datos_tabla)

        # --- LÓGICA DE CONTINUIDAD (La "Magia" final) ---
        # Si Base MD está vacía, la llenamos con el Top de la fila siguiente
        for i in range(len(df) - 1):
            if not df.loc[i, "Base MD(ft)"] or df.loc[i, "Base MD(ft)"] == "":
                df.loc[i, "Base MD(ft)"] = df.loc[i+1, "MD Top(ft)"]

        return df
            
    except Exception as e:
        st.error(f"Error técnico: {str(e)}")
        return None

# ==========================================
# 2. INTERFAZ DE USUARIO
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
    if st.button("⚙️ Ir a Mantenimiento BES", use_container_width=True):
        st.session_state.menu = "BES"
        st.rerun()

elif st.session_state.menu == "BES":
    st.title("⚙️ Extracción de Estado Mecánico")
    pasted = paste_image_button(label="📋 Clic aquí y presiona Ctrl+V para pegar el recorte", key="paster")
    
    if pasted.image_data:
        st.image(pasted.image_data, caption="Imagen para análisis", width=800)
        if st.button("🚀 Procesar Tabla con IA"):
            with st.status("Mejorando enfoque y extrayendo datos...") as s:
                df_final = skill_extract_tabular_data(pasted.image_data)
                s.update(label="¡Extracción exitosa!", state="complete")
            
            if df_final is not None and not df_final.empty:
                st.dataframe(df_final, use_container_width=True)
                csv = df_final.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Descargar CSV para Well Plan", csv, "estado_mecanico.csv", "text/csv")
