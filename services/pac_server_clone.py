from fastapi import FastAPI, Request
from fastapi.responses import Response
from lxml import etree
from xml.etree import ElementTree as ET
import psycopg2

DB_CONFIG  = {
    "host": "165.245.152.114",
    "dbname": "facts",
    "user": "facts",
    "password": "admin123",
    "port" : "5432"
}

CFDI_NS = "{http://www.sat.gob.mx/cfd/4}"

app = FastAPI()

def upload_data(root, xml):

    sello = root.attrib.get("Sello")
    total = root.attrib.get("Total")
    fecha = root.attrib.get("Fecha")

    emisor = root.find(f"{CFDI_NS}Emisor")
    receptor = root.find(f"{CFDI_NS}Receptor")

    if emisor is None:
        raise Exception("Emisor not found")

    if receptor is None:
        raise Exception("Receptor not found")

    rfc_emisor = emisor.attrib.get("Rfc")
    rfc_receptor = receptor.attrib.get("Rfc")

    estado = "TIMBRADO"

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    query = """
        INSERT INTO fact_schema.facturas (
            "SELLO",
            "RFC_EMISOR",
            "RFC_RECEPTOR",
            "TOTAL",
            "FECHA",
            "XML",
            "ESTADO"
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """

    try:

        cur.execute(
            query,
            (
                sello,
                rfc_emisor,
                rfc_receptor,
                total,
                fecha,
                xml,
                estado
            )
        )

        conn.commit()

    except Exception as e:

        conn.rollback()
        raise Exception(f"POSTGRES error: {e}")

    finally:

        cur.close()
        conn.close()




@app.get("/get-message")
async def read_root():
    return {"Message":"Success"}

@app.post("/test")
async def timbrar_cfdi(request: Request):

    print("ROUTE ENTERED")

    body = await request.body()

    print(body.decode("utf-8"))

    return {
        "ok": True
    }

@app.post("/process_xml")
async def timbrar_cfdi(request: Request):

    print(f"obtaining request...\nclient ip{request.client.host}\nclient port{request.client.port}\nheaders\n{request.headers}")
    xml = await request.body()
    xml = xml.decode("utf-8")


    try:

        # =========================
        # PARSE XML
        # =========================
        root = ET.fromstring(xml)
        #print(xml)
        # =========================
        # VALIDAR ROOT
        # =========================
        if root.tag != f"{CFDI_NS}Comprobante":
            raise Exception("Nodo Comprobante invalido")

        # =========================
        # ATRIBUTOS OBLIGATORIOS CFDI
        # =========================
        required_attrs = [
            "Version",
            "Fecha",
            "Moneda",
            "TipoDeComprobante",
            "LugarExpedicion",
            "SubTotal",
            "Total"
        ]

        for attr in required_attrs:
            if not root.attrib.get(attr):
                raise Exception(f"Atributo faltante en Comprobante: {attr}")

        # =========================
        # VALIDAR EMISOR
        # =========================
        emisor = root.find(f"{CFDI_NS}Emisor")

        if emisor is None:
            raise Exception("Nodo Emisor faltante")

        emisor_required = [
            "Nombre",
            "Rfc",
            "RegimenFiscal"
        ]

        for attr in emisor_required:
            if not emisor.attrib.get(attr):
                raise Exception(f"Emisor sin atributo: {attr}")

        # =========================
        # VALIDAR RECEPTOR
        # =========================
        receptor = root.find(f"{CFDI_NS}Receptor")

        if receptor is None:
            raise Exception("Nodo Receptor faltante")

        receptor_required = [
            "Nombre",
            "Rfc",
            "DomicilioFiscalReceptor",
            "RegimenFiscalReceptor",
            "UsoCFDI"
        ]

        for attr in receptor_required:
            if not receptor.attrib.get(attr):
                raise Exception(f"Receptor sin atributo: {attr}")

        # =========================
        # VALIDAR CONCEPTOS
        # =========================
        conceptos = root.find(f"{CFDI_NS}Conceptos")

        if conceptos is None:
            raise Exception("Nodo Conceptos faltante")

        conceptos_list = conceptos.findall(f"{CFDI_NS}Concepto")

        if len(conceptos_list) == 0:
            raise Exception("Debe existir al menos un concepto")

        total_conceptos = 0

        for i, concepto in enumerate(conceptos_list):

            concepto_required = [
                "Cantidad",
                "Descripcion",
                "ValorUnitario",
                "Importe"
            ]

            for attr in concepto_required:
                if not concepto.attrib.get(attr):
                    raise Exception(
                        f"Concepto {i+1} sin atributo: {attr}"
                    )

            cantidad = float(concepto.attrib["Cantidad"])
            valor = float(concepto.attrib["ValorUnitario"])
            importe = float(concepto.attrib["Importe"])

            if importe < 0:
                raise Exception(
                    f"Importe inválido en concepto {i+1}"
                )

            total_conceptos += importe

            # =========================
            # VALIDAR IMPUESTOS CONCEPTO
            # =========================
            impuestos = concepto.find(f"{CFDI_NS}Impuestos")

            if impuestos is not None:

                traslados = impuestos.find(f"{CFDI_NS}Traslados")

                if traslados is not None:

                    traslado = traslados.find(f"{CFDI_NS}Traslado")

                    if traslado is not None:

                        traslado_required = [
                            "Base",
                            "Impuesto",
                            "TipoFactor",
                            "TasaOCuota",
                            "Importe"
                        ]

                        for attr in traslado_required:
                            if not traslado.attrib.get(attr):
                                raise Exception(
                                    f"Traslado incompleto en concepto {i+1}"
                                )

        # =========================
        # VALIDAR TOTALES
        # =========================
        subtotal_xml = round(
            float(root.attrib["SubTotal"]),
            2
        )

        total_xml = round(
            float(root.attrib["Total"]),
            2
        )

        descuento_xml = round(
            float(root.attrib.get("Descuento", 0)),
            2
        )

        if subtotal_xml != round(total_conceptos, 2):
            raise Exception(
                f"SubTotal {subtotal_xml} no coincide con suma de conceptos {round(total_conceptos, 2)}"
            )

        if total_xml <= 0:
            raise Exception(
                "Total invalido"
            )

        calculado_total = round(
            subtotal_xml - descuento_xml,
            2
        )

        if total_xml < calculado_total:
            raise Exception(
                "Total menor al calculado"
            )

        # =========================
        # VALIDAR IMPUESTOS GLOBALES
        # =========================
        impuestos_global = root.find(f"{CFDI_NS}Impuestos")

        if impuestos_global is None:
            raise Exception("Nodo Impuestos faltante")

        if not impuestos_global.attrib.get(
            "TotalImpuestosTrasladados"
        ):
            raise Exception(
                "Falta TotalImpuestosTrasladados"
            )

        # =========================
        # SIMULAR TIMBRADO
        # =========================
        complemento = """
        <cfdi:Complemento xmlns:tfd="http://www.sat.gob.mx/TimbreFiscalDigital">
            <tfd:TimbreFiscalDigital
                Version="1.1"
                UUID="12345678-1234-1234-1234-123456789ABC"
                FechaTimbrado="2025-01-01T12:00:00"
                RfcProvCertif="AAA010101AAA"/>
        </cfdi:Complemento>
        """

        xml_timbrado = xml.replace(
            "</cfdi:Comprobante>",
            complemento + "\n</cfdi:Comprobante>"
        )

        try:
            upload_data(root,xml)
        except Exception as e:
            return Response(content=f"PAC ERORR: {e}", status_code=500)

        return Response(content=xml_timbrado, media_type="application/xml")

    except ET.ParseError:
        return Response(content=f"Invalid XML format", status_code=400)

    except Exception as e:
        return Response(content=f"PAC ERORR: {e}", status_code=500)

