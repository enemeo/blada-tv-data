import json
import requests

URL = "https://www.thesportsdb.com/api/v1/json/3/eventsday.php?d=2025-06-08&s=Soccer"

respuesta = requests.get(URL)
datos = respuesta.json()

partidos = []

if datos.get("events"):
    for evento in datos["events"]:
        partidos.append({
            "id": evento.get("idEvent"),
            "liga": evento.get("strLeague"),
            "hora": evento.get("strTime"),
            "fecha": evento.get("dateEvent"),
            "equipoLocal": evento.get("strHomeTeam"),
            "equipoVisitante": evento.get("strAwayTeam"),
            "logoLocal": "",
            "logoVisitante": "",
            "estado": evento.get("strStatus", "Programado"),
            "videoUrl": ""
        })

with open("partidos.json", "w", encoding="utf-8") as archivo:
    json.dump(partidos, archivo, ensure_ascii=False, indent=2)

print("Partidos actualizados")
