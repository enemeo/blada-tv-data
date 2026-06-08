import json
import requests
from datetime import datetime, timedelta

def normalizar(texto):
    return (texto or "").lower().strip()

def cargar_videos_actuales():
    try:
        with open("partidos.json", "r", encoding="utf-8") as f:
            datos = json.load(f)
        return datos
    except:
        return []

def buscar_video(local, visitante, anteriores):
    for p in anteriores:
        if normalizar(p.get("equipoLocal")) == normalizar(local) and normalizar(p.get("equipoVisitante")) == normalizar(visitante):
            return p.get("videoUrl", "")
    return ""

def es_importante(liga, local, visitante):
    texto = f"{liga} {local} {visitante}".lower()

    bloqueados = ["women", "u17", "u18", "u19", "u20", "u21", "u23", "youth"]

    if any(b in texto for b in bloqueados):
        return False

    importantes = [
        "friendly",
        "world cup",
        "copa america",
        "libertadores",
        "champions league",
        "europa league",
        "uefa",
        "premier league",
        "la liga",
        "serie a",
        "bundesliga",
        "ligue 1",
        "peru",
        "spain",
        "france",
        "argentina",
        "brazil",
        "colombia",
        "mexico",
        "uruguay",
        "chile"
    ]

    return any(i in texto for i in importantes)

anteriores = cargar_videos_actuales()
partidos = []

fechas = [
    datetime.now(),
    datetime.now() + timedelta(days=1)
]

for fecha in fechas:
    fecha_api = fecha.strftime("%Y-%m-%d")

    url = f"https://www.thesportsdb.com/api/v1/json/3/eventsday.php?d={fecha_api}&s=Soccer"

    try:
        r = requests.get(url, timeout=20)
        data = r.json()

        eventos = data.get("events") or []

        for e in eventos:
            liga = e.get("strLeague") or "Fútbol"
            local = e.get("strHomeTeam") or ""
            visitante = e.get("strAwayTeam") or ""

            if not local or not visitante:
                continue

            if not es_importante(liga, local, visitante):
                continue

            video = buscar_video(local, visitante, anteriores)

            partidos.append({
                "id": len(partidos) + 1,
                "liga": liga,
                "hora": e.get("strTime") or "",
                "fecha": fecha.strftime("%d/%m"),
                "equipoLocal": local,
                "equipoVisitante": visitante,
                "logoLocal": "",
                "logoVisitante": "",
                "estado": e.get("strStatus") or "Programado",
                "videoUrl": video
            })

    except Exception as error:
        print("Error:", error)

if not partidos:
    partidos.append({
        "id": 1,
        "liga": "Amistoso",
        "hora": "9:00 pm",
        "fecha": datetime.now().strftime("%d/%m"),
        "equipoLocal": "Perú",
        "equipoVisitante": "España",
        "logoLocal": "",
        "logoVisitante": "",
        "estado": "Programado",
        "videoUrl": buscar_video("Perú", "España", anteriores)
    })

with open("partidos.json", "w", encoding="utf-8") as f:
    json.dump(partidos, f, ensure_ascii=False, indent=2)

print("Partidos actualizados:", len(partidos))
