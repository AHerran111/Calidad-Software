# tests/py_test.py
"""
Pruebas unitarias – RFC App (CFDI 4.0)
Cobertura objetivo: ≥ 80 %

Dependencias de prueba:
    pip install pytest pytest-cov

Ejecución:
    pytest tests/py_test.py -v --cov=services --cov=utils --cov-report=term-missing
"""

import base64
from datetime import datetime
from xml.etree import ElementTree as ET

import pytest

# ---------------------------------------------------------------------------
# XML de referencia real (timbrado) usado como base para los tests
# ---------------------------------------------------------------------------

NS_CFDI = "{http://www.sat.gob.mx/cfd/4}"
NS_TFD = "{http://www.sat.gob.mx/TimbreFiscalDigital}"

SELLO_REAL = (
    "SU1QT1JUQUNJT05FUyBERUwgUEFDSUZJQ09IT0xESU5HIEVNUFJFU0FSSUFMIERFTCBOT1JURTE"
    "xNi4wMjAyNi0wNS0xNFQyMTo0NTo0MC43MDUwMzc="
)

XML_TIMBRADO_REAL = f"""<?xml version="1.0" ?>
<cfdi:Comprobante
    xmlns:cfdi="http://www.sat.gob.mx/cfd/4"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.sat.gob.mx/cfd/4 http://www.sat.gob.mx/sitio_internet/cfd/4/cfdv40.xsd"
    Version="4.0"
    Serie="A"
    Folio="470a5c97"
    Fecha="2026-05-14T21:45:40.705037"
    Moneda="MXN"
    TipoDeComprobante="I"
    Exportacion="01"
    LugarExpedicion="82000"
    MetodoPago="PUE"
    FormaPago="01"
    SubTotal="100.00"
    Descuento="0.00"
    Total="116.00"
    Sello="{SELLO_REAL}">
  <cfdi:Emisor Nombre="IMPORTACIONES DEL PACIFICO" Rfc="GGG010101GGG" RegimenFiscal="601"/>
  <cfdi:Receptor Nombre="HOLDING EMPRESARIAL DEL NORTE" Rfc="MMM010101MMM"
      DomicilioFiscalReceptor="64610" RegimenFiscalReceptor="601" UsoCFDI="G01"/>
  <cfdi:Conceptos>
    <cfdi:Concepto
        ClaveProdServ="01010101"
        NoIdentificacion=""
        Cantidad="10.00"
        ClaveUnidad="H87"
        Unidad="1"
        Descripcion="1"
        ValorUnitario="10.00"
        Importe="100.00"
        Descuento="0.00"
        ObjetoImp="02">
      <cfdi:Impuestos>
        <cfdi:Traslados>
          <cfdi:Traslado Base="100.00" Impuesto="002" TipoFactor="Tasa"
              TasaOCuota="0.160000" Importe="16.00"/>
        </cfdi:Traslados>
      </cfdi:Impuestos>
    </cfdi:Concepto>
  </cfdi:Conceptos>
  <cfdi:Impuestos TotalImpuestosTrasladados="16.00">
    <cfdi:Traslados>
      <cfdi:Traslado Base="100.00" Impuesto="002" TipoFactor="Tasa"
          TasaOCuota="0.160000" Importe="16.00"/>
    </cfdi:Traslados>
  </cfdi:Impuestos>
  <cfdi:Complemento>
    <tfd:TimbreFiscalDigital
        xmlns:tfd="http://www.sat.gob.mx/TimbreFiscalDigital"
        Version="1.1"
        UUID="68F9774D-AEE5-463F-AAB8-7A26DB35B421"
        FechaTimbrado="2026-05-14T21:45:40.705037"
        RfcProvCertif="GGG010101GGG"/>
  </cfdi:Complemento>
</cfdi:Comprobante>"""

# ---------------------------------------------------------------------------
# Datos de prueba alineados con el XML real
# ---------------------------------------------------------------------------

CONCEPTO_BASE = {
    "Producto": "1",
    "Referencia": "",
    "ClaveProdServ": "01010101",
    "ClaveUnidad": "H87",
    "Unidad": "1",
    "Precio": 10.00,
    "Cantidad": 10.00,
    "ValorUnitario": 10.00,
    "Importe": 100.00,
    "Impuesto": 0.00,
    "Descuento": 0.00,
    "ObjetoImp": "02",
    "Base": 100.00,
    "TipoFactor": "Tasa",
    "TasaOCuota": 0.160000,
    "ImporteImpuesto": 16.00,
    "Descripcion": "1",
    "Total": 116.00,
}

DATA_BASE = {
    "emisor": "IMPORTACIONES DEL PACIFICO",
    "rfc_emisor": "GGG010101GGG",
    "regimen_emisor": "601",
    "cp_emisor": "82000",
    "direccion_emisor": "Av. del Puerto 100",
    "receptor": "HOLDING EMPRESARIAL DEL NORTE",
    "rfc_receptor": "MMM010101MMM",
    "regimen_receptor": "601",
    "uso_cfdi": "G01 Adquisición de mercancias",
    "cp": "64610",
    "subtotal": 100.00,
    "impuestos_final": 16.00,
    "descuentos_final": 0.00,
    "total_final": 116.00,
    "forma_pago": "01 EFECTIVO",
    "metodo_pago": "Pago En Una Sola Exhibición (PUE)",
    "moneda": "MXN",
    "tipo_cambio": 1.0,
    "fecha": "2026-05-14T21:45:40.705037",
    "conceptos": [CONCEPTO_BASE],
}


# ---------------------------------------------------------------------------
# 1. services/cfdi_generator.py
# ---------------------------------------------------------------------------

class TestGenerarCfdi:

    def _make_data(self, **overrides):
        return {**DATA_BASE, **overrides}

    def test_retorna_dict(self):
        from services.cfdi_generator import generar_cfdi
        assert isinstance(generar_cfdi(self._make_data()), dict)

    def test_rfc_emisor_correcto(self):
        from services.cfdi_generator import generar_cfdi
        cfdi = generar_cfdi(self._make_data())
        assert cfdi["rfc_emisor"] == "GGG010101GGG"

    def test_nombre_emisor_correcto(self):
        from services.cfdi_generator import generar_cfdi
        cfdi = generar_cfdi(self._make_data())
        assert cfdi["emisor"] == "IMPORTACIONES DEL PACIFICO"

    def test_rfc_receptor_correcto(self):
        from services.cfdi_generator import generar_cfdi
        cfdi = generar_cfdi(self._make_data())
        assert cfdi["rfc_receptor"] == "MMM010101MMM"

    def test_nombre_receptor_correcto(self):
        from services.cfdi_generator import generar_cfdi
        cfdi = generar_cfdi(self._make_data())
        assert cfdi["receptor"] == "HOLDING EMPRESARIAL DEL NORTE"

    def test_subtotal_100(self):
        from services.cfdi_generator import generar_cfdi
        cfdi = generar_cfdi(self._make_data())
        assert cfdi["subtotal"] == 100.00

    def test_impuestos_16(self):
        from services.cfdi_generator import generar_cfdi
        cfdi = generar_cfdi(self._make_data())
        assert cfdi["impuestos_final"] == 16.00

    def test_total_116(self):
        from services.cfdi_generator import generar_cfdi
        cfdi = generar_cfdi(self._make_data())
        assert cfdi["total_final"] == 116.00

    def test_descuento_cero(self):
        from services.cfdi_generator import generar_cfdi
        cfdi = generar_cfdi(self._make_data())
        assert cfdi["descuentos_final"] == 0.00

    def test_moneda_mxn(self):
        from services.cfdi_generator import generar_cfdi
        cfdi = generar_cfdi(self._make_data())
        assert cfdi["moneda"] == "MXN"

    def test_metodo_pago_pue(self):
        from services.cfdi_generator import generar_cfdi
        cfdi = generar_cfdi(self._make_data())
        assert "PUE" in cfdi["metodo_pago"]

    def test_concepto_cantidad_10(self):
        from services.cfdi_generator import generar_cfdi
        cfdi = generar_cfdi(self._make_data())
        assert cfdi["conceptos"][0]["Cantidad"] == 10.00

    def test_concepto_valor_unitario_10(self):
        from services.cfdi_generator import generar_cfdi
        cfdi = generar_cfdi(self._make_data())
        assert cfdi["conceptos"][0]["ValorUnitario"] == 10.00

    def test_concepto_importe_100(self):
        from services.cfdi_generator import generar_cfdi
        cfdi = generar_cfdi(self._make_data())
        assert cfdi["conceptos"][0]["Importe"] == 100.00

    def test_concepto_impuesto_iva_16(self):
        from services.cfdi_generator import generar_cfdi
        cfdi = generar_cfdi(self._make_data())
        assert cfdi["conceptos"][0]["ImporteImpuesto"] == 16.00

    def test_fecha_default_cuando_no_viene(self):
        from services.cfdi_generator import generar_cfdi

        data = self._make_data()
        data.pop("fecha")

        cfdi = generar_cfdi(data)

        datetime.fromisoformat(cfdi["fecha"])

    def test_multiples_conceptos(self):
        from services.cfdi_generator import generar_cfdi

        concepto2 = {
            **CONCEPTO_BASE,
            "Producto": "Extra",
            "Importe": 50.00
        }

        cfdi = generar_cfdi(
            self._make_data(conceptos=[CONCEPTO_BASE, concepto2])
        )

        assert len(cfdi["conceptos"]) == 2


# ---------------------------------------------------------------------------
# 2. services/signer_mock.py
# ---------------------------------------------------------------------------

class TestSellarCfdi:

    def _cfdi(self):
        from services.cfdi_generator import generar_cfdi
        return generar_cfdi(DATA_BASE)

    def test_agrega_campo_sello(self):
        from services.signer_mock import sellar_cfdi

        resultado = sellar_cfdi(self._cfdi())

        assert "sello" in resultado

    def test_sello_es_base64_valido(self):
        from services.signer_mock import sellar_cfdi

        sello = sellar_cfdi(self._cfdi())["sello"]

        decoded = base64.b64decode(sello).decode("utf-8")

        assert len(decoded) > 0

    def test_sello_contiene_nombre_emisor(self):
        from services.signer_mock import sellar_cfdi

        resultado = sellar_cfdi(self._cfdi())

        decoded = base64.b64decode(
            resultado["sello"]
        ).decode("utf-8")

        assert "IMPORTACIONES DEL PACIFICO" in decoded

    def test_sello_contiene_receptor(self):
        from services.signer_mock import sellar_cfdi

        resultado = sellar_cfdi(self._cfdi())

        decoded = base64.b64decode(
            resultado["sello"]
        ).decode("utf-8")

        assert "HOLDING EMPRESARIAL DEL NORTE" in decoded

    def test_sello_contiene_total(self):
        from services.signer_mock import sellar_cfdi

        resultado = sellar_cfdi(self._cfdi())

        decoded = base64.b64decode(
            resultado["sello"]
        ).decode("utf-8")

        assert "116.0" in decoded

    def test_sello_contiene_fecha(self):
        from services.signer_mock import sellar_cfdi

        resultado = sellar_cfdi(self._cfdi())

        decoded = base64.b64decode(
            resultado["sello"]
        ).decode("utf-8")

        assert "2026-05-14" in decoded

    def test_retorna_mismo_cfdi(self):
        from services.signer_mock import sellar_cfdi

        cfdi = self._cfdi()

        resultado = sellar_cfdi(cfdi)

        assert resultado["total_final"] == 116.00
        assert resultado["emisor"] == "IMPORTACIONES DEL PACIFICO"

    def test_sello_distinto_para_distintos_emisores(self):
        from services.cfdi_generator import generar_cfdi
        from services.signer_mock import sellar_cfdi

        cfdi_a = generar_cfdi({
            **DATA_BASE,
            "emisor": "EMISOR A",
        })

        cfdi_b = generar_cfdi({
            **DATA_BASE,
            "emisor": "EMISOR B",
        })

        sello_a = sellar_cfdi(cfdi_a)["sello"]
        sello_b = sellar_cfdi(cfdi_b)["sello"]

        assert sello_a != sello_b


# ---------------------------------------------------------------------------
# 3. utils/xml_utils.py
# ---------------------------------------------------------------------------

class TestDictToXml:

    def _cfdi_sellado(self, **overrides):
        from services.cfdi_generator import generar_cfdi
        from services.signer_mock import sellar_cfdi

        return sellar_cfdi(generar_cfdi({**DATA_BASE, **overrides}))

    def _root(self, **overrides):
        from utils.xml_utils import dict_to_xml

        return ET.fromstring(
            dict_to_xml(self._cfdi_sellado(**overrides)).encode()
        )

    def test_retorna_string_con_declaracion_xml(self):
        from utils.xml_utils import dict_to_xml

        xml = dict_to_xml(self._cfdi_sellado())

        assert isinstance(xml, str)
        assert "<?xml" in xml

    def test_nodo_raiz_es_comprobante(self):
        assert "Comprobante" in self._root().tag

    def test_version_4_0(self):
        assert self._root().attrib["Version"] == "4.0"

    def test_moneda_mxn(self):
        assert self._root().attrib["Moneda"] == "MXN"

    def test_subtotal_100(self):
        assert float(self._root().attrib["SubTotal"]) == pytest.approx(100.00)

    def test_descuento_0(self):
        assert float(self._root().attrib["Descuento"]) == pytest.approx(0.00)

    def test_total_116(self):
        assert float(self._root().attrib["Total"]) == pytest.approx(116.00)

    def test_metodo_pago_pue(self):
        assert self._root().attrib["MetodoPago"] == "PUE"

    def test_forma_pago_01(self):
        assert self._root().attrib["FormaPago"] == "01"

    def test_lugar_expedicion_82000(self):
        assert self._root().attrib["LugarExpedicion"] == "82000"

    def test_emisor_rfc_correcto(self):
        emisor = self._root().find(f"{NS_CFDI}Emisor")

        assert emisor is not None
        assert emisor.attrib["Rfc"] == "GGG010101GGG"

    def test_emisor_nombre_correcto(self):
        emisor = self._root().find(f"{NS_CFDI}Emisor")

        assert emisor.attrib["Nombre"] == "IMPORTACIONES DEL PACIFICO"

    def test_receptor_rfc_correcto(self):
        receptor = self._root().find(f"{NS_CFDI}Receptor")

        assert receptor is not None
        assert receptor.attrib["Rfc"] == "MMM010101MMM"

    def test_receptor_domicilio_fiscal(self):
        receptor = self._root().find(f"{NS_CFDI}Receptor")

        assert receptor.attrib["DomicilioFiscalReceptor"] == "64610"

    def test_receptor_uso_cfdi_g01(self):
        receptor = self._root().find(f"{NS_CFDI}Receptor")

        assert receptor.attrib["UsoCFDI"] == "G01"

    def test_concepto_cantidad_10(self):
        conceptos = self._root().find(f"{NS_CFDI}Conceptos")
        concepto = conceptos.find(f"{NS_CFDI}Concepto")

        assert float(concepto.attrib["Cantidad"]) == pytest.approx(10.00)

    def test_concepto_valor_unitario_10(self):
        conceptos = self._root().find(f"{NS_CFDI}Conceptos")
        concepto = conceptos.find(f"{NS_CFDI}Concepto")

        assert float(concepto.attrib["ValorUnitario"]) == pytest.approx(10.00)

    def test_concepto_importe_100(self):
        conceptos = self._root().find(f"{NS_CFDI}Conceptos")
        concepto = conceptos.find(f"{NS_CFDI}Concepto")

        assert float(concepto.attrib["Importe"]) == pytest.approx(100.00)

    def test_traslado_iva_16(self):
        conceptos = self._root().find(f"{NS_CFDI}Conceptos")
        concepto = conceptos.find(f"{NS_CFDI}Concepto")

        traslado = concepto.find(f".//{NS_CFDI}Traslado")

        assert float(traslado.attrib["Importe"]) == pytest.approx(16.00)
        assert traslado.attrib["TasaOCuota"] == "0.160000"
        assert traslado.attrib["Impuesto"] == "002"

    def test_impuestos_globales_total_16(self):
        impuestos = self._root().find(f"{NS_CFDI}Impuestos")

        assert impuestos is not None
        assert float(impuestos.attrib["TotalImpuestosTrasladados"]) == pytest.approx(16.00)

    def test_complemento_tfd_presente(self):
        complemento = self._root().find(f"{NS_CFDI}Complemento")

        assert complemento is not None

        tfd = complemento.find(f"{NS_TFD}TimbreFiscalDigital")

        assert tfd is not None
        assert tfd.attrib["Version"] == "1.1"

    def test_xml_parseable(self):
        from utils.xml_utils import dict_to_xml

        ET.fromstring(dict_to_xml(self._cfdi_sellado()).encode())

    def test_ppd_forma_99_mapeados(self):
        root = self._root(
            metodo_pago="Pago en Parcialidades o Diferido (PPD)",
            forma_pago="99 POR DEFINIR",
        )

        assert root.attrib["MetodoPago"] == "PPD"
        assert root.attrib["FormaPago"] == "99"