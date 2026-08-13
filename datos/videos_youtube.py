# -*- coding: utf-8 -*-
"""
Busca en YouTube el video de resumen de cada partido ya finalizado y
arma detalles.json con {match_id: {"video": "ID_DEL_VIDEO"}}.

Canal usado: "MLS Español" (@mls-espanol), confirmado por API el
2026-08-14 — id de canal UCiI2VXTiJW0erXRuuuo2ahQ. OJO: existen otros
canales con nombre casi idéntico (p. ej. "MLS En Español",
UCPncnCPdLdbINGUfJxrKwdg) y TUDN USA (@tudn_usa) es quien en realidad
sube highlights de cada jornada de Liga MX — se usa MLS Español de
todos modos porque así se pidió explícitamente. Esto significa que
varios partidos de Liga MX normales pueden quedarse sin video (el canal
cubre sobre todo Leagues Cup/MLS) — es preferible eso a adivinar mal.

Solo se busca UNA VEZ por partido, con reintentos espaciados varias
horas (el pipeline completo corre cada 10 min vía GitHub Actions —
buscar en cada corrida agotaría la cuota gratuita de YouTube Data API
v3 en minutos: 10,000 unidades/día, 100 por búsqueda). El estado de
cada intento se guarda en salida/cache_videos.json, versionado en el
repo igual que cache_rondas.json, para que sobreviva entre corridas.

Requiere la variable de entorno YOUTUBE_API_KEY (secreto de GitHub
Actions). Si no está configurada, esta parte no hace nada — el resto
del pipeline sigue funcionando normal.
"""
import json
import os
import re
import time
import unicodedata
from datetime import datetime, timedelta

import requests

YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY", "")
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"

CANAL_ID = "UCiI2VXTiJW0erXRuuuo2ahQ"  # MLS Español (@mls-espanol)

CARPETA_SALIDA = os.path.join(os.path.dirname(__file__), "salida")
RUTA_CACHE_VIDEOS = os.path.join(CARPETA_SALIDA, "cache_videos.json")

# no reintentar antes de este tiempo tras un intento sin éxito — los
# resúmenes tardan en subirse; buscar cada 10 min sería tirar cuota
COOLDOWN_HORAS = 12
# tras este número de intentos sin encontrar nada, se deja de buscar ese
# partido para siempre (cubre ~3 días de reintentos, de sobra para que
# suba un resumen si es que lo van a subir)
MAX_INTENTOS = 6
# tope de búsquedas NUEVAS por corrida, para no gastar de golpe la cuota
# del día si hay muchos partidos recién terminados a la vez
TOPE_POR_CORRIDA = 15

_QUITAR = re.compile(r"\b(fc|cf|uanl|unam|de|del|la|los|club)\b", re.IGNORECASE)


def _normalizar(texto):
    sin_acentos = unicodedata.normalize("NFKD", texto or "")
    sin_acentos = "".join(c for c in sin_acentos if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9\s]", " ", sin_acentos.lower())


def _token_principal(nombre_display):
    """Primera palabra "fuerte" del nombre del equipo, para buscarla en
    el título del video — quita sufijos/prefijos genéricos que no
    ayudan a identificarlo (UANL, UNAM, FC, Club...)."""
    limpio = _QUITAR.sub(" ", nombre_display or "")
    palabras = _normalizar(limpio).split()
    if palabras:
        return palabras[0]
    palabras_originales = _normalizar(nombre_display).split()
    return palabras_originales[0] if palabras_originales else ""


def _titulo_coincide(titulo, home_display, away_display):
    t = _normalizar(titulo)
    home_tok = _token_principal(home_display)
    away_tok = _token_principal(away_display)
    if not home_tok or not away_tok:
        return False
    return bool(
        re.search(r"\b" + re.escape(home_tok) + r"\b", t)
        and re.search(r"\b" + re.escape(away_tok) + r"\b", t)
    )


def _buscar_video(home_display, away_display, fecha_iso):
    """Una sola llamada a la API (100 unidades de cuota). Devuelve el
    videoId si encuentra una coincidencia razonable, o None si no."""
    params = {
        "key": YOUTUBE_API_KEY,
        "part": "snippet",
        "channelId": CANAL_ID,
        "q": f"{home_display} {away_display}",
        "type": "video",
        "order": "date",
        "maxResults": 5,
    }
    if fecha_iso:
        params["publishedAfter"] = f"{fecha_iso}T00:00:00Z"

    try:
        r = requests.get(YOUTUBE_SEARCH_URL, params=params, timeout=15)
    except Exception as err:
        print(f"   ! error de red buscando '{home_display} vs {away_display}': {err}")
        return None

    if r.status_code != 200:
        print(f"   ! YouTube API respondió {r.status_code} buscando "
              f"'{home_display} vs {away_display}': {r.text[:200]}")
        return None

    items = (r.json() or {}).get("items") or []
    for item in items:
        titulo = (item.get("snippet") or {}).get("title", "")
        if _titulo_coincide(titulo, home_display, away_display):
            return item["id"]["videoId"]
    return None


def _cargar_cache():
    if os.path.exists(RUTA_CACHE_VIDEOS):
        with open(RUTA_CACHE_VIDEOS, encoding="utf-8") as f:
            return json.load(f)
    return {}


def _guardar_cache(cache):
    with open(RUTA_CACHE_VIDEOS, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def actualizar_videos(partidos):
    """partidos: lista plana de dicts ya armados por construir_partidos
    (con 'id', 'home', 'away', 'status', 'fechaISO') — es la ventana
    corta que vive en partidos.json (unos días), así que es de aquí de
    donde se sacan los datos para BUSCAR, pero NO es la base de lo que
    se devuelve: un partido sale de esa ventana a los pocos días y no
    por eso debe perder su video ya encontrado. Por eso el resultado se
    arma del caché completo (que sí es permanente), no solo de esta
    ventana. No truena si falta la API key: simplemente no busca nada
    nuevo, pero igual devuelve lo que ya hubiera en caché de antes."""
    cache = _cargar_cache()

    if not YOUTUBE_API_KEY:
        print("\n[YouTube] YOUTUBE_API_KEY no configurada, se omite la "
              "búsqueda de resúmenes.")
    else:
        ahora = datetime.utcnow()
        buscados_esta_corrida = 0

        print("\n[YouTube] buscando resúmenes en MLS Español...")
        for p in partidos:
            if p.get("status") != "ft":
                continue

            estado = cache.get(p["id"], {})
            if estado.get("video"):
                continue
            if estado.get("intentos", 0) >= MAX_INTENTOS:
                continue
            if estado.get("ultimo_intento"):
                ultimo = datetime.fromisoformat(estado["ultimo_intento"])
                if ahora - ultimo < timedelta(hours=COOLDOWN_HORAS):
                    continue
            if buscados_esta_corrida >= TOPE_POR_CORRIDA:
                break

            video_id = _buscar_video(p["home"], p["away"], p.get("fechaISO"))
            buscados_esta_corrida += 1
            cache[p["id"]] = {
                "intentos": estado.get("intentos", 0) + 1,
                "ultimo_intento": ahora.isoformat(),
                "video": video_id,
            }
            if video_id:
                print(f"   + {p['home']} vs {p['away']}: {video_id}")
            else:
                print(f"   - {p['home']} vs {p['away']}: sin coincidencia todavía "
                      f"(intento {cache[p['id']]['intentos']}/{MAX_INTENTOS})")
            time.sleep(0.3)

        _guardar_cache(cache)
        print(f"   búsquedas nuevas esta corrida: {buscados_esta_corrida}")

    detalles = {mid: {"video": v["video"]} for mid, v in cache.items() if v.get("video")}
    print(f"   videos disponibles en total (histórico): {len(detalles)}")
    return detalles
