import streamlit as st
import pandas as pd
import pdfplumber # La herramienta que realmente lee el PDF

st.set_page_config(page_title="Well Planning Hub", layout="wide")

# --- FUNCIÓN DE EXTRACCIÓN REAL ---
def extraer_tablas_pdf(archivo_subido):
    todas_las_filas = []
    with pdfplumber.open(archivo_subido) as pdf:
        # Recorremos cada página del PDF
        for pagina in pdf.pages:
            tablas = pagina.extract_tables()
            for tabla in tablas:
                for fila in tabla:
                    # Limpiamos datos vacíos y filtramos filas irrelevantes
                    if fila[0] is not None and len(fila) > 3:
                        todas_las_filas.append(fila)
    
    if not todas_las_filas:
        return None

    # Convertimos a DataFrame
    df = pd.DataFrame(todas_las_filas)
    # Intentamos asignar la primera fila como encabezado si parece texto
    df.columns = df.iloc[0]
    df = df[1:].reset_index(drop=True)
    return df

# --- INTERFAZ ---
st.title("🏗️ Well Planning Hub - Extractor Real")

with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/f/f2/Ecopetrol_logo.svg", width=120)
    menu = st.radio("Módulos", ["Mantenimiento BES"])

if menu == "Mantenimiento BES":
    st.header("⚙️ Módulo BES: Carga de Archivo")
    archivo = st.file_uploader("Subir esquemático (PDF)", type=["pdf"])

    if archivo:
        if st.button("⚡ Extraer Datos del PDF"):
            with st.spinner("Leyendo tablas del documento..."):
                # Aquí ocurre la magia real
                resultado = extraer_tablas_pdf(archivo)
                
                if resultado is not None:
                    st.session_state.df_real = resultado
                    st.success("¡Lectura completada exitosamente!")
                else:
                    st.error("No se detectaron tablas claras en el PDF.")

    # MOSTRAR RESULTADOS
    if 'df_real' in st.session_state:
        st.subheader("📋 Componentes Detectados en el Documento")
        
        # Buscador dinámico sobre los datos reales
        busqueda = st.text_input("Filtrar componentes (ej: 'ESP', 'Tubing', '7 in')...")
        
        df_mostrar = st.session_state.df_real
        if busqueda:
            # Filtra en todas las columnas
            mask = df_mostrar.apply(lambda row: row.astype(str).str.contains(busqueda, case=False).any(), axis=1)
            df_mostrar = df_mostrar[mask]

        st.dataframe(df_mostrar, use_container_width=True)
        
        # Botón para descargar lo que leyó
        csv = df_mostrar.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Descargar Tabla en CSV", csv, "extraccion_pozo.csv", "text/csv")
