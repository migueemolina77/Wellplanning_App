import streamlit as st
import google.generativeai as genai
from PIL import Image
import io
import time

# 1. Función de IA Optimizada
def skill_vision_well_plan(imagen_em, instruccion_especifica):
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt_turbo = f"""
    Actúa como un experto en Well Planning de Ecopetrol. 
    Analiza este recorte de un Estado Mecánico y extrae: {instruccion_especifica}.
    Respuesta corta, técnica y directa. Si no lo ves, di 'No detectado'.
    """
    try:
        response = model.generate_content([prompt_turbo, imagen_em])
        return response.text
    except Exception as e:
        return f"Error de conexión: {str(e)}"

# 2. Configuración de página
st.set_page_config(page_title="Well Planning - Operaciones", page_icon="🏗️", layout="wide")

# 3. Inicialización del estado del menú
if 'menu_actual' not in st.session_state:
    st.session_state.menu_actual = "Home"

# 4. Sidebar con Logo
with st.sidebar:
    st.markdown("<h1 style='text-align: center; color: #2E7D32;'>ECOPETROL 🦎</h1>", unsafe_allow_html=True)
    st.markdown("---")
    if st.button("🏠 Volver al Home", use_container_width=True):
        st.session_state.menu_actual = "Home"
        st.rerun()

# 5. Lógica de Navegación Principal
if st.session_state.menu_actual == "Home":
    st.title("🚧 Construcción Well Plan - Operaciones CUA")
    st.subheader("Seleccione el tipo de operación para iniciar:")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🌑 1. Abandonos", use_container_width=True):
            st.session_state.menu_actual = "Abandonos"
            st.rerun()
        if st.button("⚙️ 2. Retiro y/o Mantenimiento BES", use_container_width=True):
            st.session_state.menu_actual = "BES"
            st.rerun()
    with col2:
        if st.button("📊 3. Rediseño SLA", use_container_width=True):
            st.session_state.menu_actual = "SLA"
            st.rerun()
        if st.button("🛠️ 4. Workover", use_container_width=True):
            st.session_state.menu_actual = "Workover"
            st.rerun()

elif st.session_state.menu_actual == "BES":
    st.title("⚙️ Módulo de Extracción por Secciones (BES)")
    st.info("💡 **Tip:** Haz clic en el recuadro de carga y presiona **Ctrl + V** para pegar tu captura de pantalla.")

    # DEFINICIÓN DE LA FUNCIÓN CON INDENTACIÓN CORRECTA
    def procesar_extraccion(archivo, instruccion, key_btn):
        if archivo:
            img = Image.open(archivo)
            img.thumbnail((800, 800))
            st.image(img, width=400, caption="Recorte detectado")
            
            if st.button(f"🔍 Ejecutar Escáner", key=key_btn):
                status_container = st.empty()
                progreso = st.progress(10)
                
                try:
                    with st.spinner("Procesando imagen..."):
                        # Paso 1: Simulación de carga y envío
                        status_container.info("⏳ Optimizando y enviando datos a la nube... (Paso 1/2)")
                        progreso.progress(40)
                        time.sleep(1) # Delay táctico para visualización
                        
                        # Paso 2: Llamada a la IA
                        status_container.warning("🤖 La IA está interpretando el Estado Mecánico... (Paso 2/2)")
                        progreso.progress(70)
                        
                        resultado = skill_vision_well_plan(img, instruccion)
                        
                        # Finalización
                        progreso.progress(100)
                        status_container.success("✅ ¡Datos recibidos con éxito!")
                        st.markdown(f"### Resultado Extraído:\n{resultado}")
                        
                except Exception as e:
                    status_container.error(f"❌ Error de comunicación: {str(e)}")

    tab1, tab2, tab3 = st.tabs(["🏗️ Cabezal (BOP)", "🕳️ Liner / Casing", "🔌 Sarta / BES"])

    with tab1:
        st.subheader("Información de Sección B / Cabezal")
        file_head = st.file_uploader("Pega/Sube recorte del Cabezal", type=["jpg", "png", "jpeg"], key="u_head")
        procesar_extraccion(file_head, "Tipo de Sección B (Tubing Head) y Presión Nominal (psi)", "btn_head")

    with tab2:
        st.subheader("Información de Revestimiento")
        file_liner = st.file_uploader("Pega/Sube recorte del Liner/Casing", type=["jpg", "png", "jpeg"], key="u_liner")
        procesar_extraccion(file_liner, "OD del Casing, Peso (lb/ft) y Grado del acero", "btn_liner")

    with tab3:
        st.subheader("Información de Sarta y Equipo BES")
        file_string = st.file_uploader("Pega/Sube recorte de la Sarta", type=["jpg", "png", "jpeg"], key="u_string")
        procesar_extraccion(file_string, "OD del Tubing, profundidad de la bomba BES (ft) y número de etapas si aplica", "btn_string")

    st.markdown("---")
    st.subheader("2. Verificación Manual")
    c1, c2 = st.columns(2)
    with c1:
        st.number_input("Profundidad de asentamiento (ft MD)", value=3433)
        st.selectbox("Diámetro de Tubing", ["3 1/2\"", "4 1/2\""])
    with c2:
        st.selectbox("Sección B", ["11\" 2K", "11\" 3K", "11\" 5K"])
        st.checkbox("¿Cuenta con sensor de fondo?")

# Espacios para otros módulos alineados
elif st.session_state.menu_actual == "Abandonos":
    st.title("🌑 Módulo de Abandonos")
    st.write("Contenido en desarrollo...")

elif st.session_state.menu_actual == "SLA":
    st.title("📊 Rediseño SLA")
    st.write("Contenido en desarrollo...")

elif st.session_state.menu_actual == "Workover":
    st.title("🛠️ Módulo de Workover")
    st.write("Contenido en desarrollo...")
