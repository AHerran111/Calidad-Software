# services/cfdi_generator.py
from datetime import datetime
import uuid

def generar_cfdi(data):
    cfdi = {
        "uuid": str(uuid.uuid4()),
        "fecha": datetime.now().isoformat(),
        "emisor": data["emisor"],
        "receptor": data["receptor"],
        "total": data["total"],
        "conceptos": data["conceptos"]
    }
    return cfdi