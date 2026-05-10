# services/cfdi_generator.py

from datetime import datetime

def generar_cfdi(data):

    cfdi = {
        # =========================
        # EMISOR
        # =========================
        "emisor": data["emisor"],
        "rfc_emisor": data["rfc_emisor"],
        "regimen_emisor": data["regimen_emisor"],
        "cp_emisor": data["cp_emisor"],
        "direccion_emisor": data["direccion_emisor"],

        # =========================
        # RECEPTOR
        # =========================
        "receptor": data["receptor"],
        "rfc_receptor": data["rfc_receptor"],
        "regimen_receptor": data["regimen_receptor"],
        "uso_cfdi": data["uso_cfdi"],
        "cp": data["cp"],

        # =========================
        # TOTALES
        # =========================
        "subtotal": data["subtotal"],
        "impuestos_final": data["impuestos_final"],
        "descuentos_final": data["descuentos_final"],
        "total_final": data["total_final"],

        # =========================
        # PAGO
        # =========================
        "forma_pago": data["forma_pago"],
        "metodo_pago": data["metodo_pago"],

        # =========================
        # MONEDA
        # =========================
        "moneda": data["moneda"],
        "tipo_cambio": data["tipo_cambio"],

        # =========================
        # FECHA
        # =========================
        "fecha": data.get(
            "fecha",
            datetime.now().isoformat()
        ),

        # =========================
        # CONCEPTOS
        # =========================
        "conceptos": data["conceptos"]
    }

    return cfdi