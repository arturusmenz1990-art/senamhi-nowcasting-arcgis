
import requests
import xml.etree.ElementTree as ET

BASE = (
    "https://idesep.senamhi.gob.pe/"
    "geoserver/g_nowcasting/ows"
)

params = {
    "service": "WFS",
    "version": "1.0.0",
    "request": "GetCapabilities"
}

headers = {
    "User-Agent": "Mozilla/5.0 SENAMHI-ArcGIS-Test/1.0"
}

print("===================================")
print("PRUEBA DIRECTA DEL WFS SENAMHI")
print("===================================")

print("\n1. Conectando con GeoServer...")

try:
    response = requests.get(
        BASE,
        params=params,
        headers=headers,
        timeout=(30, 90)
    )

    response.raise_for_status()

    print("HTTP:", response.status_code)
    print("Conexión establecida.")

    print("\n2. Analizando respuesta XML...")

    root = ET.fromstring(response.content)

    def local_name(element):
        return element.tag.split("}")[-1]

    if local_name(root) in (
        "ExceptionReport",
        "ServiceExceptionReport"
    ):
        print("ERROR DEL GEOSERVER:")
        print(response.text[:3000])
        raise RuntimeError("GeoServer devolvió una excepción.")

    feature_types = [
        element for element in root.iter()
        if local_name(element) == "FeatureType"
    ]

    print("\n3. CAPAS DISPONIBLES:")

    for feature in feature_types:
        for child in feature:
            if local_name(child) == "Name":
                print("-", child.text)

    expected = "g_nowcasting:view_nowcasting"

    names = [
        child.text
        for feature in feature_types
        for child in feature
        if local_name(child) == "Name"
    ]

    if expected not in names:
        raise RuntimeError(
            "No se encontró la capa " + expected
        )

    print("\n===================================")
    print("WFS ACCESIBLE CORRECTAMENTE")
    print("CAPA NOWCASTING IDENTIFICADA")
    print("===================================")

except requests.exceptions.Timeout:
    print("ERROR: TIEMPO DE CONEXION AGOTADO")
    raise

except requests.exceptions.RequestException as error:
    print("ERROR DE CONEXION:", error)
    raise
