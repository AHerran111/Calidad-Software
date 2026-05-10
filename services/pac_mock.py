# services/pac_mock.py

from xml.etree import ElementTree as ET
import requests


def timbrar_cfdi(xml_string):

   
    url = "http://127.0.0.1:8000/process_xml"

    headers = {
        "Content-Type": "application/xml"
    }

    response = requests.post(
        url,
        data=xml_string,
        headers=headers
    )

    print(response.status_code)
    print(response.text)

    