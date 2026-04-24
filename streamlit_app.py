# app.py
import streamlit as st
from services.cfdi_generator import generar_cfdi
from services.signer_mock import sellar_cfdi
from services.pac_mock import timbrar_cfdi
from utils.xml_utils import dict_to_xml
from utils.rfc_validator import validar_rfc
from utils.zipcode_validator import validar_zip

city,state = '',''

st.title("Simulador CFDI + PAC")

# Inputs
emisor = st.text_input("RFC Emisor")
receptor = st.text_input("RFC Receptor")
regimen = st.selectbox("Regimen Fiscal",("601 REGIMEN GENERAL DE LEY PERSONAS MORALES",
"602 RÉGIMEN SIMPLIFICADO DE LEY PERSONAS MORALES",
"603 PERSONAS MORALES CON FINES NO LUCRATIVOS",
"604 RÉGIMEN DE PEQUEÑOS CONTRIBUYENTES",
"605 RÉGIMEN DE SUELDOS Y SALARIOS E INGRESOS ASIMILADOS A SALARIOS",
"606 RÉGIMEN DE ARRENDAMIENTO",
"607 RÉGIMEN DE ENAJENACIÓN O ADQUISICIÓN DE BIENES",
"608 RÉGIMEN DE LOS DEMÁS INGRESOS",
"609 RÉGIMEN DE CONSOLIDACIÓN",
"610 RÉGIMEN RESIDENTES EN EL EXTRANJERO SIN ESTABLECIMIENTO PERMANENTE EN MÉXICO",
"611 RÉGIMEN DE INGRESOS POR DIVIDENDOS (SOCIOS Y ACCIONISTAS)",
"612 RÉGIMEN DE LAS PERSONAS FÍSICAS CON ACTIVIDADES EMPRESARIALES Y PROFESIONALES",
"613 RÉGIMEN INTERMEDIO DE LAS PERSONAS FÍSICAS CON ACTIVIDADES EMPRESARIALES",
"614 RÉGIMEN DE LOS INGRESOS POR INTERESES",
"615 RÉGIMEN DE LOS INGRESOS POR OBTENCIÓN DE PREMIOS",
"616 SIN OBLIGACIONES FISCALES",
"617 PEMEX",
"618 RÉGIMEN SIMPLIFICADO DE LEY PERSONAS FÍSICAS",
"619 INGRESOS POR LA OBTENCIÓN DE PRÉSTAMOS",
"620 SOCIEDADES COOPERATIVAS DE PRODUCCIÓN QUE OPTAN POR DIFERIR SUS INGRESOS.",
"621 RÉGIMEN DE INCORPORACIÓN FISCAL",
"622 RÉGIMEN DE ACTIVIDADES AGRÍCOLAS, GANADERAS, SILVÍCOLAS Y PESQUERAS PM",
"623 RÉGIMEN DE OPCIONAL PARA GRUPOS DE SOCIEDADES",
"624 RÉGIMEN DE LOS COORDINADOS",
"625 RÉGIMEN DE LAS ACTIVIDADES EMPRESARIALES CON INGRESOS A TRAVÉS DE PLATAFORMAS TECNOLÓGICAS.",
"626 RÉGIMEN SIMPLIFICADO DE CONFIANZA"))
zipcode = st.text_input("Codigo Postal",max_chars=5)

if (st.button("Validar Código Postal",disabled=(len(zipcode) != 5))):
    try:
        city , state = validar_zip(int(zipcode))
        st.success("Codigo postal valido")
    except Exception:
        st.error("Codigo postal no valido")


st.text_input("Ciudad",disabled=True,value=city)
st.text_input("Estado",disabled = True,value = state)

total = st.number_input("Total", min_value=0.0)








if st.button("Generar CFDI"):
    data = {
        "emisor": emisor,
        "receptor": receptor,
        "total": total,
        "conceptos": []
    }

    cfdi = generar_cfdi(data)
    cfdi = sellar_cfdi(cfdi)
    cfdi = timbrar_cfdi(cfdi)

    xml = dict_to_xml(cfdi)

    st.success("CFDI generado y timbrado (simulado)")
    st.json(cfdi)

    st.download_button(
        label="Descargar XML",
        data=xml,
        file_name="cfdi.xml",
        mime="application/xml"
    )