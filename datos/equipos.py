# -*- coding: utf-8 -*-
"""
Mapeo de equipos para datos de TheSportsDB.

TheSportsDB no da un id de equipo estable y utilizable en el plan
gratuito (los endpoints de listado de equipos vienen truncados), así
que el cruce se hace por NOMBRE: cada partido trae strHomeTeam /
strAwayTeam y aquí lo traducimos a la abreviación y nombre bonito que
ya usan el resto del sitio (escudos, colores, etc. en pizarramx.js).

Cuando generar_datos.py encuentre un equipo que no está en NAME_MAP
avisará con un "! equipo sin mapear" — hay que agregarlo aquí a mano
(usa el nombre normalizado: minúsculas y sin acentos).
"""

# nombre normalizado (minúsculas, sin acentos) -> abreviación
NAME_MAP = {
    # --- Liga BBVA MX ---
    'america': 'AME',
    'atlante': 'ATE',
    'atlas': 'ATL',
    'atletico de san luis': 'SLP',
    'atletico san luis': 'SLP',
    'cd guadalajara': 'GDL',
    'guadalajara': 'GDL',
    'chivas': 'GDL',
    'cruz azul': 'CRZ',
    'juarez': 'JUA',
    'fc juarez': 'JUA',
    'leon': 'LEO',
    'monterrey': 'MTY',
    'necaxa': 'NEC',
    'pachuca': 'PAC',
    'puebla': 'PUE',
    'pumas unam': 'PUM',
    'pumas': 'PUM',
    'queretaro': 'QRO',
    'santos laguna': 'SAN',
    'santos': 'SAN',
    'tigres uanl': 'TIG',
    'tigres': 'TIG',
    'tijuana': 'TIJ',
    'toluca': 'TOL',

    # --- Liga de Expansión MX ---
    'alebrijes de oaxaca': 'ALE',
    'atletico la paz': 'ALP',
    'tampico madero': 'TAM',
    'jaiba brava': 'TAM',
    'cancun fc': 'CUN',
    'cancun': 'CUN',
    'celaya': 'CEL',
    'correcaminos uat': 'COR',
    'correcaminos': 'COR',
    'dorados de sinaloa': 'DOR',
    'dorados': 'DOR',
    'leones negros udeg': 'LEN',
    'leones negros udg': 'LEN',
    'leones negros': 'LEN',
    'mineros de zacatecas': 'MIN',
    'mineros': 'MIN',
    'atletico morelia': 'MOR',
    'monarcas morelia': 'MOR',
    'tapatio': 'TAP',
    'tepatitlan': 'TEP',
    'tlaxcala': 'TLA',
    'tlaxcala fc': 'TLA',
    'venados': 'VEN',
    'venados fc': 'VEN',
    'irapuato': 'IRA',
    # equipos nuevos en Expansión que todavía no tienen escudo propio
    # en /logos — se muestran con su abreviación como respaldo
    'alacranes de durango': 'DGO',
    'cruz azul hidalgo': 'CAH',
    'piratas': 'PIR',
    'piratas de campeche': 'PIR',
}

# nombres bonitos para mostrar (abreviación -> nombre).
# Si un equipo no está aquí, se usa el nombre tal cual lo manda la API.
DISPLAY_NAMES = {
    'AME': 'América', 'CRZ': 'Cruz Azul', 'TOL': 'Toluca', 'MTY': 'Monterrey',
    'TIG': 'Tigres UANL', 'PAC': 'Pachuca', 'LEO': 'León', 'GDL': 'Guadalajara',
    'PUM': 'Pumas UNAM', 'NEC': 'Necaxa', 'SAN': 'Santos Laguna', 'PUE': 'Puebla',
    'ATL': 'Atlas', 'QRO': 'Querétaro', 'JUA': 'FC Juárez', 'TIJ': 'Tijuana',
    'ATE': 'Atlante', 'SLP': 'Atlético San Luis',
    'ALE': 'Alebrijes de Oaxaca', 'ALP': 'Atlético La Paz', 'CUN': 'Cancún FC',
    'COR': 'Correcaminos UAT', 'DOR': 'Dorados de Sinaloa', 'LEN': 'Leones Negros',
    'MIN': 'Mineros de Zacatecas', 'TEP': 'Tepatitlán', 'VEN': 'Venados FC',
    'CEL': 'Celaya', 'TAM': 'Tampico Madero (Jaiba Brava)', 'MOR': 'Atlético Morelia',
    'TAP': 'Tapatío', 'TLA': 'Tlaxcala FC', 'IRA': 'Irapuato',
    'DGO': 'Alacranes de Durango', 'CAH': 'Cruz Azul Hidalgo', 'PIR': 'Piratas de Campeche',
}
