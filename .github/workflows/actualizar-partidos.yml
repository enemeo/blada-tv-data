import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime

BUSQUEDAS = [
    "partidos amistosos internacionales hoy fútbol",
    "partidos copa mundial fútbol hoy",
    "partidos eliminatorias mundial hoy fútbol",
    "partidos copa libertadores hoy",
    "partidos champions league hoy"
]

partidos = []

def agregar_partido(local, visitante, liga="Fútbol", hora="", fecha="", estado="Programado"):
    partidos.append({
        "id": len(partidos) + 1,
        "liga": liga,
        "hora": hora,
        "fecha": fecha,
        "equipoLocal": local,
        "equipoVisitante": visitante,
        "logoLocal": "",
        "logoVisitante": "",
        "estado": estado,
        "videoUrl": ""
    })

for busqueda in BUSQUEDAS:
    try:
        url = "https://www.google.com/search"
        params = {"q": busqueda, "hl": "es"}
        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        html = requests.get(url, params=params, headers=headers, timeout=15).text
        soup = BeautifulSoup(html, "html.parser")
        texto = soup.get_text(" ")

        # Por ahora dejamos ejemplo fijo mientras probamos el scraper
        if "Perú" in texto or "España" in texto:
            agregar_partido(
                local="Perú",
                visitante="España",
                liga="Amistoso",
                hora="9:00 pm",
                fecha=datetime.now().strftime("%d/%m"),
                estado="Programado"
            )

    except Exception as e:
        print("Error buscando:", busqueda, e)

# Si Google no devuelve nada, dejamos respaldo
if not partidos:
    agregar_partido(
        local="Perú",
        visitante="España",
        liga="Amistoso",
        hora="9:00 pm",
        fecha=datetime.now().strftime("%d/%m"),
        estado="Programado"
    )

with open("partidos.json", "w", encoding="utf-8") as f:
    json.dump(partidos, f, ensure_ascii=False, indent=2)

print("partidos.json actualizado con", len(partidos), "partidos")
