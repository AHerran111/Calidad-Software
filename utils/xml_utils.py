# utils/xml_utils.py

from datetime import datetime
import uuid


def safe_float(value, default=0):
    try:
        return float(value)
    except:
        return default


def get_concepto_value(concepto, key, index_map=None, default=""):
    """
    Supports:
    - dict
    - list/tuple
    """

    if isinstance(concepto, dict):
        return concepto.get(key, default)

    if isinstance(concepto, (list, tuple)) and index_map:
        idx = index_map.get(key)

        if idx is not None and idx < len(concepto):
            return concepto[idx]

    return default


def dict_to_xml(cfdi):

    conceptos = cfdi.get("conceptos", [])

    conceptos_xml = ""

 

    # ONLY needed if concepto is LIST
    # Adjust indexes to your real structure
    index_map = {
        "Referencia": 0,
        "Descripcion": 1,
        "Cantidad": 2,
        "Precio": 3,
        "Importe": 4,
        "Impuesto": 5,
        "ImpuestoPct": 6,
        "Descuento": 7,
    }

    for c in conceptos:

        referencia = get_concepto_value(c, "Referencia", index_map, "")
        descripcion = get_concepto_value(c, "Descripcion", index_map, "")

        cantidad = safe_float(
            get_concepto_value(c, "Cantidad", index_map, 0)
        )

        precio = safe_float(
            get_concepto_value(c, "Precio", index_map, 0)
        )

        base = safe_float(
            get_concepto_value(c, "Importe", index_map, 0)
        )

        impuesto = safe_float(
            get_concepto_value(c, "Impuesto", index_map, 0)
        )

        descuento = safe_float(
            get_concepto_value(c, "Descuento", index_map, 0)
        )

        impuesto_pct = safe_float(
            get_concepto_value(c, "ImpuestoPct", index_map, 16)
        )

        conceptos_xml += f"""
        <cfdi:Concepto
            ClaveProdServ="01010101"
            NoIdentificacion="{referencia}"
            Cantidad="{cantidad:.2f}"
            ClaveUnidad="H87"
            Unidad="Pieza"
            Descripcion="{descripcion}"
            ValorUnitario="{precio:.2f}"
            Importe="{base:.2f}"
            Descuento="{descuento:.2f}"
            ObjetoImp="02">

            <cfdi:Impuestos>
                <cfdi:Traslados>
                    <cfdi:Traslado
                        Base="{base:.2f}"
                        Impuesto="002"
                        TipoFactor="Tasa"
                        TasaOCuota="{impuesto_pct / 100:.6f}"
                        Importe="{impuesto:.2f}"/>
                </cfdi:Traslados>
            </cfdi:Impuestos>

        </cfdi:Concepto>
        """
    subtotal = safe_float(cfdi.get("subtotal", 0))
    total_impuestos = safe_float(cfdi.get("impuestos_final", 0))
    total_descuentos = safe_float(cfdi.get("descuentos_final", 0))
    total = safe_float(cfdi.get("total_final", 0))
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>

<cfdi:Comprobante
    xmlns:cfdi="http://www.sat.gob.mx/cfd/4"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="
        http://www.sat.gob.mx/cfd/4
        http://www.sat.gob.mx/sitio_internet/cfd/4/cfdv40.xsd"
    Version="4.0"
    Serie="A"
    Folio="{uuid.uuid4().hex[:8]}"
    Fecha="{datetime.now().isoformat()}"
    Moneda="MXN"
    TipoDeComprobante="I"
    Exportacion="01"
    LugarExpedicion="{cfdi['cp_emisor']}"
    MetodoPago="{cfdi['metodo_pago'][:3]}"
    FormaPago="{cfdi['forma_pago'][:2]}"
    SubTotal="{subtotal:.2f}"
    Descuento="{total_descuentos:.2f}"
    Total="{total:.2f}">

    <cfdi:Emisor
        Nombre="{cfdi['emisor']}"
        Rfc="{cfdi['rfc_emisor']}"
        RegimenFiscal="{cfdi['regimen_emisor'][:3]}"/>

    <cfdi:Receptor
        Nombre="{cfdi['receptor']}"
        Rfc="{cfdi['rfc_receptor']}"
        DomicilioFiscalReceptor="{cfdi['cp']}"
        RegimenFiscalReceptor="{cfdi['regimen_receptor'][:3]}"
        UsoCFDI="{cfdi['uso_cfdi'][:3]}"/>

    <cfdi:Conceptos>

        {conceptos_xml}

    </cfdi:Conceptos>

    <cfdi:Impuestos TotalImpuestosTrasladados="{total_impuestos:.2f}">
        <cfdi:Traslados>
            <cfdi:Traslado
                Base="{subtotal:.2f}"
                Impuesto="002"
                TipoFactor="Tasa"
                TasaOCuota="0.160000"
                Importe="{total_impuestos:.2f}"/>
        </cfdi:Traslados>
    </cfdi:Impuestos>

</cfdi:Comprobante>
"""

    return xml