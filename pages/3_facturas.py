#/pages/3_facturas.py
import streamlit as st
from utils.database import get_facturas

st.title("Facturas")


col1, col2, col3, col4 = st.columns(4)

with col1:
    estado = st.selectbox("Estado", ["Todos", "TIMBRADO", "PENDIENTE", "CANCELADO"])

with col2:
    rfc_emisor = st.text_input("RFC Emisor")

with col3:
    rfc_receptor = st.text_input("RFC Receptor")

with col4:
    fecha = st.date_input("Fecha", value=None)


df = get_facturas(
    estado=estado, rfc_emisor=rfc_emisor, rfc_receptor=rfc_receptor, fecha=fecha
)

st.dataframe(df, use_container_width=True)
