//tests/load_test.js
import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  vus: 20,
  duration: "30s",

  thresholds: {
    http_req_duration: ["p(95)<2000"],
    http_req_failed: ["rate<0.01"],
  },
};

function generateXML() {
  const folio = Math.random().toString(16).substring(2, 10);

  // unique sello per request
  const sello =
    "TEST_" +
    Date.now().toString(16) +
    "_" +
    Math.random().toString(16).substring(2, 12);

  return `
<cfdi:Comprobante
    xmlns:cfdi="http://www.sat.gob.mx/cfd/4"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.sat.gob.mx/cfd/4
    http://www.sat.gob.mx/sitio_internet/cfd/4/cfdv40.xsd"
    Version="4.0"
    Serie="A"
    Folio="${folio}"
    Fecha="2026-05-15T06:24:50"
    Moneda="MXN"
    TipoDeComprobante="I"
    Exportacion="01"
    LugarExpedicion="44600"
    MetodoPago="PUE"
    FormaPago="01"
    SubTotal="200.00"
    Descuento="40.00"
    Total="185.60"
    Sello="${sello}">

    <cfdi:Emisor
        Nombre="TECNOLOGIA APLICADA SA DE CV"
        Rfc="FFF010101FFF"
        RegimenFiscal="601"/>

    <cfdi:Receptor
        Nombre="GRUPO HOTELERO MAYA"
        Rfc="QQQ010101QQQ"
        DomicilioFiscalReceptor="77500"
        RegimenFiscalReceptor="601"
        UsoCFDI="G01"/>

    <cfdi:Conceptos>
        <cfdi:Concepto
            ClaveProdServ="01010101"
            Cantidad="10.00"
            ClaveUnidad="H87"
            Unidad="Pieza"
            Descripcion="Producto Test"
            ValorUnitario="20.00"
            Importe="200.00"
            Descuento="40.00"
            ObjetoImp="02">

            <cfdi:Impuestos>
                <cfdi:Traslados>
                    <cfdi:Traslado
                        Base="160.00"
                        Impuesto="002"
                        TipoFactor="Tasa"
                        TasaOCuota="0.160000"
                        Importe="25.60"/>
                </cfdi:Traslados>
            </cfdi:Impuestos>

        </cfdi:Concepto>
    </cfdi:Conceptos>

    <cfdi:Impuestos TotalImpuestosTrasladados="25.60">
        <cfdi:Traslados>
            <cfdi:Traslado
                Base="160.00"
                Impuesto="002"
                TipoFactor="Tasa"
                TasaOCuota="0.160000"
                Importe="25.60"/>
        </cfdi:Traslados>
    </cfdi:Impuestos>

</cfdi:Comprobante>
`;
}

export default function () {
  const payload = generateXML();

  const params = {
    headers: {
      "Content-Type": "application/xml",
      Accept: "application/xml",
    },
  };

  const response = http.post(
    "http://146.190.199.98/process_xml",
    payload,
    params
  );

  check(response, {
    "status 200": (r) => r.status === 200,
    "not empty response": (r) => r.body.length > 0,
    "response under 2s": (r) => r.timings.duration < 2000,
  });

  if (response.status !== 200) {
    console.log("ERROR STATUS:", response.status);
    console.log("ERROR BODY:", response.body);
  }

  sleep(1);
}