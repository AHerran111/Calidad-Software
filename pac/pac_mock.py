# services/pac_mock.py

from xml.etree import ElementTree as ET

CFDI_NS = "{http://www.sat.gob.mx/cfd/4}"

def timbrar_cfdi(xml_string):

    try:

        # =========================
        # PARSE XML
        # =========================
        root = ET.fromstring(xml_string)

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

            calculado = round(cantidad * valor, 2)

            if round(importe, 2) != calculado:
                raise Exception(
                    f"Importe incorrecto en concepto {i+1}"
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
        subtotal_xml = round(float(root.attrib["SubTotal"]), 2)
        total_xml = round(float(root.attrib["Total"]), 2)

        if subtotal_xml != round(total_conceptos, 2):
            raise Exception(
                "Subtotal no coincide con suma de conceptos"
            )

        if total_xml <= 0:
            raise Exception("Total invalido")

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

        xml_timbrado = xml_string.replace(
            "</cfdi:Comprobante>",
            complemento + "\n</cfdi:Comprobante>"
        )

        return xml_timbrado

    except ET.ParseError:
        raise Exception("XML mal formado")

    except Exception as e:
        raise Exception(f"PAC ERROR: {str(e)}")