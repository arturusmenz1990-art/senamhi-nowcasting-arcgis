
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs
import json
import html
import re

PAGE = "https://www.senamhi.gob.pe/?p=reportes-nowcasting"
BASE = "https://idesep.senamhi.gob.pe/geoserver/g_nowcasting/ows"

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 SENAMHI-ArcGIS-Integration/1.0"
})

print("1. Consultando página SENAMHI...")

response = session.get(PAGE, timeout=40)
response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")

links = []

for a in soup.find_all("a", href=True):
    href = html.unescape(a["href"])
    url = urljoin(PAGE, href)

    if "g_nowcasting/ows" in url and "viewparams" in url:
        links.append(url)

# Buscar también URLs presentes en el HTML
if not links:
    matches = re.findall(
        r'https?://[^"\']*g_nowcasting/ows[^"\']*',
        response.text
    )
    links = [
        html.unescape(x).replace("&amp;", "&")
        for x in matches if "viewparams" in x
    ]

if not links:
    raise RuntimeError(
        "No se encontró el enlace WFS dinámico. "
        "Hay que revisar el HTML de la página."
    )

wfs_link = links[0]
query = parse_qs(urlparse(wfs_link).query)

viewparams = query.get("viewparams", [None])[0]

if not viewparams:
    raise RuntimeError("No se encontró viewparams.")

print("2. Reporte identificado:", viewparams)

params = {
    "service": "WFS",
    "version": "1.0.0",
    "request": "GetFeature",
    "typeName": "g_nowcasting:view_nowcasting",
    "outputFormat": "application/json",
    "srsName": "EPSG:4326",
    "maxFeatures": 30000,
    "viewparams": viewparams
}

print("3. Descargando entidades WFS...")

r = session.get(BASE, params=params, timeout=(20, 120))
r.raise_for_status()

try:
    data = r.json()
except ValueError:
    print(r.text[:2000])
    raise RuntimeError("El servidor no devolvió JSON válido.")

features = data.get("features", [])

if not features:
    raise RuntimeError("El WFS no devolvió polígonos.")

print("4. DESCARGA EXITOSA")
print("Cantidad de entidades:", len(features))
print("Atributos:", list(features[0]["properties"].keys()))
print("Geometría:", features[0]["geometry"]["type"])
print("Reporte:", viewparams)
