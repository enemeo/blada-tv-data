import json
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime

URLS_ESPN = [
    {
        "url": "https://www.espn.com.pe/futbol/calendario/_/liga/fifa.friendly",
        "liga": "Amistoso"
    },
    {
        "url": "https://www.espn.com.pe/futbol/calendario/_/liga/fifa.world",
        "liga": "Copa Mundial"
    }
]

def limpiar(texto):
    return re.sub(r"\s+", " ", texto or "").strip()

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

anteriores = cargar_anteriores()
partidos = []

headers = {
    "User-Agent": "Mozilla/5.0"
}

for fuente in URLS_ESPN:
    try:
        html = requests.get(fuente["url"], headers=headers, timeout=20).text
        soup = BeautifulSoup(html, "html.parser")

        fecha_actual = datetime.now().strftime("%d/%m")

        for h2 in soup.find_all(["h2", "h3"]):
            texto_fecha = limpiar(h2.get_text())

            if "Lunes" in texto_fecha or "Martes" in texto_fecha or "Miércoles" in texto_fecha or "Jueves" in texto_fecha or "Viernes" in texto_fecha or "Sábado" in texto_fecha or "Domingo" in texto_fecha:
                fecha_actual = texto_fecha

            tabla = h2.find_next("table")
            if not tabla:
                continue

            filas = tabla.find_all("tr")

            for fila in filas:
                celdas = fila.find_all("td")
                if len(celdas) < 2:
                    continue

                texto = limpiar(fila.get_text(" "))

                if " v " not in texto:
                    continue

                partes = texto.split(" v ")
                if len(partes) < 2:
                    continue

                local = limpiar(partes[0])
                resto = limpiar(partes[1])

                hora_match = re.search(r"(\d{1,2}:\d{2}\s?[AP]M)", resto, re.IGNORECASE)
                hora = hora_match.group(1) if hora_match else ""

                visitante = resto
                if hora:
                    visitante = limpiar(resto.replace(hora, ""))

                if not local or not visitante:
                    continue

                if any(b in f"{local} {visitante}".lower() for b in ["u17", "u18", "u19", "u20", "u21", "u23", "women", "femenino"]):
                    continue

                partidos.append({
                    "id": len(partidos) + 1,
                    "liga": fuente["liga"],
                    "hora": hora,
                    "fecha": fecha_actual,
                    "equipoLocal": local,
                    "equipoVisitante": visitante,
                    "logoLocal": "",
                    "logoVisitante": "",
                    "estado": "Programado",
                    "videoUrl": buscar_video(local, visitante, anteriores)
                })

    except Exception as e:
        print("Error ESPN:", fuente["url"], e)

with open("partidos.json", "w", encoding="utf-8") as f:
    json.dump(partidos, f, ensure_ascii=False, indent=2)

print("Partidos ESPN actualizados:", len(partidos))
