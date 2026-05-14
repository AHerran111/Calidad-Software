# pages/2_timbrar_factura.py

import streamlit as st

from utils.database import (
    obtener_pendientes,
    obtener_xml,
    actualizar_timbrado
)


from utils.database import get_connection

conn = get_connection()
cursor = conn.cursor()

from services.pac_api import timbrar_cfdi

pendientes = obtener_pendientes(conn)

options = {
    f"{r[0]} - ${r[2]}": r[0]
    for r in pendientes
}

selected = st.selectbox(
    "Facturas Pendientes",
    list(options.keys())
)

if st.button("Timbrar"):

    sello = options[selected]

    xml = obtener_xml(conn, sello)

    xml_timbrado = timbrar_cfdi(xml)

    actualizar_timbrado(
        conn,
        sello,
        xml_timbrado
    )

    st.success("Factura timbrada")