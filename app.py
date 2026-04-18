elif st.session_state.menu_actual == "BES":
    st.title("⚙️ Módulo de Extracción por Secciones")
    st.info("💡 **Tip de agilidad:** Haz clic en 'Browse files' y presiona **Ctrl + V** para pegar tu captura directamente.")

    tab1, tab2, tab3 = st.tabs(["🏗️ Cabezal (BOP)", "🕳️ Liner / Casing", "🔌 Sarta / BES"])

    with tab1:
        st.subheader("Información de Sección B / Cabezal")
        file_head = st.file_uploader("Pega o sube el recorte del Cabezal", type=["jpg", "png", "jpeg"], key="u_head")
        if file_head:
            # PRIMERO: Abrimos la imagen
            img_head = Image.open(file_head)
            # SEGUNDO: Reducimos tamaño (Esto es lo que faltaba en tu código)
            img_head.thumbnail((800, 800))
            
            st.image(img_head, width=300)
            if st.button("🔍 Extraer Cabezal"):
                with st.spinner("Analizando cabezal..."):
                    res = skill_vision_well_plan(img_head, "Identifica el tipo de Sección B (Tubing Head) y su presión nominal.")
                    st.success(res)

    with tab2:
        st.subheader("Información de Revestimiento")
        file_liner = st.file_uploader("Pega o sube el recorte del Liner", type=["jpg", "png", "jpeg"], key="u_liner")
        if file_liner:
            img_liner = Image.open(file_liner)
            img_liner.thumbnail((800, 800)) # Aplicamos reducción aquí también
            
            st.image(img_liner, width=300)
            if st.button("🔍 Extraer Liner"):
                with st.spinner("Analizando revestimiento..."):
                    res = skill_vision_well_plan(img_liner, "Extrae el OD del Casing de producción, su peso y grado.")
                    st.success(res)

    with tab3:
        st.subheader("Información de Sarta y BES")
        file_string = st.file_uploader("Pega o sube el recorte de la Sarta", type=["jpg", "png", "jpeg"], key="u_string")
        if file_string:
            img_string = Image.open(file_string)
            img_string.thumbnail((800, 800)) # Aplicamos reducción aquí también
            
            st.image(img_string, width=300)
            if st.button("🔍 Extraer Sarta"):
                with st.spinner("Analizando sarta..."):
                    res = skill_vision_well_plan(img_string, "Extrae el OD del Tubing y la profundidad de asentamiento de la bomba BES.")
                    st.success(res)
