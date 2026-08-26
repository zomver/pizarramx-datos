# -*- coding: utf-8 -*-
"""
Cron de América: Liga BBVA MX, Liga Profesional Argentina, Brasileirão
y Leagues Cup (Liga MX vs MLS). Corre cada 10 min, separado del de
Europa desde 2026-08-26 — con las 7 ligas juntas en un solo cron cada
corrida tardaba ~6 min y solo iba a crecer; separarlas por continente
deja a cada una con menos ligas que bajar, y una no bloquea a la otra
si alguna se atora pidiendo datos.

También es el único de los dos que baja resúmenes de YouTube y aplica
los overrides de detalles_manuales.json — esas dos cosas hoy en día son
todas de Liga MX/Leagues Cup, no tendría caso correrlas en el de Europa.

Uso:
    python generar_america.py
"""
from generar_datos import main

if __name__ == "__main__":
    main(
        claves_ligas=["bbva", "argentina", "brasil"],
        sufijo="_america",
        con_leagues_cup=True,
        con_extras=True,
    )
