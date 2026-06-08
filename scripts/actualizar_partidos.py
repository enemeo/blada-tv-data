import json
import requests
from bs4 import BeautifulSoup

partidos = []

try:
    url = "https://www.google.com/search?q=partidos+amistosos+hoy"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    html = requests.get(url, headers=headers).text
    soup = BeautifulSoup(html, "html.parser")

    # EJEMPLO
    partidos.append({
        "id": 1,
        "liga": "Amistoso",
        "hora": "9:00 pm",
        "fecha": "08/06",
        "equipoLocal": "Perú",
        "equipoVisitante": "España",
        "logoLocal": "https://media.api-sports.io/football/teams/30.png",
        "logoVisitante": "https://media.api-sports.io/football/teams/9.png",
        "estado": "ATV / Movistar Deportes",
        "videoUrl": ""
    })

    with open("partidos.json", "w", encoding="utf-8") as f:
        json.dump(partidos, f, ensure_ascii=False, indent=2)

    print("partidos.json actualizado")

except Exception as e:
    print("Error:", e)
