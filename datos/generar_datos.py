# -*- coding: utf-8 -*-
"""
Genera posiciones.json y partidos.json a partir de datos reales de
TheSportsDB (https://www.thesportsdb.com).

Usa la llave gratuita compartida ("123"). Esa llave limita algunos
endpoints (la tabla de posiciones y la lista de eventos por temporada
vienen truncadas), así que en vez de pedir la tabla ya armada, bajamos
jornada por jornada con /eventsround.php (sin tope de resultados) y
calculamos la tabla nosotros mismos a partir de los resultados. Esto
de paso nos da el calendario completo de la temporada.

Uso:
    python generar_datos.py
"""
import json
import os
import time
import unicodedata
from datetime import date, datetime, timedelta

import requests

from equipos import DISPLAY_NAMES, NAME_MAP
from escribir_datos_js import escribir_datos_js

API_KEY = "123"
BASE_URL = f"https://www.thesportsdb.com/api/v1/json/{API_KEY}"

TEMPORADA = "2026-2027"
# Liga de Expansión MX se quitó a petición del usuario (2026-08-03): el
# sitio se enfoca solo en Liga BBVA MX por ahora. Para traerla de vuelta,
# basta con agregar de nuevo la entrada "expansion".
LIGAS = {
    "bbva": {"id": 4350, "nombre": "Liga BBVA MX"},
}

MAX_JORNADAS = 25  # tope de seguridad; se detiene antes si una jornada viene vacía

# ventana de fechas que se guarda en partidos.json (la sección "Partidos"
# muestra un vistazo actual, no la temporada completa — eso ya vive en
# calendario.html)
DIAS_ANTES = 3
DIAS_DESPUES = 8

CARPETA_SALIDA = os.path.join(os.path.dirname(__file__), "salida")
os.makedirs(CARPETA_SALIDA, exist_ok=True)

# jornadas que ya terminaron (todos sus partidos en FT) no van a cambiar,
# así que se guardan aquí para no volver a pedirlas — con la llave gratuita
# compartida, bajar las 32 jornadas de las dos ligas EN CADA CORRIDA (cada
# 5 min desde GitHub Actions) agota la cuota y tira 429. Con caché, en
# temporada regular solo se piden de verdad la jornada en curso y la
# siguiente; el resto sale de aquí.
RUTA_CACHE = os.path.join(CARPETA_SALIDA, "cache_rondas.json")

peticiones_usadas = 0

# la llave gratuita ("123") es compartida por muchísimos proyectos, y desde
# las IPs de GitHub Actions el límite se siente mucho más agresivo que en
# una conexión normal (probablemente porque otros workflows de GitHub
# Actions ajenos a este proyecto están pegándole a la misma llave desde
# IPs parecidas al mismo tiempo). 1.2s de pausa no fue suficiente y tiró
# 429 dos corridas seguidas, así que se baja el ritmo y se le da más
# paciencia al reintento antes de rendirse.
PAUSA_ENTRE_PETICIONES = 2.5
REINTENTOS_429 = 6


def pedir(endpoint, params=None):
    global peticiones_usadas
    for intento in range(REINTENTOS_429 + 1):
        r = requests.get(f"{BASE_URL}/{endpoint}", params=params or {})
        if r.status_code == 429 and intento < REINTENTOS_429:
            espera = 8 * (intento + 1)
            print(f"   ! 429 Too Many Requests, esperando {espera}s antes de reintentar...")
            time.sleep(espera)
            continue
        r.raise_for_status()
        peticiones_usadas += 1
        time.sleep(PAUSA_ENTRE_PETICIONES)
        return r.json() or {}


def normalizar(nombre):
    sin_acentos = unicodedata.normalize("NFKD", nombre or "")
    sin_acentos = "".join(c for c in sin_acentos if not unicodedata.combining(c))
    return sin_acentos.lower().strip()


def mapear_equipo(nombre_api):
    abbr = NAME_MAP.get(normalizar(nombre_api))
    if not abbr:
        print(f"   ! equipo sin mapear: '{nombre_api}' — agrégalo en equipos.py")
        abbr = normalizar(nombre_api)[:3].upper()
    nombre = DISPLAY_NAMES.get(abbr, nombre_api)
    return abbr, nombre


MESES = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic']


def mapear_estado(status, fecha, hora, elapsed=None):
    if status == "FT":
        return "ft", "FINALIZADO"
    if status == "NS" or not status:
        return "ns", f"{fecha.day} {MESES[fecha.month - 1]} · {hora}"
    if status in ("1H", "HT", "2H", "ET", "BT", "P", "LIVE"):
        return "live", f"{elapsed}'" if elapsed else "EN VIVO"
    # estados raros (suspendido, cancelado, pospuesto, etc.)
    return "ft", status


def cargar_cache():
    if os.path.exists(RUTA_CACHE):
        with open(RUTA_CACHE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def guardar_cache(cache):
    with open(RUTA_CACHE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def jornada_terminada(eventos):
    return bool(eventos) and all(ev.get("strStatus") == "FT" for ev in eventos)


def descargar_temporada(clave_liga, info_liga, cache):
    """Baja las jornadas de la liga (usando caché para las ya terminadas) y
    devuelve la lista cruda de eventos."""
    print(f"\n[{info_liga['nombre']}] descargando jornadas...")
    cache_liga = cache.setdefault(clave_liga, {})
    eventos = []
    for jornada in range(1, MAX_JORNADAS + 1):
        clave_jornada = str(jornada)

        if clave_jornada in cache_liga:
            partidos_jornada = cache_liga[clave_jornada]
            print(f"   jornada {jornada}: {len(partidos_jornada)} partidos (caché)")
            eventos.extend(partidos_jornada)
            continue

        data = pedir("eventsround.php", {
            "id": info_liga["id"], "r": jornada, "s": TEMPORADA,
        })
        partidos_jornada = data.get("events") or []
        if not partidos_jornada:
            break
        eventos.extend(partidos_jornada)
        print(f"   jornada {jornada}: {len(partidos_jornada)} partidos")

        if jornada_terminada(partidos_jornada):
            cache_liga[clave_jornada] = partidos_jornada

    print(f"   total: {len(eventos)} partidos en {info_liga['nombre']}")
    return eventos


def calcular_standings(eventos):
    tabla = {}

    def equipo(abbr, nombre):
        if abbr not in tabla:
            tabla[abbr] = {"abbr": abbr, "name": nombre, "pj": 0, "g": 0, "e": 0,
                           "p": 0, "pts": 0, "_gf": 0, "_gc": 0}
        return tabla[abbr]

    for ev in eventos:
        if ev.get("strStatus") != "FT":
            continue
        if ev.get("intHomeScore") is None or ev.get("intAwayScore") is None:
            continue

        home_abbr, home_nombre = mapear_equipo(ev["strHomeTeam"])
        away_abbr, away_nombre = mapear_equipo(ev["strAwayTeam"])
        gh, ga = int(ev["intHomeScore"]), int(ev["intAwayScore"])

        h, a = equipo(home_abbr, home_nombre), equipo(away_abbr, away_nombre)
        h["pj"] += 1; a["pj"] += 1
        h["_gf"] += gh; h["_gc"] += ga
        a["_gf"] += ga; a["_gc"] += gh

        if gh > ga:
            h["g"] += 1; h["pts"] += 3; a["p"] += 1
        elif ga > gh:
            a["g"] += 1; a["pts"] += 3; h["p"] += 1
        else:
            h["e"] += 1; a["e"] += 1; h["pts"] += 1; a["pts"] += 1

    filas = list(tabla.values())
    filas.sort(key=lambda t: (-t["pts"], -(t["_gf"] - t["_gc"]), -t["_gf"]))
    for f in filas:
        del f["_gf"], f["_gc"]
    return filas


def construir_partidos(eventos, info_liga):
    hoy = date.today()
    desde = hoy - timedelta(days=DIAS_ANTES)
    hasta = hoy + timedelta(days=DIAS_DESPUES)

    partidos = []
    for ev in eventos:
        fecha_str = ev.get("dateEvent")
        if not fecha_str:
            continue
        fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        if not (desde <= fecha <= hasta):
            continue

        home_abbr, home_nombre = mapear_equipo(ev["strHomeTeam"])
        away_abbr, away_nombre = mapear_equipo(ev["strAwayTeam"])

        hora = (ev.get("strTimeLocal") or ev.get("strTime") or "00:00:00")[:5]
        fecha_iso = f"{fecha_str}T{hora}:00"
        estado, tiempo = mapear_estado(ev.get("strStatus"), fecha, hora)

        if fecha == hoy:
            dia = "hoy"
        elif estado == "ns":
            dia = "proximo"
        else:
            dia = "pasado"

        partido = {
            "id": f"{home_abbr}-{away_abbr}-{ev['idEvent']}".lower(),
            "competition": info_liga["nombre"],
            "round": f"Jornada {ev.get('intRound', '?')}",
            "home": home_nombre, "homeAbbr": home_abbr,
            "away": away_nombre, "awayAbbr": away_abbr,
            "homeScore": int(ev["intHomeScore"]) if ev.get("intHomeScore") is not None else None,
            "awayScore": int(ev["intAwayScore"]) if ev.get("intAwayScore") is not None else None,
            "status": estado,
            "time": tiempo,
            "venue": ev.get("strVenue") or "Por confirmar",
            "date": f"{fecha.day} {MESES[fecha.month - 1]} {fecha.year}",
            "day": dia,
        }
        if estado == "ns":
            partido["kickoff"] = fecha_iso
        partidos.append((fecha_str, hora, partido))

    return partidos


def main():
    standings = {}
    partidos = []
    cache = cargar_cache()

    for clave, info in LIGAS.items():
        eventos = descargar_temporada(clave, info, cache)
        standings[clave] = calcular_standings(eventos)
        partidos += construir_partidos(eventos, info)

    guardar_cache(cache)

    partidos.sort(key=lambda tupla: (tupla[0], tupla[1]))
    partidos = [partido for _, _, partido in partidos]

    ruta_pos = os.path.join(CARPETA_SALIDA, "posiciones.json")
    ruta_partidos = os.path.join(CARPETA_SALIDA, "partidos.json")

    with open(ruta_pos, "w", encoding="utf-8") as f:
        json.dump(standings, f, ensure_ascii=False, indent=2)
    with open(ruta_partidos, "w", encoding="utf-8") as f:
        json.dump(partidos, f, ensure_ascii=False, indent=2)

    # datos.js junta todos los .json de salida/ (incluido el medallero, si
    # existe) en un solo <script>, para que la página muestre datos reales
    # se abra como se abra (con servidor o con doble clic).
    ruta_datos_js, _ = escribir_datos_js()

    print(f"\nListo. Peticiones usadas: {peticiones_usadas}")
    print(f"Escrito: {ruta_pos} ({sum(len(v) for v in standings.values())} equipos)")
    print(f"Escrito: {ruta_partidos} ({len(partidos)} partidos en ventana de "
          f"{DIAS_ANTES} días atrás / {DIAS_DESPUES} días adelante)")
    print(f"Escrito: {ruta_datos_js}")


if __name__ == "__main__":
    main()
