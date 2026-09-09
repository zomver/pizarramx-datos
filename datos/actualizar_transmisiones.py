# -*- coding: utf-8 -*-
"""
Aplica detalles_manuales.json y republica datos.js — separado de
generar_america.py/generar_europa.py/generar_champions.py para que una
transmisión cargada a mano se vea rápido (corre cada 5 min) sin esperar
al cron completo de ese continente (cada 10 min) y SIN gastar ninguna
llamada a la API de TheSportsDB — este script no le pide nada a
TheSportsDB, solo lee lo que los otros 3 crons ya dejaron.

posiciones_*.json/partidos_*.json/detalles.json no viven en el repo (los
sube cada cron por FTP nada más, ver sincronizar_otro_continente en
generar_datos.py) — así que este script los baja directo del sitio en
vivo, aplica detalles_manuales.json encima, y vuelve a armar datos.js con
escribir_datos_js() (que junta TODO lo que haya en salida/: standings,
partidos, medallero.json y estadisticas.json — estos dos últimos SÍ están
en el checkout porque se commitean al repo, ver sus propios workflows).

Uso:
    python actualizar_transmisiones.py
"""
import json
import os

import requests

import detalles_manuales
from escribir_datos_js import escribir_datos_js

SITIO_EN_VIVO = "https://pizarramx.com.mx/datos/salida/"
CARPETA_SALIDA = os.path.join(os.path.dirname(__file__), "salida")

# posiciones_*/partidos_* de los 3 continentes + el detalles.json actual
# (para no perder los videos/reddit que ya trae, solo agregarle encima lo
# manual) — todo bajado del sitio en vivo, nunca del checkout.
ARCHIVOS_A_BAJAR = [
    "posiciones_america.json", "posiciones_europa.json", "posiciones_champions.json",
    "partidos_america.json", "partidos_europa.json", "partidos_champions.json",
    "detalles.json",
]


def bajar_json(nombre_archivo, respaldo):
    try:
        r = requests.get(f"{SITIO_EN_VIVO}{nombre_archivo}", timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as err:
        print(f"   ! no se pudo traer {nombre_archivo} del sitio en vivo: {err}")
        return respaldo


def main():
    os.makedirs(CARPETA_SALIDA, exist_ok=True)

    for nombre in ARCHIVOS_A_BAJAR:
        datos = bajar_json(nombre, None)
        if datos is None:
            continue
        with open(os.path.join(CARPETA_SALIDA, nombre), "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)

    todos_los_partidos = []
    for nombre in ("partidos_america.json", "partidos_europa.json", "partidos_champions.json"):
        ruta = os.path.join(CARPETA_SALIDA, nombre)
        if os.path.exists(ruta):
            with open(ruta, encoding="utf-8") as f:
                partidos = json.load(f)
            print(f"   {nombre}: {len(partidos)} partido(s)")
            todos_los_partidos += partidos

    ruta_detalles = os.path.join(CARPETA_SALIDA, "detalles.json")
    detalles = {}
    if os.path.exists(ruta_detalles):
        with open(ruta_detalles, encoding="utf-8") as f:
            detalles = json.load(f)

    detalles = detalles_manuales.aplicar(todos_los_partidos, detalles)

    with open(ruta_detalles, "w", encoding="utf-8") as f:
        json.dump(detalles, f, ensure_ascii=False, indent=2)

    ruta_datos_js, datos_finales = escribir_datos_js()
    print(f"\n[actualizar_transmisiones] {ruta_datos_js} regenerado "
          f"({len(detalles)} partido(s) con detalles, "
          f"{len(datos_finales.get('partidos', []))} partido(s) en total).")


if __name__ == "__main__":
    main()
