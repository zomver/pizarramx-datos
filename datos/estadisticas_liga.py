# -*- coding: utf-8 -*-
"""
Genera estadisticas.json (goleadores, asistencias, tarjetas amarillas y
rojas, top 5 por liga) a partir de TheSportsDB.

Por qué un script/cron aparte de generar_datos.py:
- generar_datos.py corre cada 10 minutos (ver partidos.yml) y ya usa casi
  toda la cuota de la llave gratuita compartida "123" solo para
  calendario/resultados/tabla. No hay endpoint de "goleadores de la
  liga": lookuptimeline.php (goles/tarjetas de UN partido) hay que
  pedirlo partido por partido, y eso no cabe en el presupuesto de una
  corrida cada 10 min.
- Estos datos no cambian en vivo (no importa si el goleador del día se ve
  reflejado aquí 5 minutos o 20 horas después de anotar), así que corren
  una vez al día en su propio workflow (estadisticas.yml), desacoplado
  del de partidos.

Cómo evita re-pedir lo mismo cada día:
- cache_estadisticas.json guarda, por liga, el acumulado de goles /
  asistencias / tarjetas por jugador Y la lista de idEvent ya
  procesados. Cada corrida solo pide lookuptimeline.php de los partidos
  FT que todavía no estén en esa lista — un partido ya contado no se
  vuelve a pedir nunca.
- cache_rondas.json (el caché de jornadas que ya usa generar_datos.py)
  se lee aquí tal cual, de solo lectura: no se le agregan jornadas ni se
  reescribe. Así este script no compite por escribir el mismo archivo
  que partidos.yml actualiza cada 10 minutos — si una jornada todavía no
  está cacheada (está en curso), simplemente se vuelve a pedir por
  eventsround.php cada corrida diaria; es una sola llamada extra por
  liga, no vale la pena complicar el caché compartido por eso.

Salida: datos/salida/estadisticas.json, con esta forma (igual a
LIGA_STATS_EXTRA en pizarramx.js, para que el front-end la use tal
cual):
    {
      "bbva": {
        "goleadores": [{"player": "...", "abbr": "MTY", "value": 3}, ...],
        "asistencias": [...], "amarillas": [...], "rojas": [...]
      },
      "argentina": {...}, "brasil": {...}
    }

Uso:
    python estadisticas_liga.py
"""
import json
import os

from equipos import DISPLAY_NAMES
from generar_datos import (
    LIGAS,
    CARPETA_SALIDA,
    pedir,
    mapear_equipo,
    descargar_temporada,
)

RUTA_CACHE_ESTADISTICAS = os.path.join(CARPETA_SALIDA, "cache_estadisticas.json")
RUTA_SALIDA = os.path.join(CARPETA_SALIDA, "estadisticas.json")

TOP_N = 5


def cargar_cache_rondas():
    """Desde el 2026-08-26 el caché de jornadas ya no vive en un solo
    cache_rondas.json — generar_america.py/generar_europa.py (cron
    separado por continente, ver ese cambio) escriben cada uno el suyo.
    Se juntan los dos (claves de liga distintas, no hay pisado posible)
    para no perder el ahorro de caché en ninguna de las 7 ligas."""
    combinado = {}
    for nombre in ("cache_rondas_america.json", "cache_rondas_europa.json"):
        ruta = os.path.join(CARPETA_SALIDA, nombre)
        if os.path.exists(ruta):
            with open(ruta, encoding="utf-8") as f:
                combinado.update(json.load(f))
    return combinado


def cargar_cache_estadisticas():
    if os.path.exists(RUTA_CACHE_ESTADISTICAS):
        with open(RUTA_CACHE_ESTADISTICAS, encoding="utf-8") as f:
            return json.load(f)
    return {"procesados": [], "jugadores": {}}


def guardar_cache_estadisticas(cache):
    with open(RUTA_CACHE_ESTADISTICAS, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def jugador(cache_liga, id_jugador, nombre, abbr):
    if id_jugador not in cache_liga:
        cache_liga[id_jugador] = {
            "player": nombre, "abbr": abbr,
            "goles": 0, "asistencias": 0, "amarillas": 0, "rojas": 0,
        }
    # el nombre/equipo se refresca por si cambió de club en el mercado
    cache_liga[id_jugador]["player"] = nombre
    cache_liga[id_jugador]["abbr"] = abbr
    return cache_liga[id_jugador]


def procesar_timeline(timeline, liga_clave, cache_liga):
    """Suma al acumulado de cache_liga (dict idPlayer -> stats) los goles,
    asistencias y tarjetas de un partido. No hay endpoint de "goleadores
    de la liga" con la llave gratuita, así que se arma sumando partido
    por partido lo que trae lookuptimeline.php de cada uno."""
    for ev in timeline:
        tipo = ev.get("strTimeline")
        detalle = (ev.get("strTimelineDetail") or "")
        equipo_abbr, _ = mapear_equipo(ev.get("strTeam") or "", liga_clave)

        if tipo == "Goal":
            id_autor = ev.get("idPlayer")
            if id_autor:
                j = jugador(cache_liga, id_autor, ev.get("strPlayer") or "?", equipo_abbr)
                j["goles"] += 1

            id_asist = ev.get("idAssist")
            if id_asist and id_asist != "0" and ev.get("strAssist"):
                # el asistente es del mismo equipo que anotó
                j2 = jugador(cache_liga, id_asist, ev.get("strAssist"), equipo_abbr)
                j2["asistencias"] += 1

        elif tipo == "Card":
            id_jug = ev.get("idPlayer")
            if not id_jug:
                continue
            j = jugador(cache_liga, id_jug, ev.get("strPlayer") or "?", equipo_abbr)
            if "Yellow" in detalle:
                j["amarillas"] += 1
            elif "Red" in detalle:
                j["rojas"] += 1


def top5(cache_liga, campo):
    filas = [
        {"player": v["player"], "abbr": v["abbr"], "value": v[campo]}
        for v in cache_liga.values() if v[campo] > 0
    ]
    filas.sort(key=lambda f: -f["value"])
    return filas[:TOP_N]


def main():
    cache_rondas = cargar_cache_rondas()
    cache = cargar_cache_estadisticas()
    procesados = set(cache["procesados"])
    peticiones_timeline = 0

    salida = {}

    for liga_clave, info in LIGAS.items():
        print(f"\n[{info['nombre']}] revisando partidos terminados...")
        # copia: descargar_temporada puede agregar jornadas recién
        # terminadas al dict que recibe, y no queremos persistir eso
        # aquí (ver nota arriba: cache_rondas.json es de solo lectura
        # para este script)
        eventos = descargar_temporada(liga_clave, info, dict(cache_rondas))

        cache_liga = cache["jugadores"].setdefault(liga_clave, {})

        nuevos = [
            ev for ev in eventos
            if ev.get("strStatus") == "FT" and ev.get("idEvent") not in procesados
        ]
        print(f"   {len(nuevos)} partido(s) nuevo(s) por contar (de {len(eventos)} totales)")

        for ev in nuevos:
            id_evento = ev["idEvent"]
            try:
                data = pedir("lookuptimeline.php", {"id": id_evento})
            except Exception as err:
                print(f"   ! no se pudo pedir el timeline de {id_evento} ({ev.get('strEvent')}): {err}")
                continue  # no se marca como procesado: se reintenta mañana
            timeline = data.get("timeline") or []
            procesar_timeline(timeline, liga_clave, cache_liga)
            procesados.add(id_evento)
            peticiones_timeline += 1

        salida[liga_clave] = {
            "goleadores": top5(cache_liga, "goles"),
            "asistencias": top5(cache_liga, "asistencias"),
            "amarillas": top5(cache_liga, "amarillas"),
            "rojas": top5(cache_liga, "rojas"),
        }

    cache["procesados"] = sorted(procesados)
    guardar_cache_estadisticas(cache)

    with open(RUTA_SALIDA, "w", encoding="utf-8") as f:
        json.dump(salida, f, ensure_ascii=False, indent=2)

    print(f"\nListo. Peticiones a lookuptimeline.php: {peticiones_timeline}")
    print(f"Escrito: {RUTA_SALIDA}")


if __name__ == "__main__":
    main()
