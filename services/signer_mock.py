# services/signer_mock.py

import base64
from typing import Any


def sellar_cfdi(cfdi: dict[str, Any]) -> dict[str, Any]:
    cadena = (
        f"{cfdi['emisor']}"
        f"{cfdi['receptor']}"
        f"{cfdi['total_final']}"
        f"{cfdi['fecha']}"
    )

    sello_fake = base64.b64encode(cadena.encode("utf-8")).decode("utf-8")

    cfdi["sello"] = sello_fake

    return cfdi