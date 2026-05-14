# utils/database.py

import psycopg2
from psycopg2.extras import RealDictCursor


import tomllib

with open("./utils/secrets.toml", "rb") as f:
    config = tomllib.load(f)

DB_CONFIG = config["database"]


def get_connection():
    return psycopg2.connect(
        host=DB_CONFIG["host"],
        dbname=DB_CONFIG["dbname"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        port=DB_CONFIG["port"],
    )


def get_emisores():
    conn = get_connection()

    try:
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

    finally:
        conn.close()


def get_receptores():
    conn = get_connection()

    try:
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

    finally:
        conn.close()

def guardar_factura(conn, factura):
    cursor = conn.cursor()

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
    VALUES (%s, %s, %s, %s, %s, %s, 'PENDIENTE')
    """

    cursor.execute(
        query,
        (
            factura["sello"],
            factura["rfc_emisor"],
            factura["rfc_receptor"],
            factura["total_final"],
            factura["fecha"],
            factura["xml"]
        )
    )

    conn.commit()
    cursor.close()

def obtener_pendientes(conn):

    cursor = conn.cursor()

    query = """
    SELECT
        "SELLO",
        "RFC_EMISOR",
        "TOTAL",
        "FECHA"
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

    cursor.execute(
        query,
        (
            xml_timbrado,
            sello
        )
    )

    conn.commit()
    cursor.close()