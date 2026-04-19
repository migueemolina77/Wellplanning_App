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
# 1. MOTOR DE EXTRACCIÓN DE ALTA PRECISIÓN
# ==========================================

@st.cache_resource
def load_ocr_model():
    """Carga el motor OCR una sola vez para ahorrar memoria."""
    return easyocr.Reader(['es', 'en'], gpu=False)

def preprocess_image(imagen_pil):
    """Mejora visual: Escalado y Binarización para caracteres pequeños."""
    img = np.array(imagen_pil.convert('RGB'))
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    gris = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Upscaling (x2): Fundamental para que el OCR vea bien los puntos decimales
    alto, ancho = gris.shape
    gris = cv2.resize(gris, (ancho * 2, alto * 2), interpolation=cv2.INTER_LANCZOS4)
    
    # Binarización Adaptativa: Texto negro puro sobre fondo blanco
    binaria = cv2.adaptiveThreshold(
        gris, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )
    return binaria

def skill_extract_tabular_data(imagen_pil):
    try:
        reader = load_ocr_model()
        img_pre = preprocess_image(imagen_pil)
        ancho_total = img_pre.shape[1]
        
        # Ejecución del OCR
        results = reader.readtext(img_pre, detail=1)
        if not results: return None

        # --- Agrupamiento por Filas (Eje Y) ---
        filas_dict = {}
        tolerancia_y = 22 # Ajustada para el reescalado

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
        
        # --- Clasificación por Columnas (Eje X) ---
        for y in sorted(filas_dict.keys()):
            elementos = sorted(filas_dict[y], key=lambda x: x[0])
            c_long, c_od, c_desc, c_top, c_base = [], [], [], [], []

            for x, txt in elementos:
                pct_x = x / ancho_total
                
                # Zonificación dinámica (Basada en image_3820c7.png)
                if pct_x < 0.10: c_long.append(txt)
                elif 0.10 <= pct_x < 0.20: 
                    if any(c.isdigit() for c in txt): c_od.append(txt)
                    else: c_desc.append(txt)
                elif 0.20 <= pct_x < 0.70: c_desc.append(txt)
                elif 0.70 <= pct_x < 0.86: c_top.append(txt)
                else: c_base.append(txt)

            # --- Limpieza y Rescate ---
            desc_raw = " ".join(c_desc).replace("/", "").replace("|", "").strip()
            
            def clean_numeric(v_list):
                v = "".join(v_list).replace(",", ".")
                return re.sub(r'[^0-9.]', '', v)

            val_top = clean_numeric(c_top)
            val_base = clean_numeric(c_base)

            # Estrategia de División: Si el Top absorbió a la Base (ej: 24.525.4)
            if val_top and not val_base:
                parts = re.findall(r'\d+\.\d+|\d+', val_top)
                if len(parts) >= 2:
                    val_top = parts[0]
                    val_base = parts[1]

            if len(desc_raw) > 3 and not any(p in desc_raw for p in ["Descripción", "Componente", "MD"]):
                datos_tabla.append({
                    "Long(ft)": clean_numeric(c_long),
                    "OD(in)": clean_numeric(c_od),
                    "Descripción del Componente": desc_raw,
                    "MD Top(ft)": val_top,
                    "Base MD(ft)": val_base
                })

        df = pd.DataFrame(datos_tabla)

        # --- LÓGICA DE CONTINUIDAD GEOMÉTRICA ---
        # Si Base(n) está vacía, se asume que es el Top(n+1)
        for i in range(len(df) - 1):
            if not df.loc[i, "Base MD(ft)"] or df.loc[i, "Base MD(ft)"] == "":
                df.loc[i, "Base MD(ft)"] = df.loc[i+1, "MD Top(ft)"]

        return df
            
    except Exception as e:
        st.error(f"Error técnico en el motor: {str(e)}")
        return None

# ==========================================
# 2. INTERFAZ STREAMLIT
# ==========================================
st.set_page_config(page_title="Well Plan CUA", page_icon="🏗️", layout="wide")

if 'menu' not in st.session_state:
    st.session_state.menu = "Home"

with st.sidebar:
    st.markdown("<h1 style='text-align: center; color: #2E7D32;'>ECOPETROL 🦎</h1>", unsafe_allow_html=True)
    if st.button("🏠 Inicio", use_container_width=True):
        st.session_state.menu = "Home"
        st.rerun()

if st.session_state.menu == "Home":
    st.title("🚧 Construcción Well Plan - Operaciones CUA")
    st.info("Sistema de extracción de estados mecánicos mediante visión artificial.")
    if st.button("⚙️ Entrar a Módulo BES", use_container_width=True):
        st.session_state.menu = "BES"
        st.rerun()

elif st.session_state.menu == "BES":
    st.title("⚙️ Extracción de Sarta de Producción")
    
    # Botón de pegado especial
    pasted = paste_image_button(label="📋 Clic aquí y presiona Ctrl+V para pegar el recorte", key="paster_main")
    
    if pasted.image_data:
        st.image(pasted.image_data, caption="Imagen cargada para análisis", width=800)
        
        if st.button("🚀 Extraer Datos con Lógica de Continuidad"):
            with st.status("Mejorando resolución y analizando filas...") as s:
                df_final = skill_extract_tabular_data(pasted.image_data)
                s.update(label="¡Análisis finalizado!", state="complete")
            
            if df_final is not None and not df_final.empty:
                st.success("Tabla recuperada con éxito:")
                st.dataframe(df_final, use_container_width=True)
                
                # Exportación
                csv = df_final.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Descargar Excel/CSV", csv, "sarta_pozo.csv", "text/csv")
            else:
                st.error("No se pudieron extraer datos. Prueba con un recorte más nítido.")
