# utils/xml_utils.py
def dict_to_xml(cfdi):
    xml = f"""
<cfdi>
    <emisor>{cfdi['emisor']}</emisor>
    <receptor>{cfdi['receptor']}</receptor>
    <total>{cfdi['total']}</total>
    <uuid>{cfdi['uuid']}</uuid>
    <sello>{cfdi.get('sello','')}</sello>
</cfdi>
"""
    return xml