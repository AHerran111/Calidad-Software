# pages/2_timbrar_factura.py

import pandas as pd
import streamlit as st
from services.pac_api import timbrar_cfdi
from utils.database import (
    actualizar_timbrado,
    get_connection,
    obtener_pendientes,
    obtener_xml,
)

st.set_page_config(page_title="Timbrar Facturas", page_icon="📄")

st.title("Timbrado de Facturas")

conn = get_connection()

# =========================================================
# FACTURAS PENDIENTES
# =========================================================
# ORDEN:
# 0 SELLO
# 1 RFC_EMISOR
# 2 RFC_RECEPTOR
# 3 TOTAL
# 4 FECHA
# 5 XML
# 6 ESTADO

pendientes = obtener_pendientes(conn)

if not pendientes:
    st.warning("No hay facturas pendientes")
    st.stop()


# =========================================================
# SELECTBOX
# =========================================================

options = {f"{r[4]} | {r[1]} -> {r[2]} | ${r[3]}": r[0] for r in pendientes}

selected = st.selectbox("Facturas Pendientes", list(options.keys()))

sello = options[selected]


# =========================================================
# DETALLE FACTURA
# =========================================================

factura = next(r for r in pendientes if r[0] == sello)

detalle = {
    "SELLO": factura[0],
    "RFC EMISOR": factura[1],
    "RFC RECEPTOR": factura[2],
    "TOTAL": factura[3],
    "FECHA": factura[4],
    "ESTADO": factura[5],
}

st.subheader("Detalle de Factura")

df = pd.DataFrame([detalle])

st.table(df)


# =========================================================
# TIMBRAR
# =========================================================

if st.button("Timbrar"):
    try:
        xml = obtener_xml(conn, sello)

        xml_timbrado = timbrar_cfdi(xml)

        actualizar_timbrado(conn, sello, xml_timbrado)

        st.success("Factura timbrada correctamente")

        st.download_button(
            label="Descargar XML Timbrado",
            data=xml_timbrado,
            file_name="cfdi_timbrado.xml",
            mime="application/xml",
        )

    except Exception as e:
        st.error(str(e))
