# -*- coding: utf-8 -*-
"""
Cron de Europa: Premier League, LaLiga, Serie A y Bundesliga. Corre
cada 10 min, separado del de América desde 2026-08-26 (ver
generar_america.py para el motivo completo).

Sin Leagues Cup (es Liga MX vs MLS, no aplica aquí) y sin
videos/detalles_manuales (esas dos cosas hoy en día son todas de Liga
MX, ver generar_america.py).

Uso:
    python generar_europa.py
"""
from generar_datos import main

if __name__ == "__main__":
    main(
        claves_ligas=["premier", "laliga", "seriea", "bundesliga"],
        sufijo="_europa",
        con_leagues_cup=False,
        con_extras=False,
    )
