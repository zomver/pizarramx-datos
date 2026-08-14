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

RUTA = os.path.join(os.path.dirname(__file__), "detalles_manuales.json")


def _cargar():
    if not os.path.exists(RUTA):
        return []
    with open(RUTA, encoding="utf-8") as f:
        return json.load(f)


def aplicar(partidos, detalles):
    """partidos: lista de dicts con homeAbbr/awayAbbr/fechaISO/id (los
    que arma construir_partidos en generar_datos.py). detalles: dict
    {match_id: {...}} que ya trae lo automático (p.ej. video de
    videos_youtube.py) — se le agrega/mezcla encima lo manual, sin pisar
    lo que ya hubiera para ese partido."""
    manuales = _cargar()
    if not manuales:
        return detalles

    # index rápido: (home, away, fecha) -> id real del partido en esta corrida
    por_equipos_fecha = {
        (p["homeAbbr"], p["awayAbbr"], p.get("fechaISO")): p["id"]
        for p in partidos
    }

    aplicadas = 0
    for entrada in manuales:
        clave = (entrada.get("home"), entrada.get("away"), entrada.get("date"))
        match_id = por_equipos_fecha.get(clave)
        if not match_id:
            # normal: el partido ya salió de la ventana de partidos.json
            # (unos días antes/después) o todavía no aparece — no es error
            continue
        extra = {k: v for k, v in entrada.items() if k not in ("home", "away", "date")}
        detalles[match_id] = {**detalles.get(match_id, {}), **extra}
        aplicadas += 1

    if aplicadas:
        print(f"\n[Detalles manuales] {aplicadas} entrada(s) de "
              f"detalles_manuales.json aplicadas a partidos de esta ventana.")

    return detalles
