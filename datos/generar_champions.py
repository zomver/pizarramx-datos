# -*- coding: utf-8 -*-
"""
Cron de Champions League. A diferencia de América y Europa, este NO
corre solo cada 10 min — su workflow (partidos_champions.yml) solo
tiene "workflow_dispatch", sin "schedule", así que hace falta correrlo
a mano desde GitHub Actions cada vez que se quiera actualizar.

Sin Leagues Cup (es Liga MX vs MLS, no aplica aquí) y sin
videos/detalles_manuales (esas dos cosas hoy en día son todas de Liga
MX, ver generar_america.py).

Uso:
    python generar_champions.py
"""
from generar_datos import main

if __name__ == "__main__":
    main(
        claves_ligas=["champions"],
        sufijo="_champions",
        con_leagues_cup=False,
        con_extras=False,
    )
