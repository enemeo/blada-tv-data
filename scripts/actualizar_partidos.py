import json
import requests
from datetime import datetime, timedelta

LIGAS_ESPN = [
    ("fifa.friendly", "Amistoso"),
    ("fifa.world", "Copa Mundial"),
    ("conmebol.libertadores", "Copa Libertadores"),
    ("uefa.champions", "Champions League"),
    ("uefa.europa", "Europa League"),
    ("esp.1", "LaLiga"),
    ("eng.1", "Premier League"),
    ("ita.1", "Serie A"),
    ("ger.1", "Bundesliga"),
    ("fra.1", "Ligue 1")
]

def limpiar(texto):
    return (texto or "").strip()

def cargar_anteriores():
    try:
        with open("partidos.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def buscar_video(local, visitante, anteriores):
    for p in anteriores:
        if limpiar(p.get("equipoLocal")).lower() == limpiar(local).lower() and limpiar(p.get("equipoVisitante")).lower() == limpiar(visitante).lower():
            return p.get("videoUrl", "")
    return ""

def estado_espn(estado):
    nombre = estado.get("name", "")
    detalle = estado.get("detail", "")
    texto = f"{nombre} {detalle}".lower()

    if "final" in texto:
        return "Finalizado"
    if "in progress" in texto or "halftime" in texto or "live" in texto:
        return "En progreso"
    return "Programado"

anteriores = cargar_anteriores()
partidos = []

for dias in range(0, 4):
    fecha = datetime.now() + timedelta(days=dias)
    fecha_api = fecha.strftime("%Y%m%d")
    fecha_app = fecha.strftime("%d/%m")

    for codigo_liga, nombre_liga in LIGAS_ESPN:
        url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{codigo_liga}/scoreboard"

        try:
            r = requests.get(
                url,
                params={
                    "dates": fecha_api,
                    "limit": 100,
                    "region": "pe",
                    "lang": "es"
                },
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=20
            )

            data = r.json()
            eventos = data.get("events", [])

            for evento in eventos:
                competidores = evento.get("competitions", [{}])[0].get("competitors", [])

                if len(competidores) < 2:
                    continue

                home = next((c for c in competidores if c.get("homeAway") == "home"), competidores[0])
                away = next((c for c in competidores if c.get("homeAway") == "away"), competidores[1])

                local = limpiar(home.get("team", {}).get("displayName"))
                visitante = limpiar(away.get("team", {}).get("displayName"))

                if not local or not visitante:
                    continue

                texto = f"{nombre_liga} {local} {visitante}".lower()
                if any(x in texto for x in ["women", "u17", "u18", "u19", "u20", "u21", "u23"]):
                    continue

                estado = estado_espn(evento.get("status", {}).get("type", {}))

                if estado == "Finalizado":
                    continue

                hora = evento.get("date", "")

                partidos.append({
                    "id": len(partidos) + 1,
                    "liga": nombre_liga,
                    "hora": hora,
                    "fecha": fecha_app,
                    "equipoLocal": local,
                    "equipoVisitante": visitante,
                    "logoLocal": home.get("team", {}).get("logo", ""),
                    "logoVisitante": away.get("team", {}).get("logo", ""),
                    "estado": estado,
                    "videoUrl": buscar_video(local, visitante, anteriores)
                })

        except Exception as e:
            print("Error ESPN API:", codigo_liga, e)

with open("partidos.json", "w", encoding="utf-8") as f:
    json.dump(partidos, f, ensure_ascii=False, indent=2)

print("Partidos ESPN API actualizados:", len(partidos))
