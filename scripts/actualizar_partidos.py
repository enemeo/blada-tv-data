import json
import requests
from datetime import datetime, timedelta, timezone

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

PERU_TZ = timezone(timedelta(hours=-5))

CANAL_DEFAULT = "ESPN"
FUENTE_DEFAULT = "https://tvporinternet2.com/espn-en-vivo-por-internet.php"


def limpiar(texto):
    return (texto or "").strip()


def cargar_anteriores():
    try:
        with open("partidos.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []


def buscar_dato_anterior(local, visitante, anteriores, campo, default=""):
    for p in anteriores:
        if (
            limpiar(p.get("equipoLocal")).lower() == limpiar(local).lower()
            and limpiar(p.get("equipoVisitante")).lower() == limpiar(visitante).lower()
        ):
            return p.get(campo, default)
    return default


def estado_espn(estado):
    texto = f"{estado.get('name', '')} {estado.get('detail', '')}".lower()

    if "final" in texto:
        return "Finalizado"

    if "in progress" in texto or "halftime" in texto or "live" in texto:
        return "En progreso"

    return "Programado"


def convertir_fecha_hora_peru(fecha_hora):
    try:
        dt_utc = datetime.fromisoformat(fecha_hora.replace("Z", "+00:00"))
        dt_peru = dt_utc.astimezone(PERU_TZ)

        hora = dt_peru.strftime("%I:%M %p").lstrip("0")
        fecha = dt_peru.strftime("%d/%m")

        return dt_peru, hora, fecha
    except:
        return None, "", ""


def partido_ya_paso(dt_peru, estado):
    if estado == "En progreso":
        return False

    if estado == "Finalizado":
        return True

    if not dt_peru:
        return False

    ahora = datetime.now(PERU_TZ)
    return ahora > dt_peru + timedelta(hours=2)


anteriores = cargar_anteriores()
partidos = []

for dias in range(0, 4):
    fecha = datetime.now(PERU_TZ) + timedelta(days=dias)
    fecha_api = fecha.strftime("%Y%m%d")

    for codigo_liga, nombre_liga in LIGAS_ESPN:
        url = (
            f"https://site.api.espn.com/apis/site/v2/"
            f"sports/soccer/{codigo_liga}/scoreboard"
        )

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

                home = next(
                    (c for c in competidores if c.get("homeAway") == "home"),
                    competidores[0]
                )

                away = next(
                    (c for c in competidores if c.get("homeAway") == "away"),
                    competidores[1]
                )

                local = limpiar(home.get("team", {}).get("displayName"))
                visitante = limpiar(away.get("team", {}).get("displayName"))

                if not local or not visitante:
                    continue

                texto = f"{nombre_liga} {local} {visitante}".lower()

                if any(
                    x in texto
                    for x in [
                        "women",
                        "femenino",
                        "u17",
                        "u18",
                        "u19",
                        "u20",
                        "u21",
                        "u23"
                    ]
                ):
                    continue

                estado = estado_espn(evento.get("status", {}).get("type", {}))

                dt_peru, hora, fecha_app = convertir_fecha_hora_peru(
                    evento.get("date", "")
                )

                if partido_ya_paso(dt_peru, estado):
                    continue

                canal_anterior = buscar_dato_anterior(
                    local,
                    visitante,
                    anteriores,
                    "canal",
                    CANAL_DEFAULT
                )

                fuente_anterior = buscar_dato_anterior(
                    local,
                    visitante,
                    anteriores,
                    "fuenteUrl",
                    FUENTE_DEFAULT
                )

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
                    "canal": canal_anterior or CANAL_DEFAULT,
                    "fuenteUrl": fuente_anterior or FUENTE_DEFAULT,
                    "videoUrl": ""
                })

        except Exception as e:
            print("Error ESPN:", codigo_liga, e)


with open("partidos.json", "w", encoding="utf-8") as f:
    json.dump(partidos, f, ensure_ascii=False, indent=2)

print("Partidos actualizados:", len(partidos))
