import json
import requests
from datetime import datetime, timedelta

def normalizar(t):
    return (t or "").lower().strip()

def cargar_anteriores():
    try:
        with open("partidos.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def buscar_video(local, visitante, anteriores):
    for p in anteriores:
        if normalizar(p.get("equipoLocal")) == normalizar(local) and normalizar(p.get("equipoVisitante")) == normalizar(visitante):
            return p.get("videoUrl", "")
    return ""

def aceptar_partido(liga, local, visitante, estado):
    texto = f"{liga} {local} {visitante}".lower()

    bloqueados = [
        "women", "femenino", "u17", "u18", "u19", "u20", "u21", "u23",
        "youth", "primera b", "reserva", "reserve"
    ]

    if any(b in texto for b in bloqueados):
        return False

    if estado in ["FT", "AET", "PEN"]:
        return False

    importantes = [
        "friendly",
        "world cup",
        "copa america",
        "libertadores",
        "champions",
        "uefa",
        "eliminatorias",
        "qualifiers",
        "peru",
        "spain",
        "france",
        "argentina",
        "brazil",
        "colombia",
        "uruguay",
        "chile",
        "mexico"
    ]

    return any(i in texto for i in importantes)

anteriores = cargar_anteriores()
partidos = []

for dias in range(0, 3):
    fecha = datetime.now() + timedelta(days=dias)
    fecha_api = fecha.strftime("%Y-%m-%d")

    url = f"https://www.thesportsdb.com/api/v1/json/3/eventsday.php?d={fecha_api}&s=Soccer"

    try:
        data = requests.get(url, timeout=20).json()
        eventos = data.get("events") or []

        for e in eventos:
            liga = e.get("strLeague") or "Fútbol"
            local = e.get("strHomeTeam") or ""
            visitante = e.get("strAwayTeam") or ""
            estado = e.get("strStatus") or "Programado"

            if not local or not visitante:
                continue

            if not aceptar_partido(liga, local, visitante, estado):
                continue

            partidos.append({
                "id": len(partidos) + 1,
                "liga": liga,
                "hora": e.get("strTime") or "",
                "fecha": fecha.strftime("%d/%m"),
                "equipoLocal": local,
                "equipoVisitante": visitante,
                "logoLocal": "",
                "logoVisitante": "",
                "estado": estado,
                "videoUrl": buscar_video(local, visitante, anteriores)
            })

    except Exception as e:
        print("Error:", e)

# respaldo si la fuente gratis no devuelve partidos buenos
if not partidos:
    partidos.append({
        "id": 1,
        "liga": "Amistoso",
        "hora": "9:00 pm",
        "fecha": datetime.now().strftime("%d/%m"),
        "equipoLocal": "Perú",
        "equipoVisitante": "España",
        "logoLocal": "https://media.api-sports.io/football/teams/30.png",
        "logoVisitante": "https://media.api-sports.io/football/teams/9.png",
        "estado": "Programado",
        "videoUrl": buscar_video("Perú", "España", anteriores)
    })

with open("partidos.json", "w", encoding="utf-8") as f:
    json.dump(partidos, f, ensure_ascii=False, indent=2)

print("Partidos actualizados:", len(partidos))
