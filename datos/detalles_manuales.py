# -*- coding: utf-8 -*-
"""
Overrides manuales de "detalles" por partido — el complemento de
videos_youtube.py para datos que no se pueden buscar automático. Hoy en
día es solo hilos de Reddit: Reddit cerró el registro de apps nuevas
desde noviembre de 2025 (Responsible Builder Policy) y hasta los
endpoints .json públicos dejaron de funcionar el 30 de mayo de 2026, así
que no hay forma gratuita de automatizar esa búsqueda por ahora. Si algún
día Reddit reabre el acceso, esto se puede reemplazar por un módulo
automático igual que videos_youtube.py.

Edita datos/detalles_manuales.json a mano para agregar/quitar entradas.

Cada entrada se identifica por equipo local + visitante (abreviaciones
de equipos.py) + fecha (YYYY-MM-DD) — NO por el id del partido, porque
ese id depende de un idEvent de TheSportsDB que nadie tiene a mano de
antemano al escribir la entrada. Cualquier campo aparte de
home/away/date se mezcla tal cual sobre el "detalle" de ese partido
(mismo formato que ya usa videos_youtube.py, p.ej. "reddit": {...}).
"""
import json
import os
from datetime import date as _date

RUTA = os.path.join(os.path.dirname(__file__), "detalles_manuales.json")

# tolerancia al comparar la fecha que se escribió a mano contra la que
# guarda TheSportsDB (fechaISO). Un partido nocturno en México (ej. 21:00h
# CDMX = UTC-6) cae DESPUÉS de medianoche en UTC, así que TheSportsDB lo
# registra como si fuera el día siguiente — comprobado en vivo el 2026-08-16
# con Atlas-Tigres y Monterrey-Juárez, ambos escritos como "hoy sábado" en
# hora de México pero guardados un día después. Con ±1 día de tolerancia,
# quien escriba la fecha "como la vive" (hora de México) no tiene que
# convertir nada a mano.
TOLERANCIA_DIAS = 1


def _cargar():
    if not os.path.exists(RUTA):
        return []
    with open(RUTA, encoding="utf-8") as f:
        return json.load(f)


def _distancia_dias(fecha_iso_a, fecha_iso_b):
    """Diferencia en días entre dos fechas YYYY-MM-DD, o None si alguna
    falta o viene mal formada (así nunca truena por un dato manual sucio)."""
    try:
        return abs((_date.fromisoformat(fecha_iso_a) - _date.fromisoformat(fecha_iso_b)).days)
    except (TypeError, ValueError):
        return None


def aplicar(partidos, detalles):
    """partidos: lista de dicts con homeAbbr/awayAbbr/fechaISO/id (los
    que arma construir_partidos en generar_datos.py). detalles: dict
    {match_id: {...}} que ya trae lo automático (p.ej. video de
    videos_youtube.py) — se le agrega/mezcla encima lo manual, sin pisar
    lo que ya hubiera para ese partido."""
    manuales = _cargar()
    if not manuales:
        return detalles

    # candidatos por (home, away) — casi siempre hay solo uno en la
    # ventana de ~11 días de partidos.json, pero se agrupan por si acaso
    # (torneos con partidos dobles, etc.)
    por_equipos = {}
    for p in partidos:
        por_equipos.setdefault((p["homeAbbr"], p["awayAbbr"]), []).append(p)

    aplicadas = 0
    for entrada in manuales:
        candidatos = por_equipos.get((entrada.get("home"), entrada.get("away"))) or []
        fecha_dada = entrada.get("date")

        # de los candidatos, el más cercano en fecha — y solo si cae
        # dentro de la tolerancia (si no, mejor no aplicar que aplicar
        # sobre el partido equivocado)
        mejor, mejor_dist = None, None
        for p in candidatos:
            d = _distancia_dias(p.get("fechaISO"), fecha_dada)
            if d is not None and (mejor_dist is None or d < mejor_dist):
                mejor, mejor_dist = p, d

        if mejor is None or mejor_dist > TOLERANCIA_DIAS:
            # normal: el partido ya salió de la ventana de partidos.json,
            # todavía no aparece, o la fecha está demasiado lejos como
            # para ser el mismo partido — no es error
            continue

        extra = {k: v for k, v in entrada.items() if k not in ("home", "away", "date")}
        detalles[mejor["id"]] = {**detalles.get(mejor["id"], {}), **extra}
        aplicadas += 1

    if aplicadas:
        print(f"\n[Detalles manuales] {aplicadas} entrada(s) de "
              f"detalles_manuales.json aplicadas a partidos de esta ventana.")

    return detalles
