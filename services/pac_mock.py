# services/pac_mock.py
import uuid
from datetime import datetime

def timbrar_cfdi(cfdi):
    cfdi["timbre"] = {
        "uuid_fiscal": str(uuid.uuid4()),
        "fecha_timbrado": datetime.now().isoformat(),
        "pac": "PAC_FAKE"
    }
    cfdi["status"] = "timbrado"
    return cfdi