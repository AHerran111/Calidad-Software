# utils/xml_utils.py

from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom
import uuid


def dict_to_xml(cfdi):

    NS_CFDI = "http://www.sat.gob.mx/cfd/4"
    NS_XSI = "http://www.w3.org/2001/XMLSchema-instance"
    NS_TFD = "http://www.sat.gob.mx/TimbreFiscalDigital"

    metodo_map = {
        "Pago En Una Sola Exhibición (PUE)": "PUE",
        "Pago en Parcialidades o Diferido (PPD)": "PPD"
    }

    forma_map = {
        "01 EFECTIVO": "01",
        "02 CHEQUE": "02",
        "03 TRANSFERENCIA": "03",
        "04 TARJETA DE CRÉDITO": "04",
        "28 TARJETA DE DÉBITO": "28",
        "99 POR DEFINIR": "99"
    }

    subtotal = round(float(cfdi["subtotal"]), 2)
    descuentos = round(float(cfdi["descuentos_final"]), 2)
    impuestos = round(float(cfdi["impuestos_final"]), 2)
    total = round(float(cfdi["total_final"]), 2)

    comprobante_attrs = {
        "xmlns:cfdi": NS_CFDI,
        "xmlns:xsi": NS_XSI,
        "xsi:schemaLocation": (
            "http://www.sat.gob.mx/cfd/4 "
            "http://www.sat.gob.mx/sitio_internet/cfd/4/cfdv40.xsd"
        ),

        "Version": "4.0",
        "Serie": "A",
        "Folio": str(uuid.uuid4())[:8],

        "Fecha": cfdi["fecha"],

        "Moneda": cfdi["moneda"],
        "TipoDeComprobante": "I",
        "Exportacion": "01",

        "LugarExpedicion": str(cfdi["cp_emisor"]),

        "MetodoPago": metodo_map[cfdi["metodo_pago"]],
        "FormaPago": forma_map[cfdi["forma_pago"]],

        "SubTotal": f"{subtotal:.2f}",
        "Descuento": f"{descuentos:.2f}",
        "Total": f"{total:.2f}",

        "Sello": cfdi["sello"]
    }

    root = Element("cfdi:Comprobante", comprobante_attrs)

    # =========================
    # EMISOR
    # =========================

    SubElement(root, "cfdi:Emisor", {
        "Nombre": cfdi["emisor"],
        "Rfc": cfdi["rfc_emisor"],
        "RegimenFiscal": "601"
    })

    # =========================
    # RECEPTOR
    # =========================

    SubElement(root, "cfdi:Receptor", {
        "Nombre": cfdi["receptor"],
        "Rfc": cfdi["rfc_receptor"],
        "DomicilioFiscalReceptor": str(cfdi["cp"]),
        "RegimenFiscalReceptor": "601",
        "UsoCFDI": "G01"
    })

    # =========================
    # CONCEPTOS
    # =========================

    conceptos_tag = SubElement(root, "cfdi:Conceptos")

    for concepto in cfdi["conceptos"]:

        concepto_tag = SubElement(conceptos_tag, "cfdi:Concepto", {
            "ClaveProdServ": (
                concepto["ClaveProdServ"]
                if concepto["ClaveProdServ"]
                else "01010101"
            ),

            "NoIdentificacion": concepto["Referencia"],

            "Cantidad": f'{float(concepto["Cantidad"]):.2f}',

            "ClaveUnidad": (
                concepto["ClaveUnidad"]
                if concepto["ClaveUnidad"]
                else "H87"
            ),

            "Unidad": concepto["Unidad"],

            "Descripcion": (
                concepto["Descripcion"]
                if concepto["Descripcion"]
                else concepto["Producto"]
            ),

            "ValorUnitario": (
                f'{float(concepto["ValorUnitario"]):.2f}'
            ),

            "Importe": (
                f'{float(concepto["Importe"]):.2f}'
            ),

            "Descuento": (
                f'{float(concepto["Importe"]) - float(concepto["Base"]):.2f}'
            ),

            "ObjetoImp": concepto["ObjetoImp"]
        })

        impuestos_tag = SubElement(
            concepto_tag,
            "cfdi:Impuestos"
        )

        traslados_tag = SubElement(
            impuestos_tag,
            "cfdi:Traslados"
        )

        SubElement(traslados_tag, "cfdi:Traslado", {
            "Base": f'{float(concepto["Base"]):.2f}',
            "Impuesto": "002",
            "TipoFactor": concepto["TipoFactor"],
            "TasaOCuota": f'{float(concepto["TasaOCuota"]):.6f}',
            "Importe": f'{float(concepto["ImporteImpuesto"]):.2f}'
        })

    # =========================
    # IMPUESTOS GLOBALES
    # =========================

    impuestos_root = SubElement(root, "cfdi:Impuestos", {
        "TotalImpuestosTrasladados": f"{impuestos:.2f}"
    })

    traslados_root = SubElement(
        impuestos_root,
        "cfdi:Traslados"
    )

    SubElement(traslados_root, "cfdi:Traslado", {
        "Base": f"{subtotal - descuentos:.2f}",
        "Impuesto": "002",
        "TipoFactor": "Tasa",
        "TasaOCuota": "0.160000",
        "Importe": f"{impuestos:.2f}"
    })

    # =========================
    # COMPLEMENTO TIMBRE
    # =========================

    complemento = SubElement(
        root,
        "cfdi:Complemento"
    )

    SubElement(complemento, "tfd:TimbreFiscalDigital", {
        "xmlns:tfd": NS_TFD,
        "Version": "1.1",
        "UUID": str(uuid.uuid4()).upper(),
        "FechaTimbrado": cfdi["fecha"],
        "RfcProvCertif": cfdi["rfc_emisor"]
    })

    xml_bytes = tostring(
        root,
        encoding="utf-8"
    )

    pretty_xml = minidom.parseString(
        xml_bytes
    ).toprettyxml(indent="    ")

    return pretty_xml