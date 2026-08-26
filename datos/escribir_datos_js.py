# -*- coding: utf-8 -*-
"""
Arma datos/salida/datos.js juntando los .json que haya en salida/.

Vive aparte porque lo usan dos scripts: generar_datos.py (fútbol) y
actualizar_medallero.py (medallero). Así se puede correr cualquiera de
los dos por separado sin que el otro borre sus datos.
"""
import json
import os

CARPETA_SALIDA = os.path.join(os.path.dirname(__file__), "salida")


def _leer(nombre):
    ruta = os.path.join(CARPETA_SALIDA, nombre)
    if not os.path.exists(ruta):
        return None
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def _combinar_standings():
    """posiciones_america.json + posiciones_europa.json (cron por
    continente, ver generar_america.py/generar_europa.py) si existen;
    si no, cae a posiciones.json de siempre (corrida manual de
    generar_datos.py sin split, como se usó antes del 2026-08-26)."""
    america = _leer("posiciones_america.json")
    europa = _leer("posiciones_europa.json")
    if america is None and europa is None:
        return _leer("posiciones.json")
    combinado = {}
    combinado.update(america or {})
    combinado.update(europa or {})
    return combinado


def _combinar_partidos():
    """Mismo criterio que _combinar_standings pero concatenando las dos
    listas (y reordenando por fecha, ya que vienen de dos corridas
    independientes que no se vieron entre sí)."""
    america = _leer("partidos_america.json")
    europa = _leer("partidos_europa.json")
    if america is None and europa is None:
        return _leer("partidos.json")
    combinados = (america or []) + (europa or [])
    combinados.sort(key=lambda p: p.get("fechaISO") or "")
    return combinados


def escribir_datos_js():
    """
    Genera datos.js con todo lo que exista. Se usa <script src> en vez de
    fetch() porque los navegadores bloquean fetch() a archivos locales
    cuando la página se abre con doble clic (file://).
    """
    datos = {}

    standings = _combinar_standings()
    if standings is not None:
        datos["standings"] = standings

    partidos = _combinar_partidos()
    if partidos is not None:
        datos["partidos"] = partidos

    medallero = _leer("medallero.json")
    if medallero is not None:
        datos["medallero"] = medallero

    # {match_id: {"video": "ID_DE_YOUTUBE"}} — lo arma videos_youtube.py.
    # El front-end (pizarramx.js) lo mezcla sobre MATCH_DETAILS.
    detalles = _leer("detalles.json")
    if detalles is not None:
        datos["detalles"] = detalles

    # goleadores/asistencias/tarjetas por liga — lo arma estadisticas_liga.py
    # (corre una vez al día, workflow aparte). A diferencia de
    # posiciones.json/partidos.json, este SÍ se commitea al repo (ver
    # estadisticas.yml), así que sobrevive al checkout limpio de cada
    # corrida de generar_datos.py y se sigue mezclando aquí aunque
    # generar_datos.py corra 10 minutos después sin que estadisticas.yml
    # haya vuelto a correr.
    estadisticas = _leer("estadisticas.json")
    if estadisticas is not None:
        datos["estadisticas"] = estadisticas

    ruta = os.path.join(CARPETA_SALIDA, "datos.js")
    with open(ruta, "w", encoding="utf-8") as f:
        f.write("// generado por los scripts de /datos — no editar a mano\n")
        f.write("window.DATOS_REALES = ")
        json.dump(datos, f, ensure_ascii=False, indent=2)
        f.write(";\n")

    return ruta, datos
