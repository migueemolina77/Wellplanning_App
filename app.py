import streamlit as st

st.set_page_config(page_title="Well Planning Tool", page_icon="🛢️")

st.title("🚀 Well Planning: Retiro de BES & Abandono")
st.markdown("---")

# Formulario inicial
with st.container():
    col1, col2 = st.columns(2)
    with col1:
        campo = st.text_input("Campo", "Rubiales")
        pozo = st.text_input("Pozo", "RB-123")
    with col2:
        fecha = st.date_input("Fecha de Operación")
        tipo = st.selectbox("Tipo de Operación", ["Retiro de BES", "Abandono Permanente", "Abandono Temporal"])

st.success(f"Configurando programa para el pozo {pozo} en el campo {campo}...")

# Espacio para el esquema del pozo (Handbook dinámico)
st.sidebar.header("Menú de Ingeniería")
if st.sidebar.button("Calcular Volumen de Control"):
    st.sidebar.write("Capacidad de Casing: 0.0387 bbl/ft")
