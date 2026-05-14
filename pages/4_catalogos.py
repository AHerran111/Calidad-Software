# pages/4_catalogos.py

import pandas as pd
import streamlit as st
from utils.database import get_connection, insertar_emisor, insertar_receptor
from utils.vars import vars

st.set_page_config(page_title="Catálogos", page_icon="📂")

conn = get_connection()

st.title("Administrar Emisores y Receptores")

tab1, tab2 = st.tabs(["Emisores", "Receptores"])

# =========================================================
# EMISORES
# =========================================================

with tab1:
    st.header("Crear Emisor")

    with st.form("form_emisor"):
        nombre = st.text_input("Nombre")
        rfc = st.text_input("RFC")
        regimen = st.selectbox("Régimen Fiscal", vars["regimenes"])
        cp = st.text_input("Código Postal")
        direccion = st.text_area("Dirección")

        submitted = st.form_submit_button("Guardar Emisor")

        if submitted:
            insertar_emisor(conn, rfc, nombre, regimen, cp, direccion)

            st.success("Emisor guardado")

    st.divider()

    st.subheader("Carga Masiva Emisores")

    archivo_emisores = st.file_uploader(
        "Subir CSV Emisores", type=["csv"], key="emisores_csv"
    )

    if archivo_emisores is not None:
        df = pd.read_csv(archivo_emisores)

        st.dataframe(df)

        if st.button("Importar Emisores"):
            for _, row in df.iterrows():
                insertar_emisor(
                    conn,
                    row["rfc"],
                    row["nombre"],
                    row["regimen_fiscal"],
                    str(row["codigo_postal"]),
                    row["direccion"],
                )

            st.success("Emisores importados")


# =========================================================
# RECEPTORES
# =========================================================

with tab2:
    st.header("Crear Receptor")

    with st.form("form_receptor"):
        nombre = st.text_input("Nombre ", key="rec_nombre")
        rfc = st.text_input("RFC ", key="rec_rfc")
        regimen = st.selectbox("Régimen Fiscal", vars["regimenes"])
        cp = st.text_input("Código Postal ", key="rec_cp")

        submitted = st.form_submit_button("Guardar Receptor")

        if submitted:
            insertar_receptor(conn, rfc, nombre, regimen, cp)

            st.success("Receptor guardado")

    st.divider()

    st.subheader("Carga Masiva Receptores")

    archivo_receptores = st.file_uploader(
        "Subir CSV Receptores", type=["csv"], key="receptores_csv"
    )

    if archivo_receptores is not None:
        df = pd.read_csv(archivo_receptores)

        st.dataframe(df)

        if st.button("Importar Receptores"):
            for _, row in df.iterrows():
                insertar_receptor(
                    conn,
                    row["rfc"],
                    row["nombre"],
                    row["regimen_fiscal"],
                    str(row["codigo_postal"]),
                )

            st.success("Receptores importados")
