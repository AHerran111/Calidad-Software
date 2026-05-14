# app.py
import streamlit as st
from services.cfdi_generator import generar_cfdi
from services.signer_mock import sellar_cfdi
from services.pac_api import timbrar_cfdi
from utils.xml_utils import dict_to_xml
from utils.rfc_validator import validar_rfc
from utils.zipcode_validator import validar_zip
from datetime import datetime
from utils.vars import vars
from utils.database import get_emisores, get_receptores
from forex_python.converter import CurrencyRates


c = CurrencyRates()
emisores = get_emisores()
receptores = get_receptores()

st.set_page_config(page_title="Crear Factura", page_icon="📈")

def calcular_totales(rows):

    subtotal = 0
    impuestos = 0
    descuentos = 0
    total = 0

    for row in rows:

        subtotal += row.get("Importe", 0)
        impuestos += row.get("ImporteImpuesto", 0)

        descuento_row = (
            row.get("Importe", 0)
            - row.get("Base", 0)
        )

        descuentos += descuento_row

        total += row.get("Total", 0)

    return {
        "subtotal": round(subtotal, 2),
        "impuestos": round(impuestos, 2),
        "descuentos": round(descuentos, 2),
        "total": round(total, 2)
    }

button_state = False

# Inputs
fecha = st.date_input("Fecha de Factura",min_value=vars["date"],max_value="today")
emisor_predef = st.selectbox("Emisor",emisores)
#print(emisores[emisor_predef])
# emisor = st.text_input("RFC Emisor",disabled=True)
# regimen_emisor = st.selectbox("Regimen Fiscal",vars["regimenes"],key='reg_emisor',disabled=True)
st.subheader("Datos emisor")
st.table(emisores[emisor_predef])
st.divider()
# razon_social_receptor  = st.text_input("Razón Social Receptor")
# receptor = st.text_input("RFC Receptor")
# regimen_receptor = st.selectbox("Regimen Fiscal",vars["regimenes"],key='reg_receptor')

st.subheader("Datos receptor")

receptor_names = [r["nombre"] for r in receptores]

receptor_selected = st.selectbox(
    "Receptor",
    receptor_names
)

receptor_data = next(
    r for r in receptores
    if r["nombre"] == receptor_selected
)

razon_social_receptor = receptor_data["nombre"]

receptor = st.text_input(
    "RFC Receptor",
    value=receptor_data["rfc"],
    disabled=True
)

regimen_receptor = st.text_input(
    "Regimen Fiscal",
    value=receptor_data["regimen_fiscal"],
    disabled=True
)

zipcode = st.text_input(
    "Codigo Postal",
    value=receptor_data["codigo_postal"],
    disabled=True
)

uso_cfdi = st.selectbox("Uso",vars['CFDIS'])

for code in vars["morales_codes"]:
    if code in regimen_receptor:
        if uso_cfdi not in vars["morales_options"]:
            button_state = True
            st.error(f"{uso_cfdi} no valido para {regimen_receptor}")
            break


        
st.divider()

if "rows" not in st.session_state:
    st.session_state.rows = [{
        "Producto": '',
        "Referencia": '',

        # CFDI 4.0
        "ClaveProdServ": '',
        "ClaveUnidad": '',
        "Unidad": '',

        "Precio": 0.00,
        "Cantidad": 0.00,

        "ValorUnitario": 0.00,
        "Importe": 0.00,

        "Impuesto": 0.00,
        "Descuento": 0.00,

        # CFDI impuestos
        "ObjetoImp": '02',
        "Base": 0.00,
        "TipoFactor": 'Tasa',
        "TasaOCuota": 0.160000,
        "ImporteImpuesto": 0.00,

        "Descripcion": '',
        "Total": 0.00
    }]

def add_row():
    st.session_state.rows.append({
        "Producto": '',
        "Referencia": '',

        # CFDI 4.0
        "ClaveProdServ": '',
        "ClaveUnidad": '',
        "Unidad": '',

        "Precio": 0.00,
        "Cantidad": 0.00,

        "ValorUnitario": 0.00,
        "Importe": 0.00,

        "Impuesto": 0.00,
        "Descuento": 0.00,

        # CFDI impuestos
        "ObjetoImp": '02',
        "Base": 0.00,
        "TipoFactor": 'Tasa',
        "TasaOCuota": 0.160000,
        "ImporteImpuesto": 0.00,

        "Descripcion": '',
        "Total": 0.00
    })
    st.rerun()

def remove_row(index):
    st.session_state.rows.pop(index)

for i, row in enumerate(st.session_state.rows):

    cols = st.columns(14)

    with cols[0]:
        st.session_state.rows[i]["Producto"] = st.text_input(
            "Producto", key=f"producto_{i}"
        )


    with cols[1]:
        st.session_state.rows[i]["Unidad"] = st.text_input(
            "Unidad", key=f"unidad_{i}"
        )

    with cols[2]:
        cantidad = st.session_state.rows[i]["Cantidad"] = st.number_input(
            "Cantidad", min_value=0.0, key=f"cant_{i}"
        )

    with cols[3]:
        valor_unitario = st.session_state.rows[i]["ValorUnitario"] = st.number_input(
            "Valor Unitario", min_value=0.0, key=f"vu_{i}"
        )

    with cols[4]:
        descuento = st.session_state.rows[i]["Descuento"] = st.number_input(
            "Descuento %", min_value=0.0, key=f"desc_{i}"
        )

    with cols[5]:
        tasa = st.session_state.rows[i]["TasaOCuota"] = st.number_input(
            "IVA", min_value=0.0, value=0.160000, format="%.6f", key=f"iva_{i}"
        )

    with cols[6]:
        st.session_state.rows[i]["ObjetoImp"] = st.selectbox(
            "ObjetoImp",
            ["01", "02", "03"],
            index=1,
            key=f"objimp_{i}"
        )

    with cols[7]:
        st.session_state.rows[i]["TipoFactor"] = st.selectbox(
            "TipoFactor",
            ["Tasa", "Cuota", "Exento"],
            key=f"tf_{i}"
        )

    # ===== CALCULOS CFDI =====

    importe = round(cantidad * valor_unitario, 2)
    descuento_importe = round(importe * (descuento / 100), 2)
    base = round(importe - descuento_importe, 2)

    impuesto_importe = round(base * tasa, 2)

    total = round(base + impuesto_importe, 2)

    st.session_state.rows[i]["Importe"] = importe
    st.session_state.rows[i]["Base"] = base
    st.session_state.rows[i]["ImporteImpuesto"] = impuesto_importe
    st.session_state.rows[i]["Total"] = total


    with cols[8]:
        st.text_input(
            "Importe",
            value=str(importe),
            disabled=True,
        )

    with cols[9]:
        st.text_input(
            "Impuesto",
            value=str(impuesto_importe),
            disabled=True,
        )

    with cols[10]:
        st.text_input(
            "Total",
            value=total,
            disabled=True,
        )

    st.session_state.rows[i]["Descripcion"] = st.text_area(
        "Descripcion",
        key=f"desc_txt_{i}"
    )
        

st.button("➕ Agregar concepto", on_click=add_row)


totales  = calcular_totales(st.session_state.rows)

#print(totales)

cols = st.columns(3)
with cols[2]:
    st.text(f"Subtotal: ${round(totales['subtotal'],3)}",text_alignment="right")
    st.text(f"Impuestos: ${round(totales['impuestos'],3)}",text_alignment="right")
    st.text(f"Descuentos: ${round(totales['descuentos'],3)}",text_alignment="right")
    st.text(f"Total: ${round(totales['total'],3)}",text_alignment="right")

forma_pago = st.selectbox("Forma de Pago",vars['formas'])
moneda_pago = st.selectbox("Forma de Pago",vars['monedas'],index=0)

tipo_cambio = c.get_rate(moneda_pago, 'MXN')
st.text(f"Razon de cambio\n {tipo_cambio} MXN")


metodo_pago = st.selectbox("Metodo de Pago",["Pago En Una Sola Exhibición (PUE)",
                                             "Pago en Parcialidades o Diferido (PPD)"])

if "(PPD)" in metodo_pago and forma_pago != "99 POR DEFINIR":
        button_state = True
        st.error(f"La forma de pago para '{metodo_pago}' tiene que ser '99 POR DEFINIR'")



#print(st.session_state.rows)

data = {
    "emisor": emisor_predef,

    "rfc_emisor": emisores[emisor_predef]["rfc"],
    "regimen_emisor": emisores[emisor_predef]["regimen"],
    "cp_emisor": emisores[emisor_predef]["cp"],
    "direccion_emisor": emisores[emisor_predef]["address"],

    "receptor": razon_social_receptor,
    "rfc_receptor": receptor,

    "regimen_receptor": regimen_receptor,
    "uso_cfdi": uso_cfdi,

    "cp": zipcode,

    "subtotal": round(totales["subtotal"], 2),
    "total_final": round(totales["total"], 2),

    "conceptos": st.session_state.rows,

    "forma_pago": forma_pago,
    "metodo_pago": metodo_pago,

    "moneda": moneda_pago,
    "tipo_cambio": tipo_cambio,

    "fecha": datetime.now().isoformat()
}



for row in data.values():
    #print(row)
    if(row) == "" or (row) == 0:
        button_state = True
        print(f"error en {row}")

data.update({ "impuestos_final": round(totales["impuestos"], 2),
        "descuentos_final": round(totales["descuentos"], 2)})

if st.button("Generar CFDI",disabled = button_state):
    cfdi = generar_cfdi(data)
    cfdi = sellar_cfdi(cfdi)
    
    

    st.success("CFDI generado y timbrado (simulado)")
    st.json(cfdi)

    xml = dict_to_xml(cfdi)

   
        #print(xml)
    try:
        xml_timbrado = timbrar_cfdi(xml)
        #print(xml_timbrado)
    except Exception as e:
        print(e)

    st.download_button(
        label="Descargar XML",
        data=xml_timbrado,
        file_name="cfdi.xml",
        mime="application/xml"
    )