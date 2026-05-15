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
from datetime import date, datetime
from unittest.mock import MagicMock, patch
from xml.etree import ElementTree as ET

import psycopg2
import pytest

# ---------------------------------------------------------------------------
# Helpers / fixtures compartidos
# ---------------------------------------------------------------------------

CONCEPTO_BASE = {
    "Producto": "Laptop",
    "Referencia": "REF-001",
    "ClaveProdServ": "43211503",
    "ClaveUnidad": "H87",
    "Unidad": "Pieza",
    "Precio": 10000.00,
    "Cantidad": 2.00,
    "ValorUnitario": 10000.00,
    "Importe": 20000.00,
    "Impuesto": 0.00,
    "Descuento": 0.00,
    "ObjetoImp": "02",
    "Base": 20000.00,
    "TipoFactor": "Tasa",
    "TasaOCuota": 0.160000,
    "ImporteImpuesto": 3200.00,
    "Descripcion": "Laptop de desarrollo",
    "Total": 23200.00,
}

DATA_BASE = {
    "emisor": "ACME SA de CV",
    "rfc_emisor": "ACM010101ABC",
    "regimen_emisor": "601",
    "cp_emisor": "44100",
    "direccion_emisor": "Av. Siempre Viva 123",
    "receptor": "Cliente SA de CV",
    "rfc_receptor": "CLI010101XYZ",
    "regimen_receptor": "601",
    "uso_cfdi": "G01 Adquisición de mercancias",
    "cp": "45010",
    "subtotal": 20000.00,
    "impuestos_final": 3200.00,
    "descuentos_final": 0.00,
    "total_final": 23200.00,
    "forma_pago": "03 TRANSFERENCIA",
    "metodo_pago": "Pago En Una Sola Exhibición (PUE)",
    "moneda": "MXN",
    "tipo_cambio": 1.0,
    "fecha": "2025-01-15T12:00:00",
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
        resultado = generar_cfdi(self._make_data())
        assert isinstance(resultado, dict)

    def test_campos_emisor_presentes(self):
        from services.cfdi_generator import generar_cfdi
        cfdi = generar_cfdi(self._make_data())
        assert cfdi["emisor"] == "ACME SA de CV"
        assert cfdi["rfc_emisor"] == "ACM010101ABC"
        assert cfdi["regimen_emisor"] == "601"
        assert cfdi["cp_emisor"] == "44100"

    def test_campos_receptor_presentes(self):
        from services.cfdi_generator import generar_cfdi
        cfdi = generar_cfdi(self._make_data())
        assert cfdi["receptor"] == "Cliente SA de CV"
        assert cfdi["rfc_receptor"] == "CLI010101XYZ"
        assert cfdi["uso_cfdi"] == "G01 Adquisición de mercancias"

    def test_totales_correctos(self):
        from services.cfdi_generator import generar_cfdi
        cfdi = generar_cfdi(self._make_data())
        assert cfdi["subtotal"] == 20000.00
        assert cfdi["impuestos_final"] == 3200.00
        assert cfdi["descuentos_final"] == 0.00
        assert cfdi["total_final"] == 23200.00

    def test_conceptos_se_copian(self):
        from services.cfdi_generator import generar_cfdi
        cfdi = generar_cfdi(self._make_data())
        assert len(cfdi["conceptos"]) == 1
        assert cfdi["conceptos"][0]["Producto"] == "Laptop"

    def test_fecha_default_cuando_no_viene(self):
        from services.cfdi_generator import generar_cfdi
        data = self._make_data()
        data.pop("fecha")
        cfdi = generar_cfdi(data)
        # Debe generar una fecha ISO válida
        datetime.fromisoformat(cfdi["fecha"])

    def test_pago_presente(self):
        from services.cfdi_generator import generar_cfdi
        cfdi = generar_cfdi(self._make_data())
        assert "forma_pago" in cfdi
        assert "metodo_pago" in cfdi
        assert "moneda" in cfdi
        assert "tipo_cambio" in cfdi

    def test_multiples_conceptos(self):
        from services.cfdi_generator import generar_cfdi
        concepto2 = {**CONCEPTO_BASE, "Producto": "Mouse", "Importe": 500.00}
        cfdi = generar_cfdi(self._make_data(conceptos=[CONCEPTO_BASE, concepto2]))
        assert len(cfdi["conceptos"]) == 2


# ---------------------------------------------------------------------------
# 2. services/signer_mock.py
# ---------------------------------------------------------------------------

class TestSellarCfdi:

    def _cfdi_sin_sello(self):
        from services.cfdi_generator import generar_cfdi
        return generar_cfdi(DATA_BASE)

    def test_agrega_campo_sello(self):
        from services.signer_mock import sellar_cfdi
        cfdi = self._cfdi_sin_sello()
        resultado = sellar_cfdi(cfdi)
        assert "sello" in resultado

    def test_sello_es_base64_valido(self):
        from services.signer_mock import sellar_cfdi
        cfdi = self._cfdi_sin_sello()
        resultado = sellar_cfdi(cfdi)
        # No debe lanzar excepción al decodificar
        decoded = base64.b64decode(resultado["sello"]).decode()
        assert len(decoded) > 0

    def test_sello_contiene_datos_cfdi(self):
        from services.signer_mock import sellar_cfdi
        cfdi = self._cfdi_sin_sello()
        resultado = sellar_cfdi(cfdi)
        decoded = base64.b64decode(resultado["sello"]).decode()
        assert cfdi["emisor"] in decoded
        assert cfdi["receptor"] in decoded

    def test_retorna_mismo_cfdi(self):
        from services.signer_mock import sellar_cfdi
        cfdi = self._cfdi_sin_sello()
        resultado = sellar_cfdi(cfdi)
        assert resultado["emisor"] == cfdi["emisor"]
        assert resultado["total_final"] == cfdi["total_final"]

    def test_sello_distinto_para_distintos_cfdi(self):
        from services.signer_mock import sellar_cfdi
        from services.cfdi_generator import generar_cfdi
        cfdi_a = generar_cfdi({**DATA_BASE, "emisor": "EmisorA"})
        cfdi_b = generar_cfdi({**DATA_BASE, "emisor": "EmisorB"})
        assert sellar_cfdi(cfdi_a)["sello"] != sellar_cfdi(cfdi_b)["sello"]


# ---------------------------------------------------------------------------
# 3. utils/xml_utils.py
# ---------------------------------------------------------------------------

class TestDictToXml:

    def _cfdi_sellado(self, **overrides):
        from services.cfdi_generator import generar_cfdi
        from services.signer_mock import sellar_cfdi
        data = {**DATA_BASE, **overrides}
        # sellar_cfdi guarda "sello" (minúscula); xml_utils lee "sello"
        cfdi = generar_cfdi(data)
        return sellar_cfdi(cfdi)

    def test_retorna_string_xml(self):
        from utils.xml_utils import dict_to_xml
        xml = dict_to_xml(self._cfdi_sellado())
        assert isinstance(xml, str)
        assert "<?xml" in xml

    def test_nodo_comprobante_presente(self):
        from utils.xml_utils import dict_to_xml
        xml = dict_to_xml(self._cfdi_sellado())
        root = ET.fromstring(xml.encode())
        assert "Comprobante" in root.tag

    def test_atributos_obligatorios_comprobante(self):
        from utils.xml_utils import dict_to_xml
        xml = dict_to_xml(self._cfdi_sellado())
        root = ET.fromstring(xml.encode())
        for attr in ["Version", "Fecha", "Moneda", "SubTotal", "Total"]:
            assert root.attrib.get(attr), f"Falta atributo: {attr}"

    def test_version_es_4(self):
        from utils.xml_utils import dict_to_xml
        xml = dict_to_xml(self._cfdi_sellado())
        root = ET.fromstring(xml.encode())
        assert root.attrib["Version"] == "4.0"

    def test_nodo_emisor_presente(self):
        from utils.xml_utils import dict_to_xml
        NS = "{http://www.sat.gob.mx/cfd/4}"
        xml = dict_to_xml(self._cfdi_sellado())
        root = ET.fromstring(xml.encode())
        emisor = root.find(f"{NS}Emisor")
        assert emisor is not None
        assert emisor.attrib["Rfc"] == "ACM010101ABC"

    def test_nodo_receptor_presente(self):
        from utils.xml_utils import dict_to_xml
        NS = "{http://www.sat.gob.mx/cfd/4}"
        xml = dict_to_xml(self._cfdi_sellado())
        root = ET.fromstring(xml.encode())
        receptor = root.find(f"{NS}Receptor")
        assert receptor is not None
        assert receptor.attrib["Rfc"] == "CLI010101XYZ"

    def test_al_menos_un_concepto(self):
        from utils.xml_utils import dict_to_xml
        NS = "{http://www.sat.gob.mx/cfd/4}"
        xml = dict_to_xml(self._cfdi_sellado())
        root = ET.fromstring(xml.encode())
        conceptos = root.find(f"{NS}Conceptos")
        assert conceptos is not None
        assert len(conceptos.findall(f"{NS}Concepto")) >= 1

    def test_subtotal_correcto(self):
        from utils.xml_utils import dict_to_xml
        xml = dict_to_xml(self._cfdi_sellado())
        root = ET.fromstring(xml.encode())
        assert float(root.attrib["SubTotal"]) == pytest.approx(20000.00)

    def test_total_correcto(self):
        from utils.xml_utils import dict_to_xml
        xml = dict_to_xml(self._cfdi_sellado())
        root = ET.fromstring(xml.encode())
        assert float(root.attrib["Total"]) == pytest.approx(23200.00)

    def test_metodo_pago_mapeado(self):
        from utils.xml_utils import dict_to_xml
        xml = dict_to_xml(self._cfdi_sellado())
        root = ET.fromstring(xml.encode())
        assert root.attrib["MetodoPago"] == "PUE"

    def test_forma_pago_mapeada(self):
        from utils.xml_utils import dict_to_xml
        xml = dict_to_xml(self._cfdi_sellado())
        root = ET.fromstring(xml.encode())
        assert root.attrib["FormaPago"] == "03"

    def test_complemento_timbrado_presente(self):
        from utils.xml_utils import dict_to_xml
        NS_CFDI = "{http://www.sat.gob.mx/cfd/4}"
        NS_TFD = "{http://www.sat.gob.mx/TimbreFiscalDigital}"
        xml = dict_to_xml(self._cfdi_sellado())
        root = ET.fromstring(xml.encode())
        complemento = root.find(f"{NS_CFDI}Complemento")
        assert complemento is not None
        tfd = complemento.find(f"{NS_TFD}TimbreFiscalDigital")
        assert tfd is not None
        assert tfd.attrib["Version"] == "1.1"

    def test_impuestos_globales_presentes(self):
        from utils.xml_utils import dict_to_xml
        NS = "{http://www.sat.gob.mx/cfd/4}"
        xml = dict_to_xml(self._cfdi_sellado())
        root = ET.fromstring(xml.encode())
        impuestos = root.find(f"{NS}Impuestos")
        assert impuestos is not None
        assert impuestos.attrib.get("TotalImpuestosTrasladados")

    def test_xml_es_parseable(self):
        from utils.xml_utils import dict_to_xml
        xml = dict_to_xml(self._cfdi_sellado())
        # No debe lanzar excepción
        ET.fromstring(xml.encode())

    def test_ppd_mapeado(self):
        from utils.xml_utils import dict_to_xml
        cfdi = self._cfdi_sellado(
            metodo_pago="Pago en Parcialidades o Diferido (PPD)",
            forma_pago="99 POR DEFINIR",
        )
        xml = dict_to_xml(cfdi)
        root = ET.fromstring(xml.encode())
        assert root.attrib["MetodoPago"] == "PPD"
        assert root.attrib["FormaPago"] == "99"


# ---------------------------------------------------------------------------
# 4. utils/database.py  –  con fixture de BD de prueba
# ---------------------------------------------------------------------------

TEST_DB_CONFIG = {
    "host": "localhost",
    "dbname": "test_cfdi",
    "user": "postgres",
    "password": "postgres",
    "port": 5432,
}

DDL = """
CREATE SCHEMA IF NOT EXISTS fact_schema;

CREATE TABLE IF NOT EXISTS fact_schema.emisores (
    rfc            TEXT PRIMARY KEY,
    nombre         TEXT NOT NULL,
    regimen_fiscal TEXT NOT NULL,
    codigo_postal  TEXT NOT NULL,
    direccion      TEXT
);

CREATE TABLE IF NOT EXISTS fact_schema.receptores (
    rfc            TEXT PRIMARY KEY,
    nombre         TEXT NOT NULL,
    regimen_fiscal TEXT NOT NULL,
    codigo_postal  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS fact_schema.facturas (
    "SELLO"        TEXT PRIMARY KEY,
    "RFC_EMISOR"   TEXT NOT NULL,
    "RFC_RECEPTOR" TEXT NOT NULL,
    "TOTAL"        NUMERIC NOT NULL,
    "FECHA"        TIMESTAMP NOT NULL,
    "XML"          TEXT NOT NULL,
    "ESTADO"       TEXT NOT NULL DEFAULT 'PENDIENTE'
);
"""


def _get_test_conn():
    """Intenta conectar a la BD de prueba; omite el test si no está disponible."""
    try:
        conn = psycopg2.connect(**TEST_DB_CONFIG)
        conn.autocommit = False
        return conn
    except psycopg2.OperationalError:
        return None


@pytest.fixture(scope="module")
def test_db():
    """
    Fixture de módulo: crea el esquema de prueba y lo destruye al terminar.
    Si la BD no está disponible, todos los tests que dependan de esta
    fixture se marcarán como 'skipped'.
    """
    conn = _get_test_conn()
    if conn is None:
        pytest.skip("Base de datos de prueba no disponible (test_cfdi)")

    cur = conn.cursor()
    cur.execute(DDL)
    conn.commit()
    cur.close()

    yield conn

    # Teardown: limpiar tablas
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS fact_schema.facturas CASCADE;")
    cur.execute("DROP TABLE IF EXISTS fact_schema.emisores CASCADE;")
    cur.execute("DROP TABLE IF EXISTS fact_schema.receptores CASCADE;")
    conn.commit()
    cur.close()
    conn.close()


@pytest.fixture(autouse=False)
def clean_facturas(test_db):
    """Limpia la tabla de facturas antes de cada test que la use."""
    cur = test_db.cursor()
    cur.execute('DELETE FROM fact_schema.facturas')
    cur.execute('DELETE FROM fact_schema.emisores')
    cur.execute('DELETE FROM fact_schema.receptores')
    test_db.commit()
    cur.close()
    yield


def _xml_valido(sello="SELLO123"):
    """Genera un XML CFDI mínimo válido para insertar en la BD."""
    return f"""<?xml version="1.0" ?>
<cfdi:Comprobante
    xmlns:cfdi="http://www.sat.gob.mx/cfd/4"
    Version="4.0"
    Fecha="2025-01-15T12:00:00"
    Moneda="MXN"
    TipoDeComprobante="I"
    Exportacion="01"
    LugarExpedicion="44100"
    MetodoPago="PUE"
    FormaPago="03"
    SubTotal="20000.00"
    Descuento="0.00"
    Total="23200.00"
    Sello="{sello}">
  <cfdi:Emisor Nombre="ACME" Rfc="ACM010101ABC" RegimenFiscal="601"/>
  <cfdi:Receptor Nombre="Cliente" Rfc="CLI010101XYZ"
      DomicilioFiscalReceptor="45010"
      RegimenFiscalReceptor="601"
      UsoCFDI="G01"/>
  <cfdi:Conceptos/>
  <cfdi:Impuestos TotalImpuestosTrasladados="3200.00"/>
</cfdi:Comprobante>"""


class TestInsercionEmisor:

    def test_insertar_emisor_exitoso(self, test_db, clean_facturas):
        from utils.database import insertar_emisor
        insertar_emisor(test_db, "TST010101AAA", "Test SA", "601", "44100", "Calle 1")
        cur = test_db.cursor()
        cur.execute("SELECT rfc FROM fact_schema.emisores WHERE rfc = 'TST010101AAA'")
        row = cur.fetchone()
        cur.close()
        assert row is not None

    def test_insertar_emisor_duplicado_lanza_error(self, test_db, clean_facturas):
        from utils.database import insertar_emisor
        insertar_emisor(test_db, "DUP010101AAA", "Dup SA", "601", "44100", "Calle 2")
        with pytest.raises(Exception):
            insertar_emisor(test_db, "DUP010101AAA", "Dup SA", "601", "44100", "Calle 2")
        test_db.rollback()


class TestInsercionReceptor:

    def test_insertar_receptor_exitoso(self, test_db, clean_facturas):
        from utils.database import insertar_receptor
        insertar_receptor(test_db, "REC010101AAA", "Receptor Test", "606", "45010")
        cur = test_db.cursor()
        cur.execute("SELECT rfc FROM fact_schema.receptores WHERE rfc = 'REC010101AAA'")
        row = cur.fetchone()
        cur.close()
        assert row is not None


class TestGuardarFactura:

    def test_guardar_factura_inserta_registro(self, test_db, clean_facturas):
        sello = f"SELLO_{uuid.uuid4().hex[:8]}"
        xml = _xml_valido(sello=sello)
        # Parchamos DB_CONFIG para apuntar a la BD de prueba
        with patch("utils.database.DB_CONFIG", TEST_DB_CONFIG):
            with patch("psycopg2.connect", return_value=test_db):
                from utils.database import guardar_factura
                guardar_factura(xml)
        cur = test_db.cursor()
        cur.execute('SELECT "SELLO" FROM fact_schema.facturas WHERE "SELLO" = %s', (sello,))
        row = cur.fetchone()
        cur.close()
        assert row is not None

    def test_guardar_factura_estado_pendiente(self, test_db, clean_facturas):
        sello = f"SELLO_{uuid.uuid4().hex[:8]}"
        xml = _xml_valido(sello=sello)
        with patch("utils.database.DB_CONFIG", TEST_DB_CONFIG):
            with patch("psycopg2.connect", return_value=test_db):
                from utils.database import guardar_factura
                guardar_factura(xml)
        cur = test_db.cursor()
        cur.execute('SELECT "ESTADO" FROM fact_schema.facturas WHERE "SELLO" = %s', (sello,))
        estado = cur.fetchone()[0]
        cur.close()
        assert estado == "PENDIENTE"


class TestObtenerPendientes:

    def _insertar_factura(self, conn, sello, estado="PENDIENTE"):
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO fact_schema.facturas
                ("SELLO","RFC_EMISOR","RFC_RECEPTOR","TOTAL","FECHA","XML","ESTADO")
            VALUES (%s,%s,%s,%s,%s,%s,%s)
        """, (sello, "ACM010101ABC", "CLI010101XYZ", 23200, "2025-01-15 12:00:00",
              _xml_valido(sello), estado))
        conn.commit()
        cur.close()

    def test_retorna_solo_pendientes(self, test_db, clean_facturas):
        from utils.database import obtener_pendientes
        self._insertar_factura(test_db, "PEND001", "PENDIENTE")
        self._insertar_factura(test_db, "TIMB001", "TIMBRADO")
        rows = obtener_pendientes(test_db)
        sellos = [r[0] for r in rows]
        assert "PEND001" in sellos
        assert "TIMB001" not in sellos

    def test_sin_pendientes_retorna_lista_vacia(self, test_db, clean_facturas):
        from utils.database import obtener_pendientes
        rows = obtener_pendientes(test_db)
        assert rows == []


class TestObtenerXml:

    def test_obtiene_xml_correcto(self, test_db, clean_facturas):
        from utils.database import obtener_xml
        sello = "XMLTEST001"
        xml_orig = _xml_valido(sello=sello)
        cur = test_db.cursor()
        cur.execute("""
            INSERT INTO fact_schema.facturas
                ("SELLO","RFC_EMISOR","RFC_RECEPTOR","TOTAL","FECHA","XML","ESTADO")
            VALUES (%s,%s,%s,%s,%s,%s,%s)
        """, (sello, "ACM010101ABC", "CLI010101XYZ", 23200,
              "2025-01-15 12:00:00", xml_orig, "PENDIENTE"))
        test_db.commit()
        cur.close()
        xml_recuperado = obtener_xml(test_db, sello)
        assert "Comprobante" in xml_recuperado


class TestActualizarTimbrado:

    def test_actualiza_estado_a_timbrado(self, test_db, clean_facturas):
        from utils.database import actualizar_timbrado
        sello = "TIMB_UPD_001"
        cur = test_db.cursor()
        cur.execute("""
            INSERT INTO fact_schema.facturas
                ("SELLO","RFC_EMISOR","RFC_RECEPTOR","TOTAL","FECHA","XML","ESTADO")
            VALUES (%s,%s,%s,%s,%s,%s,%s)
        """, (sello, "ACM010101ABC", "CLI010101XYZ", 23200,
              "2025-01-15 12:00:00", _xml_valido(sello), "PENDIENTE"))
        test_db.commit()
        cur.close()

        xml_timbrado = _xml_valido(sello) + "<!-- timbrado -->"
        actualizar_timbrado(test_db, sello, xml_timbrado)

        cur = test_db.cursor()
        cur.execute('SELECT "ESTADO" FROM fact_schema.facturas WHERE "SELLO" = %s', (sello,))
        estado = cur.fetchone()[0]
        cur.close()
        assert estado == "TIMBRADO"


class TestGetFacturas:

    def _insertar(self, conn, sello, estado, rfc_e, rfc_r, fecha):
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO fact_schema.facturas
                ("SELLO","RFC_EMISOR","RFC_RECEPTOR","TOTAL","FECHA","XML","ESTADO")
            VALUES (%s,%s,%s,%s,%s,%s,%s)
        """, (sello, rfc_e, rfc_r, 1000, fecha, _xml_valido(sello), estado))
        conn.commit()
        cur.close()

    def test_filtro_estado(self, test_db, clean_facturas):
        from utils.database import get_facturas
        self._insertar(test_db, "F001", "TIMBRADO",  "AAA", "BBB", "2025-06-01 10:00:00")
        self._insertar(test_db, "F002", "PENDIENTE", "AAA", "BBB", "2025-06-02 10:00:00")
        with patch("utils.database.get_connection", return_value=test_db):
            df = get_facturas(estado="TIMBRADO")
        assert all(df["ESTADO"] == "TIMBRADO")

    def test_filtro_rfc_emisor(self, test_db, clean_facturas):
        from utils.database import get_facturas
        self._insertar(test_db, "F003", "PENDIENTE", "EMIS_X", "BBB", "2025-06-01 10:00:00")
        self._insertar(test_db, "F004", "PENDIENTE", "EMIS_Y", "BBB", "2025-06-02 10:00:00")
        with patch("utils.database.get_connection", return_value=test_db):
            df = get_facturas(rfc_emisor="EMIS_X")
        assert all(df["RFC_EMISOR"].str.contains("EMIS_X"))

    def test_sin_filtros_retorna_todo(self, test_db, clean_facturas):
        from utils.database import get_facturas
        self._insertar(test_db, "F005", "PENDIENTE", "AAA", "BBB", "2025-06-01 10:00:00")
        self._insertar(test_db, "F006", "TIMBRADO",  "CCC", "DDD", "2025-06-02 10:00:00")
        with patch("utils.database.get_connection", return_value=test_db):
            df = get_facturas()
        assert len(df) >= 2

    def test_retorna_dataframe(self, test_db, clean_facturas):
        import pandas as pd
        from utils.database import get_facturas
        with patch("utils.database.get_connection", return_value=test_db):
            df = get_facturas()
        assert isinstance(df, pd.DataFrame)


# ---------------------------------------------------------------------------
# 5. pac_server_repo/app.py  –  FastAPI con TestClient
# ---------------------------------------------------------------------------

class TestPacServer:

    @pytest.fixture(autouse=True)
    def client(self):
        from fastapi.testclient import TestClient
        # Parchamos psycopg2.connect para que upload_data no toque una BD real
        with patch("psycopg2.connect") as mock_connect:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn

            import importlib
            import pac_server_repo.app as pac_app
            importlib.reload(pac_app)
            self.app_client = TestClient(pac_app.app)
        yield

    def _xml_valido_pac(self, sello="SELLO_PAC"):
        return f"""<?xml version="1.0" ?>
<cfdi:Comprobante
    xmlns:cfdi="http://www.sat.gob.mx/cfd/4"
    Version="4.0"
    Fecha="2025-01-15T12:00:00"
    Moneda="MXN"
    TipoDeComprobante="I"
    Exportacion="01"
    LugarExpedicion="44100"
    MetodoPago="PUE"
    FormaPago="03"
    SubTotal="20000.00"
    Descuento="0.00"
    Total="23200.00"
    Sello="{sello}">
  <cfdi:Emisor Nombre="ACME" Rfc="ACM010101ABC" RegimenFiscal="601"/>
  <cfdi:Receptor Nombre="Cliente" Rfc="CLI010101XYZ"
      DomicilioFiscalReceptor="45010"
      RegimenFiscalReceptor="601"
      UsoCFDI="G01"/>
  <cfdi:Conceptos>
    <cfdi:Concepto
        ClaveProdServ="43211503"
        NoIdentificacion="REF-001"
        Cantidad="2.00"
        ClaveUnidad="H87"
        Unidad="Pieza"
        Descripcion="Laptop"
        ValorUnitario="10000.00"
        Importe="20000.00"
        Descuento="0.00"
        ObjetoImp="02">
      <cfdi:Impuestos>
        <cfdi:Traslados>
          <cfdi:Traslado Base="20000.00" Impuesto="002"
              TipoFactor="Tasa" TasaOCuota="0.160000" Importe="3200.00"/>
        </cfdi:Traslados>
      </cfdi:Impuestos>
    </cfdi:Concepto>
  </cfdi:Conceptos>
  <cfdi:Impuestos TotalImpuestosTrasladados="3200.00"/>
  <cfdi:Complemento/>
</cfdi:Comprobante>"""

    def test_get_message(self):
        r = self.app_client.get("/get-message")
        assert r.status_code == 200
        assert r.json()["Message"] == "Success"

    def test_process_xml_valido_retorna_200(self):
        with patch("pac_server_repo.app.upload_data"):
            r = self.app_client.post(
                "/process_xml",
                content=self._xml_valido_pac().encode(),
                headers={"Content-Type": "application/xml"},
            )
        assert r.status_code == 200

    def test_process_xml_contiene_timbrado(self):
        with patch("pac_server_repo.app.upload_data"):
            r = self.app_client.post(
                "/process_xml",
                content=self._xml_valido_pac().encode(),
                headers={"Content-Type": "application/xml"},
            )
        assert "TimbreFiscalDigital" in r.text

    def test_process_xml_invalido_retorna_400(self):
        r = self.app_client.post(
            "/process_xml",
            content=b"esto no es xml",
            headers={"Content-Type": "application/xml"},
        )
        assert r.status_code == 400

    def test_process_xml_sin_emisor_retorna_500(self):
        xml_malo = """<?xml version="1.0" ?>
<cfdi:Comprobante
    xmlns:cfdi="http://www.sat.gob.mx/cfd/4"
    Version="4.0" Fecha="2025-01-15T12:00:00"
    Moneda="MXN" TipoDeComprobante="I"
    Exportacion="01" LugarExpedicion="44100"
    SubTotal="100.00" Total="116.00">
  <cfdi:Conceptos>
    <cfdi:Concepto Cantidad="1.00" Descripcion="X"
        ValorUnitario="100.00" Importe="100.00"/>
  </cfdi:Conceptos>
  <cfdi:Impuestos TotalImpuestosTrasladados="16.00"/>
</cfdi:Comprobante>"""
        r = self.app_client.post(
            "/process_xml",
            content=xml_malo.encode(),
            headers={"Content-Type": "application/xml"},
        )
        assert r.status_code == 500

    def test_process_xml_sin_conceptos_retorna_500(self):
        xml_malo = """<?xml version="1.0" ?>
<cfdi:Comprobante
    xmlns:cfdi="http://www.sat.gob.mx/cfd/4"
    Version="4.0" Fecha="2025-01-15T12:00:00"
    Moneda="MXN" TipoDeComprobante="I"
    Exportacion="01" LugarExpedicion="44100"
    SubTotal="100.00" Total="116.00">
  <cfdi:Emisor Nombre="X" Rfc="AAA010101AAA" RegimenFiscal="601"/>
  <cfdi:Receptor Nombre="Y" Rfc="BBB010101BBB"
      DomicilioFiscalReceptor="44100"
      RegimenFiscalReceptor="601" UsoCFDI="G01"/>
  <cfdi:Conceptos/>
  <cfdi:Impuestos TotalImpuestosTrasladados="16.00"/>
</cfdi:Comprobante>"""
        r = self.app_client.post(
            "/process_xml",
            content=xml_malo.encode(),
            headers={"Content-Type": "application/xml"},
        )
        assert r.status_code == 500

    def test_process_xml_total_invalido_retorna_500(self):
        xml_malo = self._xml_valido_pac()
        # Reemplazar Total con 0
        xml_malo = xml_malo.replace('Total="23200.00"', 'Total="0.00"')
        r = self.app_client.post(
            "/process_xml",
            content=xml_malo.encode(),
            headers={"Content-Type": "application/xml"},
        )
        assert r.status_code == 500