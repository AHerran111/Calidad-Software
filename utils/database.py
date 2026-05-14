# utils/database.py
import tomllib
from xml.etree import ElementTree as ET

import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor

with open("./utils/secrets.toml", "rb") as f:
    config = tomllib.load(f)

DB_CONFIG = config["database"]
CFDI_NS = "{http://www.sat.gob.mx/cfd/4}"


def get_connection():
    return psycopg2.connect(
        host=DB_CONFIG["host"],
        dbname=DB_CONFIG["dbname"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        port=DB_CONFIG["port"],
    )


def get_emisores(conn):

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT
                rfc,
                nombre,
                regimen_fiscal,
                codigo_postal,
                direccion
            FROM fact_schema.emisores
            ORDER BY nombre
        """)

        rows = cur.fetchall()

        emisores = {}

        for row in rows:
            emisores[row["nombre"]] = {
                "rfc": row["rfc"],
                "regimen": row["regimen_fiscal"],
                "cp": row["codigo_postal"],
                "address": row["direccion"],
            }

        return emisores


def get_receptores(conn):

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT
                rfc,
                nombre,
                regimen_fiscal,
                codigo_postal
            FROM fact_schema.receptores
            ORDER BY nombre
        """)

        return cur.fetchall()


def guardar_factura(conn, xml):
    cursor = conn.cursor()
    root = ET.fromstring(xml)

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

    estado = "PENDIENTE"

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
        cur.execute(query, (sello, rfc_emisor, rfc_receptor, total, fecha, xml, estado))

        conn.commit()
        print("commited succesfully")

    except Exception as e:
        conn.rollback()
        raise Exception(f"POSTGRES error: {e}")

    finally:
        cur.close()
        conn.close()


def obtener_pendientes(conn):

    cursor = conn.cursor()

    query = """
    SELECT
        "SELLO",
        "RFC_EMISOR",
        "RFC_RECEPTOR",
        "TOTAL",
        "FECHA",
        "ESTADO"
    FROM fact_schema.facturas
    WHERE "ESTADO" = 'PENDIENTE'
    """

    cursor.execute(query)

    rows = cursor.fetchall()

    cursor.close()

    return rows


def obtener_xml(conn, sello):

    cursor = conn.cursor()

    query = """
    SELECT "XML"
    FROM fact_schema.facturas
    WHERE "SELLO" = %s
    """

    cursor.execute(query, (sello,))

    row = cursor.fetchone()

    cursor.close()

    return row[0]


def actualizar_timbrado(conn, sello, xml_timbrado):

    cursor = conn.cursor()

    query = """
    UPDATE fact_schema.facturas
    SET
        "XML" = %s,
        "ESTADO" = 'TIMBRADO'
    WHERE "SELLO" = %s
    """

    cursor.execute(query, (xml_timbrado, sello))

    conn.commit()
    cursor.close()


def get_facturas(estado="Todos", rfc_emisor="", rfc_receptor="", fecha=None):

    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT
            "SELLO",
            "RFC_EMISOR",
            "RFC_RECEPTOR",
            "TOTAL",
            "FECHA",
            "ESTADO"
        FROM fact_schema.facturas
        WHERE 1=1
    """

    params = []

    if estado != "Todos":
        query += ' AND "ESTADO" = %s'
        params.append(estado)

    if rfc_emisor:
        query += ' AND "RFC_EMISOR" ILIKE %s'
        params.append(f"%{rfc_emisor}%")

    if rfc_receptor:
        query += ' AND "RFC_RECEPTOR" ILIKE %s'
        params.append(f"%{rfc_receptor}%")

    if fecha:
        query += ' AND DATE("FECHA") = %s'
        params.append(fecha)

    query += ' ORDER BY "FECHA" DESC'

    cursor.execute(query, params)

    rows = cursor.fetchall()

    columns = [desc[0] for desc in cursor.description]

    df = pd.DataFrame(rows, columns=columns)

    cursor.close()
    conn.close()

    return df


def insertar_emisor(conn, rfc, nombre, regimen, cp, direccion):

    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO fact_schema.emisores (
            rfc,
            nombre,
            regimen_fiscal,
            codigo_postal,
            direccion
        )
        VALUES (%s, %s, %s, %s, %s)
    """,
        (rfc, nombre, regimen, cp, direccion),
    )

    conn.commit()


def insertar_receptor(conn, rfc, nombre, regimen, cp):

    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO fact_schema.receptores (
            rfc,
            nombre,
            regimen_fiscal,
            codigo_postal
        )
        VALUES (%s, %s, %s, %s)
    """,
        (rfc, nombre, regimen, cp),
    )

    conn.commit()
