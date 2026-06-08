import json

partidos = [
    {
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
    }
]

with open("partidos.json", "w", encoding="utf-8") as f:
    json.dump(partidos, f, ensure_ascii=False, indent=2)

print("partidos.json actualizado")
