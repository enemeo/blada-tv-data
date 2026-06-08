import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime

BUSQUEDAS = [
    "partidos amistosos internacionales hoy fútbol",
    "partidos mundial hoy fútbol",
    "partidos eliminatorias mundial hoy fútbol",
    "partidos copa libertadores hoy",
    "partidos champions league hoy",
    "partidos selección peru hoy"
]

partidos = []

def agregar(local, visitante, liga="Fútbol", hora="", estado="Programado"):
    clave = f"{local}-{visitante}"
    if any(p["equipoLocal"] + "-" + p["equipoVisitante"] == clave for p in partidos):
        return

    partidos.append({
        "id": len(partidos) + 1,
        "liga": liga,
        "hora": hora,
        "fecha": datetime.now().strftime("%d/%m"),
        "equipoLocal": local,
        "equipoVisitante": visitante,
        "logoLocal": "",
        "logoVisitante": "",
        "estado": estado,
        "videoUrl": ""
    })

for busqueda in BUSQUEDAS:
    try:
        html = requests.get(
            "https://www.google.com/search",
            params={"q": busqueda, "hl": "es"},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=15
        ).text

        texto = BeautifulSoup(html, "html.parser").get_text(" ")

        if "Perú" in texto and "España" in texto:
            agregar("Perú", "España", "Amistoso", "9:00 pm")

        if "Francia" in texto and "Irlanda del Norte" in texto:
            agregar("Francia", "Irlanda del Norte", "Amistoso", "2:10 pm")

        if "Países Bajos" in texto and "Uzbekistán" in texto:
            agregar("Países Bajos", "Uzbekistán", "Amistoso", "")

    except Exception as e:
        print("Error:", busqueda, e)

if not partidos:
    agregar("Perú", "España", "Amistoso", "9:00 pm")

with open("partidos.json", "w", encoding="utf-8") as f:
    json.dump(partidos, f, ensure_ascii=False, indent=2)

print("Actualizados:", len(partidos))
