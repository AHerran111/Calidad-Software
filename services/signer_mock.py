# services/signer_mock.py
import base64

def sellar_cfdi(cfdi):
    cadena = f"{cfdi['emisor']}{cfdi['receptor']}{cfdi['total']}"
    sello_fake = base64.b64encode(cadena.encode()).decode()

    cfdi["sello"] = sello_fake
    return cfdi