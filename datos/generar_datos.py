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
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import requests

from equipos import DISPLAY_NAMES, NAME_MAP, NAME_MAP_POR_LIGA
from escribir_datos_js import escribir_datos_js
from videos_youtube import actualizar_videos
import detalles_manuales

API_KEY = "123"
BASE_URL = f"https://www.thesportsdb.com/api/v1/json/{API_KEY}"

TEMPORADA = "2026-2027"
# Liga de Expansión MX se quitó a petición del usuario (2026-08-03): el
# sitio se enfoca solo en Liga BBVA MX por ahora. Para traerla de vuelta,
# basta con agregar de nuevo la entrada "expansion".
#
# Argentina y Brasil se agregaron 2026-08-07 (a petición del usuario, con
# la llave gratuita "123" — todavía no hay llave de pago para TheSportsDB).
# OJO: cada una trae su propia "temporada" porque la API no usa el mismo
# formato para todas las ligas — Liga BBVA MX es "2026-2027", pero
# Argentina y Brasil solo responden con el año suelto "2026" (probado a
# mano contra la API antes de escribirlo aquí). Si el año que viene deja
# de traer partidos, es lo primero a revisar.
#
# Premier League y LaLiga se agregaron 2026-08-19 — a diferencia de
# Argentina/Brasil, estas dos sí usan el mismo formato de temporada que
# Liga BBVA MX ("2026-2027"), comprobado a mano contra la API antes de
# escribirlo aquí.
#
# Serie A y Bundesliga se agregaron 2026-08-26, mismo formato de
# temporada que Premier/LaLiga ("2026-2027"), comprobado a mano.
#
# "continente" es lo que usan generar_america.py/generar_europa.py (ver
# esos archivos) para saber qué mitad de LIGAS le toca a cada cron —
# América y Europa corren en workflows separados desde el 2026-08-26
# para que cada uno tarde menos y uno no bloquee al otro.
LIGAS = {
    "bbva": {"id": 4350, "nombre": "Liga BBVA MX", "temporada": TEMPORADA, "continente": "america"},
    "argentina": {"id": 4406, "nombre": "Liga Profesional Argentina", "temporada": "2026", "continente": "america"},
    "brasil": {"id": 4351, "nombre": "Brasileirão Serie A", "temporada": "2026", "continente": "america"},
    "premier": {"id": 4328, "nombre": "Premier League", "temporada": "2026-2027", "continente": "europa"},
    "laliga": {"id": 4335, "nombre": "LaLiga", "temporada": "2026-2027", "continente": "europa"},
    "seriea": {"id": 4332, "nombre": "Serie A", "temporada": "2026-2027", "continente": "europa"},
    "bundesliga": {"id": 4331, "nombre": "Bundesliga", "temporada": "2026-2027", "continente": "europa"},
}

# 25 alcanzaba de sobra para Liga BBVA MX (17 jornadas), pero el
# Brasileirao juega 38 jornadas (20 equipos, todos contra todos ida y
# vuelta) — hay que subir el tope o su tabla se quedaría incompleta a
# mitad de temporada. No afecta a las ligas más cortas: el bucle ya se
# detiene solo en cuanto una jornada viene vacía.
MAX_JORNADAS = 40  # tope de seguridad; se detiene antes si una jornada viene vacía

# Leagues Cup 2026: no es una liga normal (25 jornadas, tabla única) — es un
# torneo aparte, formato suizo, solo 3 rondas, y Liga MX contra MLS siempre.
# Por eso se maneja con sus propias funciones más abajo, no dentro de LIGAS.
LEAGUES_CUP_ID = 5281
LEAGUES_CUP_TEMPORADA = "2026"
LEAGUES_CUP_RONDAS = 3  # fase de grupos
# fase eliminatoria (cuartos, semis, final): ver descargar_leagues_cup()
# para la explicación completa de por qué no es 4, 5, 6...
LEAGUES_CUP_RONDAS_ELIMINACION = range(125, 131)

LIGA_MX_ABBRS = {"AME", "ATE", "ATL", "SLP", "GDL", "CRZ", "JUA", "LEO", "MTY",
                  "TIJ", "NEC", "PAC", "PUE", "PUM", "QRO", "SAN", "TIG", "TOL"}
MLS_ABBRS = {"AUS", "CLT", "CHI", "CIN", "CLB", "DAL", "MIA", "LAF", "MNU",
             "NSH", "NYC", "ORL", "PHI", "POR", "RSL", "SDG", "SEA", "VAN"}

# Liga Profesional Argentina 2026: NO es una tabla única — son 2 zonas de
# 15 equipos cada una (Zona A / Zona B), formato real de la AFA para el
# Apertura/Clausura 2026 (confirmado 2026-08-19: La Nación, "Las zonas A y
# B del Apertura y Clausura 2026"). Cada equipo juega 14 partidos dentro
# de su zona + 1 interzonal; el interzonal NO cuenta para la tabla de
# ninguna zona (no hay una zona "dueña" de ese resultado), así que
# calcular_standings_argentina() solo suma partidos entre dos equipos de
# la MISMA zona, igual criterio que ya usa Leagues Cup con sus dos tablas.
# La API (TheSportsDB) no manda esta división (strGroup viene vacío), por
# eso se mantiene a mano aquí — si la AFA cambia las zonas de un año a
# otro, hay que actualizar esta lista.
ARGENTINA_ZONA_A = {"BOC", "IND", "SLO", "RIE", "TAL", "INS", "PLA", "VEL",
                     "ELP", "GEM", "LAN", "NOB", "DEJ", "CCO", "UNI"}
ARGENTINA_ZONA_B = {"RIV", "RAC", "HUR", "BAR", "BEL", "ERC", "ARG", "TIA",
                     "GLP", "IRV", "BAN", "ROS", "ALD", "ATU", "SAR"}

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

# generar_america.py y generar_europa.py corren como workflows
# SEPARADOS, cada uno con su propio checkout limpio de git — así que
# cuando corre el de América, el archivo que generó el de Europa (o
# viceversa) NO existe en ese checkout (posiciones_europa.json/
# partidos_europa.json nunca se commitean al repo, solo se suben por
# FTP). Sin este paso, escribir_datos_js() armaría un datos.js con solo
# la mitad del sitio y lo subiría por encima del bueno. Se baja del
# sitio en vivo lo último que de verdad se publicó, y solo si esta
# corrida no generó ya su propia versión más fresca.
SITIO_EN_VIVO = "https://pizarramx.com.mx/datos/salida/"


def sincronizar_otro_continente(nombre_archivo):
    ruta_local = os.path.join(CARPETA_SALIDA, nombre_archivo)
    if os.path.exists(ruta_local):
        return
    try:
        r = requests.get(f"{SITIO_EN_VIVO}{nombre_archivo}", timeout=15)
        r.raise_for_status()
        with open(ruta_local, "w", encoding="utf-8") as f:
            f.write(r.text)
        print(f"   (sincronizado {nombre_archivo} del sitio en vivo)")
    except Exception as err:
        print(f"   ! no se pudo traer {nombre_archivo} del sitio en vivo: {err}")

peticiones_usadas = 0

# la llave gratuita ("123") es compartida por muchísimos proyectos, y desde
# las IPs de GitHub Actions el límite se siente mucho más agresivo que en
# una conexión normal (probablemente porque otros workflows de GitHub
# Actions ajenos a este proyecto están pegándole a la misma llave desde
# IPs parecidas al mismo tiempo). 1.2s de pausa no fue suficiente y tiró
# 429 dos corridas seguidas, así que se baja el ritmo y se le da más
# paciencia al reintento antes de rendirse.
PAUSA_ENTRE_PETICIONES = 2.5
# Bajado de 6 reintentos (hasta 168s de espera en el peor caso, una sola
# petición) a 4 (máx. 60s) el 2026-08-07, al agregar Argentina y Brasil:
# con 3 ligas en vez de 1, una corrida que se traba en reintentos largos
# tiene más probabilidad de encimarse con la siguiente programada (ver
# el "concurrency" en partidos.yml). Si una petición de verdad falla tras
# 4 intentos, no se pierde nada: el caché hace que se vuelva a intentar
# sola en la siguiente corrida, 10 minutos después.
REINTENTOS_429 = 4


def pedir(endpoint, params=None):
    global peticiones_usadas
    for intento in range(REINTENTOS_429 + 1):
        r = requests.get(f"{BASE_URL}/{endpoint}", params=params or {})
        if r.status_code == 429 and intento < REINTENTOS_429:
            espera = 6 * (intento + 1)
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


def mapear_equipo(nombre_api, liga_clave=None):
    """liga_clave desambigua nombres que la API manda igual de corto para
    dos clubes distintos (ej. "Santos" es Santos Laguna en Liga BBVA MX
    pero Santos FC en Brasil) — se revisa NAME_MAP_POR_LIGA primero, y
    solo si no hay una excepción ahí se usa el NAME_MAP general."""
    nombre_norm = normalizar(nombre_api)
    abbr = NAME_MAP_POR_LIGA.get(liga_clave, {}).get(nombre_norm) or NAME_MAP.get(nombre_norm)
    if not abbr:
        print(f"   ! equipo sin mapear: '{nombre_api}' — agrégalo en equipos.py")
        abbr = nombre_norm[:3].upper()
    nombre = DISPLAY_NAMES.get(abbr, nombre_api)
    return abbr, nombre


MESES = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic']

# TheSportsDB guarda dateEvent en UTC. Un partido nocturno en México
# (ej. 19:00 CDMX = UTC-6) cruza la medianoche UTC y queda registrado
# como si fuera el DÍA SIGUIENTE — bug real detectado el 2026-08-28: el
# sitio mostraba Necaxa-Cruz Azul, Atlante-León y Tijuana-Pumas (los
# tres jugándose esa misma noche en México) como "próximo" en vez de
# "hoy", porque "día"/"hoy" se comparaban con la fecha UTC cruda en vez
# de la fecha en la zona horaria de México (la misma clase de bug que
# ya se había arreglado para la HORA mostrada, ver horaLocal() en
# pizarramx.js — esto es el mismo problema pero para el DÍA del calendario).
ZONA_MX = ZoneInfo("America/Mexico_City")


def fecha_local_mx(fecha_str, hora_utc):
    """Convierte dateEvent (UTC) + hora UTC a la fecha de calendario en
    México — la que de verdad le importa a quien decide "hoy"/"mañana"
    desde acá, sin importar en qué huso corra el runner de GitHub
    Actions (UTC) ni en qué huso esté el estadio."""
    dt_utc = datetime.strptime(f"{fecha_str} {hora_utc}", "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
    return dt_utc.astimezone(ZONA_MX).date()


def mapear_estado(status, fecha, hora, elapsed=None):
    if status == "FT":
        return "ft", "FINALIZADO"
    if status == "NS" or not status:
        return "ns", f"{fecha.day} {MESES[fecha.month - 1]} · {hora}"
    if status in ("1H", "HT", "2H", "ET", "BT", "P", "LIVE"):
        return "live", f"{elapsed}'" if elapsed else "EN VIVO"
    # estados raros (suspendido, cancelado, pospuesto, etc.)
    return "ft", status


def mapear_estado_en_vivo(status, progreso):
    """livescore.php manda un status más detallado que eventsround.php
    (separa 1er/2do tiempo, medio tiempo). Devuelve (None, None) si no
    reconoce el status, para no pisar con basura lo que ya había."""
    if status == "HT":
        return "live", "MEDIO TIEMPO"
    if status in ("1H", "2H", "ET", "BT", "P", "LIVE"):
        return "live", f"{progreso}'" if progreso else "EN VIVO"
    if status in ("FT", "AET", "PEN"):
        return "ft", "FINALIZADO"
    return None, None


def cargar_cache(ruta=RUTA_CACHE):
    # ruta es parámetro (no siempre RUTA_CACHE global) desde que
    # generar_america.py/generar_europa.py corren aparte: cada cron
    # necesita su PROPIO caché de rondas, si no uno le pisa al otro las
    # rondas que cacheó (ver main() más abajo).
    if os.path.exists(ruta):
        with open(ruta, encoding="utf-8") as f:
            return json.load(f)
    return {}


def guardar_cache(cache, ruta=RUTA_CACHE):
    with open(ruta, "w", encoding="utf-8") as f:
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
            "id": info_liga["id"], "r": jornada, "s": info_liga.get("temporada", TEMPORADA),
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


def pedir_livescores(id_liga, liga_clave=None):
    """eventsround.php (arriba) es el calendario: no se mueve mientras el
    partido está en curso. livescore.php sí trae marcador y minuto en
    tiempo real — este es el que faltaba, y por eso los partidos en vivo
    se quedaban pegados hasta que alguien los editaba a mano.

    OJO: livescore.php usa un idEvent DISTINTO al de eventsround.php para
    el mismo partido real (comprobado con un caso real: Inter Miami vs
    Atlético San Luis tenía 2559160 en uno y 2483224 en el otro). Cruzar
    solo por idEvent pierde partidos en silencio, así que se devuelven dos
    diccionarios: uno por idEvent (cuando sí coincide) y otro por el par
    de equipos (abreviación local-visitante) como respaldo."""
    try:
        data = pedir("livescore.php", {"id": id_liga})
    except Exception as err:
        print(f"   ! no se pudo pedir livescore.php (liga {id_liga}): {err}")
        return {}, {}
    eventos_vivos = data.get("livescore") or []

    por_id, por_equipos = {}, {}
    for ev in eventos_vivos:
        if ev.get("idEvent"):
            por_id[ev["idEvent"]] = ev
        home_abbr, _ = mapear_equipo(ev.get("strHomeTeam") or "", liga_clave)
        away_abbr, _ = mapear_equipo(ev.get("strAwayTeam") or "", liga_clave)
        por_equipos[(home_abbr, away_abbr)] = ev
    return por_id, por_equipos


def calcular_standings(eventos, liga_clave=None):
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

        home_abbr, home_nombre = mapear_equipo(ev["strHomeTeam"], liga_clave)
        away_abbr, away_nombre = mapear_equipo(ev["strAwayTeam"], liga_clave)
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


def descargar_leagues_cup(cache):
    """Baja la fase de grupos (rondas 1-3, numeración normal) y la fase
    eliminatoria de la Leagues Cup.

    OJO (descubierto 2026-08-26, cuartos de final desaparecidos del
    sitio): la fase eliminatoria NO sigue la numeración consecutiva de la
    de grupos — TheSportsDB salta directo a la ronda 125 para cuartos de
    final (comprobado a mano contra la API). No hay forma de saber de
    antemano en qué ronda van a caer semifinal y final, así que se
    revisa un rango fijo (125-130) completo en cada corrida en vez de
    parar en la primera vacía como hace la fase de grupos — una ronda de
    eliminación vacía HOY puede tener partidos mañana en cuanto se
    definan los cruces, así que tampoco se cachea vacía."""
    print(f"\n[Leagues Cup] descargando rondas...")
    cache_liga = cache.setdefault("leaguescup", {})
    eventos = []
    for ronda in range(1, LEAGUES_CUP_RONDAS + 1):
        clave_ronda = str(ronda)

        if clave_ronda in cache_liga:
            partidos_ronda = cache_liga[clave_ronda]
            print(f"   ronda {ronda}: {len(partidos_ronda)} partidos (caché)")
            eventos.extend(partidos_ronda)
            continue

        data = pedir("eventsround.php", {
            "id": LEAGUES_CUP_ID, "r": ronda, "s": LEAGUES_CUP_TEMPORADA,
        })
        partidos_ronda = data.get("events") or []
        eventos.extend(partidos_ronda)
        print(f"   ronda {ronda}: {len(partidos_ronda)} partidos")

        if jornada_terminada(partidos_ronda):
            cache_liga[clave_ronda] = partidos_ronda

    for ronda in LEAGUES_CUP_RONDAS_ELIMINACION:
        clave_ronda = str(ronda)

        if clave_ronda in cache_liga:
            partidos_ronda = cache_liga[clave_ronda]
            if partidos_ronda:
                print(f"   ronda {ronda} (eliminación): {len(partidos_ronda)} partidos (caché)")
                eventos.extend(partidos_ronda)
            continue

        data = pedir("eventsround.php", {
            "id": LEAGUES_CUP_ID, "r": ronda, "s": LEAGUES_CUP_TEMPORADA,
        })
        partidos_ronda = data.get("events") or []
        if not partidos_ronda:
            continue  # no se cachea: mañana puede que ya haya cruces
        eventos.extend(partidos_ronda)
        print(f"   ronda {ronda} (eliminación): {len(partidos_ronda)} partidos")

        if jornada_terminada(partidos_ronda):
            cache_liga[clave_ronda] = partidos_ronda

    print(f"   total: {len(eventos)} partidos en Leagues Cup")
    return eventos


def calcular_standings_leagues_cup(eventos):
    """A diferencia de una liga normal, la Leagues Cup no tiene UNA tabla:
    cada partido es Liga MX contra MLS, y arma DOS tablas independientes
    (una por liga de origen de cada equipo). Los 4 mejores de cada tabla
    avanzan a cuartos de final — no hay grupos."""
    tablas = {"ligamx": {}, "mls": {}}

    def equipo(tabla_key, abbr, nombre):
        tabla = tablas[tabla_key]
        if abbr not in tabla:
            tabla[abbr] = {"abbr": abbr, "name": nombre, "pj": 0, "g": 0, "e": 0,
                           "p": 0, "pts": 0, "_gf": 0, "_gc": 0}
        return tabla[abbr]

    def ubicar(abbr):
        if abbr in LIGA_MX_ABBRS:
            return "ligamx"
        if abbr in MLS_ABBRS:
            return "mls"
        return None

    rondas_de_grupo = {str(r) for r in range(1, LEAGUES_CUP_RONDAS + 1)}

    for ev in eventos:
        # la tabla es SOLO de la fase de grupos — los partidos de
        # eliminación (ronda 125+, ver descargar_leagues_cup) no cuentan
        # aquí, si no los "pj" de un equipo que sigue vivo en el torneo
        # se seguirían sumando después de que los grupos ya terminaron
        if ev.get("intRound") not in rondas_de_grupo:
            continue
        if ev.get("strStatus") != "FT":
            continue
        if ev.get("intHomeScore") is None or ev.get("intAwayScore") is None:
            continue

        home_abbr, home_nombre = mapear_equipo(ev["strHomeTeam"])
        away_abbr, away_nombre = mapear_equipo(ev["strAwayTeam"])
        tabla_home, tabla_away = ubicar(home_abbr), ubicar(away_abbr)
        if not tabla_home or not tabla_away:
            print(f"   ! Leagues Cup: no reconozco la liga de origen de "
                  f"'{home_abbr}' o '{away_abbr}' — revisa LIGA_MX_ABBRS/MLS_ABBRS")
            continue

        gh, ga = int(ev["intHomeScore"]), int(ev["intAwayScore"])
        h, a = equipo(tabla_home, home_abbr, home_nombre), equipo(tabla_away, away_abbr, away_nombre)
        h["pj"] += 1; a["pj"] += 1
        h["_gf"] += gh; h["_gc"] += ga
        a["_gf"] += ga; a["_gc"] += gh

        if gh > ga:
            h["g"] += 1; h["pts"] += 3; a["p"] += 1
        elif ga > gh:
            a["g"] += 1; a["pts"] += 3; h["p"] += 1
        else:
            h["e"] += 1; a["e"] += 1; h["pts"] += 1; a["pts"] += 1

    resultado = {}
    for clave, tabla in tablas.items():
        filas = list(tabla.values())
        filas.sort(key=lambda t: (-t["pts"], -(t["_gf"] - t["_gc"]), -t["_gf"]))
        for f in filas:
            del f["_gf"], f["_gc"]
        resultado[clave] = filas
    return resultado


def calcular_standings_argentina(eventos):
    """Igual que calcular_standings_leagues_cup pero para las 2 zonas de
    la Liga Profesional Argentina (ver ARGENTINA_ZONA_A/B arriba): cada
    zona es una tabla independiente, y un partido solo cuenta para la
    tabla de una zona si LOS DOS equipos son de esa misma zona (el
    interzonal, un partido por equipo contra la otra zona, no cuenta para
    ninguna tabla)."""
    tablas = {"zonaA": {}, "zonaB": {}}

    def equipo(zona, abbr, nombre):
        tabla = tablas[zona]
        if abbr not in tabla:
            tabla[abbr] = {"abbr": abbr, "name": nombre, "pj": 0, "g": 0, "e": 0,
                           "p": 0, "pts": 0, "_gf": 0, "_gc": 0}
        return tabla[abbr]

    def zona_de(abbr):
        if abbr in ARGENTINA_ZONA_A:
            return "zonaA"
        if abbr in ARGENTINA_ZONA_B:
            return "zonaB"
        return None

    for ev in eventos:
        if ev.get("strStatus") != "FT":
            continue
        if ev.get("intHomeScore") is None or ev.get("intAwayScore") is None:
            continue

        home_abbr, home_nombre = mapear_equipo(ev["strHomeTeam"], "argentina")
        away_abbr, away_nombre = mapear_equipo(ev["strAwayTeam"], "argentina")
        zona_home, zona_away = zona_de(home_abbr), zona_de(away_abbr)
        if not zona_home or not zona_away or zona_home != zona_away:
            continue  # interzonal, o algún equipo sin zona reconocida — no cuenta

        gh, ga = int(ev["intHomeScore"]), int(ev["intAwayScore"])
        h, a = equipo(zona_home, home_abbr, home_nombre), equipo(zona_away, away_abbr, away_nombre)
        h["pj"] += 1; a["pj"] += 1
        h["_gf"] += gh; h["_gc"] += ga
        a["_gf"] += ga; a["_gc"] += gh

        if gh > ga:
            h["g"] += 1; h["pts"] += 3; a["p"] += 1
        elif ga > gh:
            a["g"] += 1; a["pts"] += 3; h["p"] += 1
        else:
            h["e"] += 1; a["e"] += 1; h["pts"] += 1; a["pts"] += 1

    resultado = {}
    for clave, tabla in tablas.items():
        filas = list(tabla.values())
        filas.sort(key=lambda t: (-t["pts"], -(t["_gf"] - t["_gc"]), -t["_gf"]))
        for f in filas:
            del f["_gf"], f["_gc"]
        resultado[clave] = filas
    return resultado


def construir_partidos(eventos, info_liga, vivos_por_id=None, vivos_por_equipos=None, liga_clave=None):
    vivos_por_id = vivos_por_id or {}
    vivos_por_equipos = vivos_por_equipos or {}
    # "hoy" en hora de México, no la del runner (GitHub Actions corre en
    # UTC) — ver fecha_local_mx()/ZONA_MX arriba para el porqué.
    hoy = datetime.now(ZONA_MX).date()
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

        home_abbr, home_nombre = mapear_equipo(ev["strHomeTeam"], liga_clave)
        away_abbr, away_nombre = mapear_equipo(ev["strAwayTeam"], liga_clave)

        # strTime es la hora UTC real del partido; strTimeLocal es la hora
        # del ESTADIO (útil solo si el visitante estuviera en esa misma
        # ciudad). Antes se usaba strTimeLocal sin decir que era UTC/local
        # de nadie en particular, y el front-end la mostraba tal cual — un
        # visitante en otro país veía la hora del estadio como si fuera la
        # suya. Ahora se manda la hora UTC real con sufijo "Z", y cada
        # navegador la convierte a la hora local de quien esté viendo el
        # sitio (ver horaLocal() en pizarramx.js).
        hora = (ev.get("strTime") or ev.get("strTimeLocal") or "00:00:00")[:5]
        fecha_iso = f"{fecha_str}T{hora}:00Z"
        # fecha_mx: el día de calendario en México del kickoff real, NO el
        # dateEvent crudo de TheSportsDB (que es UTC y puede caer un día
        # después para partidos nocturnos mexicanos) — ver ZONA_MX arriba.
        fecha_mx = fecha_local_mx(fecha_str, hora)
        estado, tiempo = mapear_estado(ev.get("strStatus"), fecha_mx, hora)
        gh = int(ev["intHomeScore"]) if ev.get("intHomeScore") is not None else None
        ga = int(ev["intAwayScore"]) if ev.get("intAwayScore") is not None else None

        # si livescore.php tiene este partido, pisa marcador/estado con el
        # dato fresco (eventsround.php se queda atrás mientras está en curso).
        # primero por idEvent; si no coincide (pasa, ver nota en
        # pedir_livescores), por el par de equipos como respaldo
        en_vivo = vivos_por_id.get(ev.get("idEvent")) or vivos_por_equipos.get((home_abbr, away_abbr))
        if en_vivo:
            if en_vivo.get("intHomeScore") is not None:
                gh = int(en_vivo["intHomeScore"])
            if en_vivo.get("intAwayScore") is not None:
                ga = int(en_vivo["intAwayScore"])
            estado_vivo, tiempo_vivo = mapear_estado_en_vivo(en_vivo.get("strStatus"), en_vivo.get("strProgress"))
            if estado_vivo:
                estado, tiempo = estado_vivo, tiempo_vivo

        if fecha_mx == hoy:
            dia = "hoy"
        elif estado == "ns":
            dia = "proximo"
        else:
            dia = "pasado"

        # Leagues Cup: la fase eliminatoria no cae en una "jornada" con
        # número que le diga algo a nadie (ronda 125+, ver
        # descargar_leagues_cup) — se muestra como "Fase eliminatoria"
        # en vez de "Jornada 125".
        es_ronda_grupo = str(ev.get("intRound")) in {"1", "2", "3"}
        if info_liga["nombre"] == "Leagues Cup" and not es_ronda_grupo:
            etiqueta_ronda = "Fase eliminatoria"
        else:
            etiqueta_ronda = f"Jornada {ev.get('intRound', '?')}"

        partido = {
            "id": f"{home_abbr}-{away_abbr}-{ev['idEvent']}".lower(),
            "competition": info_liga["nombre"],
            "round": etiqueta_ronda,
            "home": home_nombre, "homeAbbr": home_abbr,
            "away": away_nombre, "awayAbbr": away_abbr,
            "homeScore": gh,
            "awayScore": ga,
            "status": estado,
            "time": tiempo,
            "venue": ev.get("strVenue") or "Por confirmar",
            "date": f"{fecha_mx.day} {MESES[fecha_mx.month - 1]} {fecha_mx.year}",
            "day": dia,
            # fecha cruda (YYYY-MM-DD): la usa videos_youtube.py para acotar
            # la búsqueda de resúmenes a partir de este día, no la consume
            # el front-end pero no estorba que viaje en partidos.json
            "fechaISO": fecha_str,
        }
        if estado == "ns":
            partido["kickoff"] = fecha_iso
        partidos.append((fecha_str, hora, partido))

    return partidos


def main(claves_ligas=None, sufijo="", con_leagues_cup=True, con_extras=True):
    """
    claves_ligas: lista de keys de LIGAS a procesar (None = todas — modo
        de siempre, para correr el script directo a mano).
    sufijo: se pega a los archivos de salida propios de esta corrida
        (posiciones{sufijo}.json, partidos{sufijo}.json,
        cache_rondas{sufijo}.json) para que generar_america.py y
        generar_europa.py (dos crons separados desde 2026-08-26, ver
        LIGAS más arriba) no se pisen el archivo entre sí. "" = nombres
        de siempre.
    con_leagues_cup: si esta corrida también baja la Leagues Cup (Liga
        MX vs MLS — solo tiene sentido en la de América).
    con_extras: si corre videos_youtube.py/detalles_manuales.py sobre
        los partidos de esta corrida (solo tiene sentido en la de
        América: los resúmenes y overrides manuales que ya existen son
        todos de Liga MX/Leagues Cup).
    """
    ligas = {k: v for k, v in LIGAS.items() if claves_ligas is None or k in claves_ligas}
    ruta_cache = os.path.join(CARPETA_SALIDA, f"cache_rondas{sufijo}.json")

    standings = {}
    partidos = []
    cache = cargar_cache(ruta_cache)

    for clave, info in ligas.items():
        eventos = descargar_temporada(clave, info, cache)
        # Argentina no tiene una tabla única (ver ARGENTINA_ZONA_A/B) —
        # el resto de las ligas sí.
        standings[clave] = (
            calcular_standings_argentina(eventos) if clave == "argentina"
            else calcular_standings(eventos, clave)
        )
        vivos_id, vivos_eq = pedir_livescores(info["id"], clave)
        print(f"   en vivo ahora mismo: {len(vivos_eq)} partido(s)")
        partidos += construir_partidos(eventos, info, vivos_id, vivos_eq, liga_clave=clave)

    if con_leagues_cup:
        eventos_lc = descargar_leagues_cup(cache)
        standings["leaguescup"] = calcular_standings_leagues_cup(eventos_lc)
        vivos_lc_id, vivos_lc_eq = pedir_livescores(LEAGUES_CUP_ID)
        print(f"   en vivo ahora mismo en Leagues Cup: {len(vivos_lc_eq)} partido(s)")
        partidos += construir_partidos(eventos_lc, {"nombre": "Leagues Cup"}, vivos_lc_id, vivos_lc_eq)

    guardar_cache(cache, ruta_cache)

    partidos.sort(key=lambda tupla: (tupla[0], tupla[1]))
    partidos = [partido for _, _, partido in partidos]

    detalles = None
    if con_extras:
        detalles = actualizar_videos(partidos)
        detalles = detalles_manuales.aplicar(partidos, detalles)

    ruta_pos = os.path.join(CARPETA_SALIDA, f"posiciones{sufijo}.json")
    ruta_partidos = os.path.join(CARPETA_SALIDA, f"partidos{sufijo}.json")

    with open(ruta_pos, "w", encoding="utf-8") as f:
        json.dump(standings, f, ensure_ascii=False, indent=2)
    with open(ruta_partidos, "w", encoding="utf-8") as f:
        json.dump(partidos, f, ensure_ascii=False, indent=2)

    if detalles is not None:
        ruta_detalles = os.path.join(CARPETA_SALIDA, "detalles.json")
        with open(ruta_detalles, "w", encoding="utf-8") as f:
            json.dump(detalles, f, ensure_ascii=False, indent=2)

    # si esta corrida es de un solo continente, hay que traer la mitad
    # que le toca al OTRO antes de armar el datos.js combinado (ver
    # sincronizar_otro_continente arriba)
    if sufijo == "_america":
        sincronizar_otro_continente("posiciones_europa.json")
        sincronizar_otro_continente("partidos_europa.json")
    elif sufijo == "_europa":
        sincronizar_otro_continente("posiciones_america.json")
        sincronizar_otro_continente("partidos_america.json")
        # detalles.json (videos/directo) solo lo genera la corrida de
        # América (con_extras=False acá) — si Europa no lo trae también,
        # su checkout de git (siempre nuevo) nunca lo tiene localmente, y
        # FTP-Deploy-Action, al subir a la MISMA carpeta datos/salida/
        # que usa América, lo borra del servidor creyendo que ya no
        # debería existir (sync tipo espejo contra su propio estado).
        # Bug real detectado el 2026-08-27: detalles.json daba 404 en
        # vivo aunque América lo generaba bien.
        sincronizar_otro_continente("detalles.json")

    # datos.js junta todos los .json de salida/ (incluido el de la OTRA
    # mitad del continente, recién sincronizada arriba) en un solo
    # <script>, para que la página muestre datos reales se abra como se
    # abra (con servidor o con doble clic).
    ruta_datos_js, _ = escribir_datos_js()

    print(f"\nListo. Peticiones usadas: {peticiones_usadas}")
    def contar_equipos(tabla):
        # "leaguescup" no es una lista plana como las demás: es
        # {"ligamx": [...], "mls": [...]}, así que hay que bajar un nivel
        return sum(contar_equipos(v) for v in tabla.values()) if isinstance(tabla, dict) else len(tabla)

    print(f"Escrito: {ruta_pos} ({sum(contar_equipos(v) for v in standings.values())} equipos)")
    print(f"Escrito: {ruta_partidos} ({len(partidos)} partidos en ventana de "
          f"{DIAS_ANTES} días atrás / {DIAS_DESPUES} días adelante)")
    if detalles is not None:
        print(f"Escrito: {ruta_detalles} ({len(detalles)} partidos con video)")
    print(f"Escrito: {ruta_datos_js}")


if __name__ == "__main__":
    # corrida manual directa: todas las ligas, Leagues Cup y
    # videos/detalles, con los nombres de archivo de siempre — igual que
    # antes de que existiera el split por continente (útil para probar
    # todo junto a mano, como en esta misma sesión).
    main(claves_ligas=None, sufijo="", con_leagues_cup=True, con_extras=True)
