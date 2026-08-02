# -*- coding: utf-8 -*-
"""
Actualiza el medallero de los Juegos Centroamericanos y del Caribe
Santo Domingo 2026 leyéndolo de Wikipedia, que mantiene la tabla al día.

Correr una vez al día durante los juegos:
    python actualizar_medallero.py

Después hay que subir datos/salida/medallero.json y datos/salida/datos.js
al hosting para que el cambio se vea en el sitio.
"""
import json
import os
import re
import time
import unicodedata
from datetime import date

import requests
from bs4 import BeautifulSoup

from escribir_datos_js import escribir_datos_js

PAGINA = "XXV Juegos Centroamericanos y del Caribe"
API = "https://es.wikipedia.org/w/api.php"

CARPETA_SALIDA = os.path.join(os.path.dirname(__file__), "salida")
RUTA_JSON = os.path.join(CARPETA_SALIDA, "medallero.json")

# Las banderas se guardan en el propio sitio en vez de enlazarlas desde
# Wikimedia: enlazar imágenes de sus servidores (hotlinking) está
# desaconsejado, es más lento y se rompería si algún día lo bloquean.
CARPETA_BANDERAS = os.path.join(os.path.dirname(__file__), "..", "logos", "banderas")
# Wikimedia solo genera miniaturas en ciertos anchos; pedir uno fuera de
# esa lista devuelve error 400. Se prueban de mayor a menor hasta que una
# funcione (las banderas se ven a ~26px, así que 120 sobra para retina).
ANCHOS_BANDERA = [120, 60, 40, 20]

# Wikipedia escribe los nombres de país en español; aquí los pasamos al
# código de 3 letras que usa el sitio. Si aparece un país nuevo el script
# avisa y usa las 3 primeras letras como respaldo.
CODIGOS = {
    "mexico": "MEX", "colombia": "COL", "cuba": "CUB",
    "republica dominicana": "DOM", "venezuela": "VEN", "guatemala": "GUA",
    "puerto rico": "PUR", "costa rica": "CRC", "el salvador": "ESA",
    "panama": "PAN", "haiti": "HAI", "honduras": "HON",
    "trinidad y tobago": "TTO", "jamaica": "JAM", "guadalupe": "GLP",
    "guyana": "GUY", "nicaragua": "NCA", "barbados": "BAR",
    "bahamas": "BAH", "aruba": "ARU", "curazao": "CUW", "islas caiman": "CAY",
    "bermudas": "BER", "belice": "BIZ", "granada": "GRN", "surinam": "SUR",
    "santa lucia": "LCA", "islas virgenes": "ISV", "martinica": "MTQ",
    "antigua y barbuda": "ANT", "dominica": "DMA", "san vicente y las granadinas": "VIN",
    "san cristobal y nieves": "SKN", "islas virgenes britanicas": "IVB",
}


def normalizar(texto):
    sin_acentos = unicodedata.normalize("NFKD", texto or "")
    sin_acentos = "".join(c for c in sin_acentos if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", sin_acentos).strip().lower()


def bajar_html():
    r = requests.get(API, params={
        "action": "parse", "page": PAGINA, "prop": "text",
        "format": "json", "formatversion": "2",
    }, headers={"User-Agent": "PizarraMX/1.0 (actualizacion de medallero)"}, timeout=30)
    r.raise_for_status()
    return r.json()["parse"]["text"]


def es_tabla_medallero(tabla):
    """
    La tabla del medallero se reconoce por sus encabezados de Oro, Plata y
    Bronce. Ojo: Wikipedia los pone como IMÁGENES de medalla, no como texto,
    así que hay que mirar también el alt de las imágenes y el title de los
    enlaces, no solo el texto visible.
    """
    piezas = []
    for th in tabla.find_all("th"):
        piezas.append(th.get_text(" "))
        piezas += [img.get("alt", "") for img in th.find_all("img")]
        piezas += [a.get("title", "") for a in th.find_all("a")]

    encabezados = normalizar(" ".join(piezas))
    return all(p in encabezados for p in ("oro", "plata", "bronce"))


def numero(celda):
    txt = re.sub(r"[^\d]", "", celda.get_text(" ").strip())
    return int(txt) if txt else 0


# una celda de posición puede venir como "1", "15" o "=15" cuando hay empate
ES_POSICION = re.compile(r"^=?\d+\.?$")


def extraer_paises(tabla):
    paises = []
    for fila in tabla.find_all("tr"):
        celdas = fila.find_all(["td", "th"])
        if len(celdas) < 4:
            continue

        # la fila de encabezados es puro <th>: se salta
        if all(c.name == "th" for c in celdas):
            continue

        # el nombre del país es la primera celda que no es una posición
        # ni un número suelto (así no se cuela "Núm." ni el "=15" de los empates)
        nombre = None
        idx_nombre = None
        for i, c in enumerate(celdas):
            txt = c.get_text(" ").strip()
            if not txt or ES_POSICION.match(txt):
                continue
            nombre = re.sub(r"\s*\(\w+\)\s*$", "", txt).strip()
            idx_nombre = i
            break

        if not nombre or normalizar(nombre) in ("total", "totales", "pais", "num."):
            continue

        # las tres cifras que siguen al nombre son oro, plata y bronce
        cifras = celdas[idx_nombre + 1: idx_nombre + 4]
        if len(cifras) < 3:
            continue

        clave = normalizar(nombre)
        code = CODIGOS.get(clave)
        if not code:
            print(f"   ! país sin código: '{nombre}' — agrégalo a CODIGOS en este script")
            code = clave[:3].upper()

        # la bandera viene como <img> dentro de la celda del país
        img = celdas[idx_nombre].find("img")
        bandera = img.get("src") if img else None

        paises.append({
            "code": code,
            "name": nombre,
            "oro": numero(cifras[0]),
            "plata": numero(cifras[1]),
            "bronce": numero(cifras[2]),
            "_bandera": bandera,
        })
    return paises


def descargar_banderas(paises):
    """
    Guarda la bandera de cada país en /logos/banderas/CODIGO.png.
    Las URLs de Wikimedia traen el ancho dentro de la ruta ("20px-..."),
    así que se cambia por uno mayor para que no se vean pixeladas.
    Solo descarga las que falten.
    """
    os.makedirs(CARPETA_BANDERAS, exist_ok=True)
    nuevas = 0

    for p in paises:
        url = p.get("_bandera")
        destino = os.path.join(CARPETA_BANDERAS, f"{p['code']}.png")
        if os.path.exists(destino):
            continue
        if not url:
            print(f"   ! sin bandera para {p['name']} ({p['code']})")
            continue

        if url.startswith("//"):
            url = "https:" + url

        cabeceras = {"User-Agent": "PizarraMX/1.0 (banderas del medallero)"}
        guardada = False
        ultimo_error = None

        for ancho in ANCHOS_BANDERA:
            # .../20px-Flag_of_Mexico.svg.png -> .../120px-Flag_of_Mexico.svg.png
            intento = re.sub(r"/\d+px-", f"/{ancho}px-", url)

            # se reintenta el MISMO tamaño ante fallos pasajeros (Wikimedia
            # limita peticiones seguidas). Solo un 400 significa de verdad
            # "ese ancho no existe", y ahí sí se baja al siguiente tamaño.
            for intento_num in range(3):
                try:
                    r = requests.get(intento, headers=cabeceras, timeout=30)
                    if r.status_code == 400:
                        ultimo_error = None
                        break
                    r.raise_for_status()
                    with open(destino, "wb") as f:
                        f.write(r.content)
                    guardada = True
                    break
                except Exception as e:
                    ultimo_error = e
                    time.sleep(1.5 * (intento_num + 1))

            if guardada:
                nuevas += 1
                break

        if not guardada:
            print(f"   ! no pude bajar la bandera de {p['name']}: {ultimo_error or 'ningún tamaño disponible'}")

        time.sleep(0.4)  # pausa cortés entre descargas

    if nuevas:
        print(f"   {nuevas} banderas nuevas guardadas en logos/banderas/")
    return nuevas


def main():
    print(f"Bajando el medallero de Wikipedia ({PAGINA})...")
    sopa = BeautifulSoup(bajar_html(), "html.parser")

    tabla = next((t for t in sopa.find_all("table") if es_tabla_medallero(t)), None)
    if tabla is None:
        raise SystemExit(
            "No encontré la tabla del medallero en la página.\n"
            "Puede que Wikipedia haya cambiado el formato: revisa la página a mano."
        )

    paises = extraer_paises(tabla)
    if not paises:
        raise SystemExit("Encontré la tabla pero salió vacía. Revisa el formato de Wikipedia.")

    descargar_banderas(paises)

    # el campo con la URL solo servía para descargar; no va al JSON final
    for p in paises:
        p.pop("_bandera", None)

    # orden olímpico estándar: primero por oro, luego plata, luego bronce
    paises.sort(key=lambda p: (-p["oro"], -p["plata"], -p["bronce"], p["name"]))

    datos = {
        "evento": "Juegos Centroamericanos y del Caribe",
        "edicion": "Santo Domingo 2026",
        "inicio": "2026-07-24",
        "fin": "2026-08-08",
        "actualizado": date.today().isoformat(),
        "fuente": f"Wikipedia — {PAGINA}",
        "paises": paises,
    }

    os.makedirs(CARPETA_SALIDA, exist_ok=True)
    with open(RUTA_JSON, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)

    print(f"\n{len(paises)} países. Top 5:")
    for i, p in enumerate(paises[:5], 1):
        print(f"   {i}. {p['name']:24} {p['oro']:>3} oro  {p['plata']:>3} plata  {p['bronce']:>3} bronce")
    # regenera datos.js juntando el medallero con lo que ya haya de fútbol
    ruta_js, _ = escribir_datos_js()

    print(f"\nEscrito: {RUTA_JSON}")
    print(f"Escrito: {ruta_js}")
    print("\nSube esos dos archivos a datos/salida/ en Hostinger para verlo en línea.")


if __name__ == "__main__":
    main()
