# tests/py_test.py
"""
Pruebas unitarias – RFC App (CFDI 4.0)
Cobertura objetivo: ≥ 80 %

Dependencias de prueba:
    pip install pytest pytest-cov psycopg2-binary

Ejecución:
    pytest tests/py_test.py -v --cov=services --cov=utils --cov-report=term-missing
"""

import base64
import uuid
from datetime import datetime
from unittest.mock import patch
from xml.etree import ElementTree as ET

import psycopg2
import pytest

# ---------------------------------------------------------------------------
# XML de referencia real (timbrado) usado como base para los tests
# ---------------------------------------------------------------------------

NS_CFDI = "{http://www.sat.gob.mx/cfd/4}"
NS_TFD  = "{http://www.sat.gob.mx/TimbreFiscalDigital}"

TEST_PREFIX = "TEST_"

# Sello real del XML de referencia
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


def _new_sello():
    """Sello único con prefijo TEST_ para cada prueba."""
    return f"{TEST_PREFIX}{uuid.uuid4().hex[:12].upper()}"


def _xml_test(sello=None):
    """
    Devuelve el XML real de referencia con un sello sustituido por uno de prueba,
    para poder insertarlo en la BD sin colisionar con datos reales.
    """
    s = sello or _new_sello()
    return XML_TIMBRADO_REAL.replace(SELLO_REAL, s)


# ---------------------------------------------------------------------------
# Fixture de conexión: nueva conexión por test, rollback al terminar.
# ---------------------------------------------------------------------------

@pytest.fixture()
def db():
    """
    Conecta a la BD real usando DB_CONFIG de utils.database.
    Envuelve cada test en una transacción y hace ROLLBACK al terminar,
    dejando la BD sin datos de prueba.
    Si la BD no está disponible el test se marca como skipped.
    """
    try:
        from utils.database import DB_CONFIG
        conn = psycopg2.connect(**DB_CONFIG)
    except Exception:
        pytest.skip("Base de datos no disponible")

    conn.autocommit = False
    yield conn
    conn.rollback()
    conn.close()


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
        concepto2 = {**CONCEPTO_BASE, "Producto": "Extra", "Importe": 50.00}
        cfdi = generar_cfdi(self._make_data(conceptos=[CONCEPTO_BASE, concepto2]))
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
        assert "sello" in sellar_cfdi(self._cfdi())

    def test_sello_es_base64_valido(self):
        from services.signer_mock import sellar_cfdi
        sello = sellar_cfdi(self._cfdi())["sello"]
        decoded = base64.b64decode(sello).decode()
        assert len(decoded) > 0

    def test_sello_contiene_rfc_emisor(self):
        from services.signer_mock import sellar_cfdi
        resultado = sellar_cfdi(self._cfdi())
        decoded = base64.b64decode(resultado["sello"]).decode()
        assert "GGG010101GGG" in decoded

    def test_sello_contiene_receptor(self):
        from services.signer_mock import sellar_cfdi
        resultado = sellar_cfdi(self._cfdi())
        decoded = base64.b64decode(resultado["sello"]).decode()
        assert "HOLDING EMPRESARIAL DEL NORTE" in decoded

    def test_sello_contiene_total(self):
        from services.signer_mock import sellar_cfdi
        resultado = sellar_cfdi(self._cfdi())
        decoded = base64.b64decode(resultado["sello"]).decode()
        assert "116.0" in decoded

    def test_sello_contiene_fecha(self):
        from services.signer_mock import sellar_cfdi
        resultado = sellar_cfdi(self._cfdi())
        decoded = base64.b64decode(resultado["sello"]).decode()
        assert "2026-05-14" in decoded

    def test_retorna_mismo_cfdi(self):
        from services.signer_mock import sellar_cfdi
        cfdi = self._cfdi()
        resultado = sellar_cfdi(cfdi)
        assert resultado["rfc_emisor"] == "GGG010101GGG"
        assert resultado["total_final"] == 116.00

    def test_sello_distinto_para_distintos_emisores(self):
        from services.cfdi_generator import generar_cfdi
        from services.signer_mock import sellar_cfdi
        cfdi_a = generar_cfdi({**DATA_BASE, "emisor": "EMISOR A"})
        cfdi_b = generar_cfdi({**DATA_BASE, "emisor": "EMISOR B"})
        assert sellar_cfdi(cfdi_a)["sello"] != sellar_cfdi(cfdi_b)["sello"]


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
        return ET.fromstring(dict_to_xml(self._cfdi_sellado(**overrides)).encode())

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


# ---------------------------------------------------------------------------
# 4. utils/database.py – BD real, rollback al terminar cada test.
# Todos los registros usan el XML real con sello sustituido por TEST_...
# ---------------------------------------------------------------------------

class TestInsercionEmisor:

    def test_insertar_emisor_exitoso(self, db):
        from utils.database import insertar_emisor
        rfc = f"TEST{uuid.uuid4().hex[:9].upper()}"
        insertar_emisor(db, rfc, "IMPORTACIONES DEL PACIFICO", "601", "82000", "Av. del Puerto 100")
        cur = db.cursor()
        cur.execute("SELECT rfc FROM fact_schema.emisores WHERE rfc = %s", (rfc,))
        assert cur.fetchone() is not None
        cur.close()

    def test_insertar_emisor_duplicado_lanza_error(self, db):
        from utils.database import insertar_emisor
        rfc = f"TEST{uuid.uuid4().hex[:9].upper()}"
        insertar_emisor(db, rfc, "IMPORTACIONES DEL PACIFICO", "601", "82000", "Av. del Puerto 100")
        with pytest.raises(Exception):
            insertar_emisor(db, rfc, "IMPORTACIONES DEL PACIFICO", "601", "82000", "Av. del Puerto 100")
        db.rollback()


class TestInsercionReceptor:

    def test_insertar_receptor_exitoso(self, db):
        from utils.database import insertar_receptor
        rfc = f"TEST{uuid.uuid4().hex[:9].upper()}"
        insertar_receptor(db, rfc, "HOLDING EMPRESARIAL DEL NORTE", "601", "64610")
        cur = db.cursor()
        cur.execute("SELECT rfc FROM fact_schema.receptores WHERE rfc = %s", (rfc,))
        assert cur.fetchone() is not None
        cur.close()


class TestGuardarFactura:

    def test_guardar_factura_inserta_registro(self, db):
        from utils.database import guardar_factura
        sello = _new_sello()
        xml = _xml_test(sello=sello)
        with patch("utils.database.get_connection", return_value=db), \
             patch("psycopg2.connect", return_value=db):
            guardar_factura(xml)
        cur = db.cursor()
        cur.execute('SELECT "SELLO" FROM fact_schema.facturas WHERE "SELLO" = %s', (sello,))
        assert cur.fetchone() is not None
        cur.close()

    def test_guardar_factura_estado_pendiente(self, db):
        from utils.database import guardar_factura
        sello = _new_sello()
        xml = _xml_test(sello=sello)
        with patch("utils.database.get_connection", return_value=db), \
             patch("psycopg2.connect", return_value=db):
            guardar_factura(xml)
        cur = db.cursor()
        cur.execute('SELECT "ESTADO" FROM fact_schema.facturas WHERE "SELLO" = %s', (sello,))
        assert cur.fetchone()[0] == "PENDIENTE"
        cur.close()

    def test_guardar_factura_rfc_emisor_correcto(self, db):
        from utils.database import guardar_factura
        sello = _new_sello()
        xml = _xml_test(sello=sello)
        with patch("utils.database.get_connection", return_value=db), \
             patch("psycopg2.connect", return_value=db):
            guardar_factura(xml)
        cur = db.cursor()
        cur.execute('SELECT "RFC_EMISOR" FROM fact_schema.facturas WHERE "SELLO" = %s', (sello,))
        assert cur.fetchone()[0] == "GGG010101GGG"
        cur.close()

    def test_guardar_factura_rfc_receptor_correcto(self, db):
        from utils.database import guardar_factura
        sello = _new_sello()
        xml = _xml_test(sello=sello)
        with patch("utils.database.get_connection", return_value=db), \
             patch("psycopg2.connect", return_value=db):
            guardar_factura(xml)
        cur = db.cursor()
        cur.execute('SELECT "RFC_RECEPTOR" FROM fact_schema.facturas WHERE "SELLO" = %s', (sello,))
        assert cur.fetchone()[0] == "MMM010101MMM"
        cur.close()

    def test_guardar_factura_total_correcto(self, db):
        from utils.database import guardar_factura
        sello = _new_sello()
        xml = _xml_test(sello=sello)
        with patch("utils.database.get_connection", return_value=db), \
             patch("psycopg2.connect", return_value=db):
            guardar_factura(xml)
        cur = db.cursor()
        cur.execute('SELECT "TOTAL" FROM fact_schema.facturas WHERE "SELLO" = %s', (sello,))
        assert float(cur.fetchone()[0]) == pytest.approx(116.00)
        cur.close()


class TestObtenerPendientes:

    def _insertar(self, conn, sello, estado="PENDIENTE"):
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO fact_schema.facturas
                ("SELLO","RFC_EMISOR","RFC_RECEPTOR","TOTAL","FECHA","XML","ESTADO")
            VALUES (%s,%s,%s,%s,%s,%s,%s)
        """, (sello, "GGG010101GGG", "MMM010101MMM", 116.00,
              "2026-05-14 21:45:40", _xml_test(sello), estado))
        conn.commit()
        cur.close()

    def test_retorna_solo_pendientes(self, db):
        from utils.database import obtener_pendientes
        sello_pend = _new_sello()
        sello_timb = _new_sello()
        self._insertar(db, sello_pend, "PENDIENTE")
        self._insertar(db, sello_timb, "TIMBRADO")
        rows = obtener_pendientes(db)
        sellos = [r[0] for r in rows]
        assert sello_pend in sellos
        assert sello_timb not in sellos

    def test_timbrado_no_aparece_en_pendientes(self, db):
        from utils.database import obtener_pendientes
        sello_timb = _new_sello()
        self._insertar(db, sello_timb, "TIMBRADO")
        rows = obtener_pendientes(db)
        sellos = [r[0] for r in rows]
        assert sello_timb not in sellos

    def test_pendiente_tiene_6_columnas(self, db):
        from utils.database import obtener_pendientes
        sello = _new_sello()
        self._insertar(db, sello, "PENDIENTE")
        rows = obtener_pendientes(db)
        fila = next(r for r in rows if r[0] == sello)
        # SELLO, RFC_EMISOR, RFC_RECEPTOR, TOTAL, FECHA, ESTADO
        assert len(fila) == 6

    def test_pendiente_rfc_emisor_correcto(self, db):
        from utils.database import obtener_pendientes
        sello = _new_sello()
        self._insertar(db, sello, "PENDIENTE")
        rows = obtener_pendientes(db)
        fila = next(r for r in rows if r[0] == sello)
        assert fila[1] == "GGG010101GGG"

    def test_pendiente_rfc_receptor_correcto(self, db):
        from utils.database import obtener_pendientes
        sello = _new_sello()
        self._insertar(db, sello, "PENDIENTE")
        rows = obtener_pendientes(db)
        fila = next(r for r in rows if r[0] == sello)
        assert fila[2] == "MMM010101MMM"


class TestObtenerXml:

    def test_obtiene_xml_y_contiene_comprobante(self, db):
        from utils.database import obtener_xml
        sello = _new_sello()
        cur = db.cursor()
        cur.execute("""
            INSERT INTO fact_schema.facturas
                ("SELLO","RFC_EMISOR","RFC_RECEPTOR","TOTAL","FECHA","XML","ESTADO")
            VALUES (%s,%s,%s,%s,%s,%s,%s)
        """, (sello, "GGG010101GGG", "MMM010101MMM", 116.00,
              "2026-05-14 21:45:40", _xml_test(sello), "PENDIENTE"))
        db.commit()
        cur.close()
        xml = obtener_xml(db, sello)
        assert "Comprobante" in xml

    def test_xml_recuperado_tiene_rfc_emisor(self, db):
        from utils.database import obtener_xml
        sello = _new_sello()
        cur = db.cursor()
        cur.execute("""
            INSERT INTO fact_schema.facturas
                ("SELLO","RFC_EMISOR","RFC_RECEPTOR","TOTAL","FECHA","XML","ESTADO")
            VALUES (%s,%s,%s,%s,%s,%s,%s)
        """, (sello, "GGG010101GGG", "MMM010101MMM", 116.00,
              "2026-05-14 21:45:40", _xml_test(sello), "PENDIENTE"))
        db.commit()
        cur.close()
        xml = obtener_xml(db, sello)
        assert "GGG010101GGG" in xml

    def test_xml_recuperado_tiene_uuid_tfd(self, db):
        from utils.database import obtener_xml
        sello = _new_sello()
        cur = db.cursor()
        cur.execute("""
            INSERT INTO fact_schema.facturas
                ("SELLO","RFC_EMISOR","RFC_RECEPTOR","TOTAL","FECHA","XML","ESTADO")
            VALUES (%s,%s,%s,%s,%s,%s,%s)
        """, (sello, "GGG010101GGG", "MMM010101MMM", 116.00,
              "2026-05-14 21:45:40", _xml_test(sello), "PENDIENTE"))
        db.commit()
        cur.close()
        xml = obtener_xml(db, sello)
        assert "68F9774D-AEE5-463F-AAB8-7A26DB35B421" in xml


class TestActualizarTimbrado:

    def test_actualiza_estado_a_timbrado(self, db):
        from utils.database import actualizar_timbrado
        sello = _new_sello()
        cur = db.cursor()
        cur.execute("""
            INSERT INTO fact_schema.facturas
                ("SELLO","RFC_EMISOR","RFC_RECEPTOR","TOTAL","FECHA","XML","ESTADO")
            VALUES (%s,%s,%s,%s,%s,%s,%s)
        """, (sello, "GGG010101GGG", "MMM010101MMM", 116.00,
              "2026-05-14 21:45:40", _xml_test(sello), "PENDIENTE"))
        db.commit()
        cur.close()
        actualizar_timbrado(db, sello, _xml_test(sello) + "<!-- timbrado -->")
        cur = db.cursor()
        cur.execute('SELECT "ESTADO" FROM fact_schema.facturas WHERE "SELLO" = %s', (sello,))
        assert cur.fetchone()[0] == "TIMBRADO"
        cur.close()

    def test_xml_actualizado_tras_timbrado(self, db):
        from utils.database import actualizar_timbrado
        sello = _new_sello()
        cur = db.cursor()
        cur.execute("""
            INSERT INTO fact_schema.facturas
                ("SELLO","RFC_EMISOR","RFC_RECEPTOR","TOTAL","FECHA","XML","ESTADO")
            VALUES (%s,%s,%s,%s,%s,%s,%s)
        """, (sello, "GGG010101GGG", "MMM010101MMM", 116.00,
              "2026-05-14 21:45:40", _xml_test(sello), "PENDIENTE"))
        db.commit()
        cur.close()
        xml_timbrado = _xml_test(sello) + "<!-- uuid_pac_real -->"
        actualizar_timbrado(db, sello, xml_timbrado)
        cur = db.cursor()
        cur.execute('SELECT "XML" FROM fact_schema.facturas WHERE "SELLO" = %s', (sello,))
        xml_guardado = cur.fetchone()[0]
        cur.close()
        assert "uuid_pac_real" in xml_guardado


class TestGetFacturas:

    def _insertar(self, conn, sello, estado, rfc_e, rfc_r, fecha):
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO fact_schema.facturas
                ("SELLO","RFC_EMISOR","RFC_RECEPTOR","TOTAL","FECHA","XML","ESTADO")
            VALUES (%s,%s,%s,%s,%s,%s,%s)
        """, (sello, rfc_e, rfc_r, 116.00, fecha, _xml_test(sello), estado))
        conn.commit()
        cur.close()

    def test_retorna_dataframe(self, db):
        import pandas as pd
        from utils.database import get_facturas
        with patch("utils.database.get_connection", return_value=db):
            df = get_facturas()
        assert isinstance(df, pd.DataFrame)

    def test_columnas_esperadas(self, db):
        from utils.database import get_facturas
        with patch("utils.database.get_connection", return_value=db):
            df = get_facturas()
        for col in ["SELLO", "RFC_EMISOR", "RFC_RECEPTOR", "TOTAL", "FECHA", "ESTADO"]:
            assert col in df.columns

    def test_filtro_estado_timbrado(self, db):
        from utils.database import get_facturas
        s1, s2 = _new_sello(), _new_sello()
        self._insertar(db, s1, "TIMBRADO",  "GGG010101GGG", "MMM010101MMM", "2026-05-14 21:45:40")
        self._insertar(db, s2, "PENDIENTE", "GGG010101GGG", "MMM010101MMM", "2026-05-14 21:45:40")
        with patch("utils.database.get_connection", return_value=db):
            df = get_facturas(estado="TIMBRADO")
        df_test = df[df["SELLO"].str.startswith(TEST_PREFIX)]
        assert all(df_test["ESTADO"] == "TIMBRADO")

    def test_filtro_rfc_emisor(self, db):
        from utils.database import get_facturas
        s1 = _new_sello()
        rfc_unico = f"TEST_{uuid.uuid4().hex[:6].upper()}"
        self._insertar(db, s1, "PENDIENTE", rfc_unico, "MMM010101MMM", "2026-05-14 21:45:40")
        with patch("utils.database.get_connection", return_value=db):
            df = get_facturas(rfc_emisor=rfc_unico)
        assert len(df) >= 1
        assert all(df["RFC_EMISOR"].str.contains(rfc_unico))

    def test_filtro_rfc_receptor(self, db):
        from utils.database import get_facturas
        s1 = _new_sello()
        rfc_unico = f"TEST_{uuid.uuid4().hex[:6].upper()}"
        self._insertar(db, s1, "PENDIENTE", "GGG010101GGG", rfc_unico, "2026-05-14 21:45:40")
        with patch("utils.database.get_connection", return_value=db):
            df = get_facturas(rfc_receptor=rfc_unico)
        assert len(df) >= 1
        assert all(df["RFC_RECEPTOR"].str.contains(rfc_unico))

    def test_registros_insertados_aparecen_sin_filtro(self, db):
        from utils.database import get_facturas
        s1, s2 = _new_sello(), _new_sello()
        self._insertar(db, s1, "PENDIENTE", "GGG010101GGG", "MMM010101MMM", "2026-05-14 21:45:40")
        self._insertar(db, s2, "TIMBRADO",  "GGG010101GGG", "MMM010101MMM", "2026-05-14 21:45:40")
        with patch("utils.database.get_connection", return_value=db):
            df = get_facturas()
        assert s1 in df["SELLO"].tolist()
        assert s2 in df["SELLO"].tolist()