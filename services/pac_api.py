# services/pac_mock.py

import requests


def timbrar_cfdi(xml_string):

    url = "http://146.190.199.98/process_xml"

    headers = {"Content-Type": "application/xml"}

    response = requests.post(url, data=xml_string, headers=headers)

    print(response.status_code)
    print(response.text)

    return response.text
