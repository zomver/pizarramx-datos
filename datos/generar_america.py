# -*- coding: utf-8 -*-
"""
Cron de América: Liga BBVA MX, Liga Profesional Argentina y Brasileirão.
Corre cada 10 min, separado del de Europa desde 2026-08-26 — con las 7
ligas juntas en un solo cron cada corrida tardaba ~6 min y solo iba a
crecer; separarlas por continente deja a cada una con menos ligas que
bajar, y una no bloquea a la otra si alguna se atora pidiendo datos.

También es el único de los dos que baja resúmenes de YouTube y aplica
los overrides de detalles_manuales.json — esas dos cosas hoy en día son
todas de Liga MX, no tendría caso correrlas en el de Europa.

Leagues Cup: el torneo 2026 terminó (6 sep) — con_leagues_cup=False desde
entonces para no seguir gastando llamadas de la API en un torneo que ya
no tiene partidos. El código de descargar_leagues_cup()/
calcular_standings_leagues_cup() se queda en generar_datos.py por si el
torneo 2027 lo vuelve a necesitar.

Uso:
    python generar_america.py
"""
from generar_datos import main

if __name__ == "__main__":
    main(
        claves_ligas=["bbva", "argentina", "brasil"],
        sufijo="_america",
        con_leagues_cup=False,
        con_extras=True,
    )
