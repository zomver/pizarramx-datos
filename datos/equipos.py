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

    # --- Leagues Cup 2026 (equipos de MLS; los de Liga MX ya están
    # mapeados arriba) ---
    'austin fc': 'AUS', 'austin': 'AUS',
    'charlotte fc': 'CLT', 'charlotte': 'CLT',
    'chicago fire': 'CHI', 'chicago fire fc': 'CHI',
    'columbus crew': 'CLB',
    'fc cincinnati': 'CIN', 'cincinnati': 'CIN',
    'fc dallas': 'DAL', 'dallas': 'DAL',
    'inter miami': 'MIA', 'inter miami cf': 'MIA',
    'los angeles fc': 'LAF', 'lafc': 'LAF',
    'minnesota united': 'MNU', 'minnesota united fc': 'MNU',
    'nashville sc': 'NSH', 'nashville': 'NSH',
    'new york city fc': 'NYC', 'nycfc': 'NYC',
    'orlando city': 'ORL', 'orlando city sc': 'ORL',
    'philadelphia union': 'PHI',
    'portland timbers': 'POR',
    'real salt lake': 'RSL',
    'san diego fc': 'SDG', 'san diego': 'SDG',
    'seattle sounders': 'SEA', 'seattle sounders fc': 'SEA',
    'vancouver whitecaps': 'VAN', 'vancouver whitecaps fc': 'VAN',

    # --- Liga Profesional Argentina (2026) ---
    'aldosivi': 'ALD',
    'defensa y justicia': 'DEJ',
    'banfield': 'BAN',
    'huracan': 'HUR',
    'union': 'UNI',
    'platense': 'PLA',
    'central cordoba de santiago del estero': 'CCO', 'central cordoba': 'CCO',
    'gimnasia y esgrima de mendoza': 'GEM',
    'independiente': 'IND',
    'estudiantes de la plata': 'ELP',
    'instituto': 'INS',
    'velez sarsfield': 'VEL', 'velez': 'VEL',
    'san lorenzo': 'SLO',
    'lanus': 'LAN',
    'barracas central': 'BAR',
    'river plate': 'RIV',
    'gimnasia y esgrima de la plata': 'GLP',
    'racing club': 'RAC',
    'independiente rivadavia': 'IRV',
    'atletico tucuman': 'ATU',
    'talleres de cordoba': 'TAL', 'talleres': 'TAL',
    "newell's old boys": 'NOB', 'newells old boys': 'NOB',
    'boca juniors': 'BOC',
    'deportivo riestra': 'RIE',
    'rosario central': 'ROS',
    'belgrano': 'BEL',
    'argentinos juniors': 'ARG',
    'sarmiento': 'SAR',
    'tigre': 'TIA',
    'estudiantes de rio cuarto': 'ERC',

    # --- Brasileirão Série A (2026) ---
    # "Santos" es ambiguo (existe Santos Laguna en Liga BBVA MX): se
    # resuelve en NAME_MAP_POR_LIGA, no aquí, para no pisar el 'santos'
    # de arriba.
    'santos fc': 'STS',
    'athletico paranaense': 'ATP',
    'atletico mineiro': 'CAM',
    'bahia': 'BAH',
    'botafogo': 'BOT',
    'bragantino': 'BRA', 'red bull bragantino': 'BRA',
    'chapecoense': 'CHA',
    'corinthians': 'CRI',
    'coritiba': 'COT',
    'cruzeiro': 'CRU',
    'flamengo': 'FLA',
    'fluminense': 'FLU',
    'gremio': 'GRE',
    'internacional': 'INT',
    'mirassol': 'MIR',
    'palmeiras': 'PAL',
    'remo': 'REM',
    'sao paulo': 'SAO',
    'vasco da gama': 'VAS', 'vasco': 'VAS',
    'vitoria': 'VIT',

    # --- Premier League (2026-27) ---
    'arsenal': 'ARS',
    'aston villa': 'AVL',
    'bournemouth': 'BOU',
    'brentford': 'BRE',
    'brighton and hove albion': 'BHA', 'brighton & hove albion': 'BHA', 'brighton': 'BHA',
    'chelsea': 'CHE',
    'coventry city': 'COV', 'coventry': 'COV',
    'crystal palace': 'CRY',
    'everton': 'EVE',
    'fulham': 'FUL',
    'hull city': 'HUL', 'hull': 'HUL',
    'ipswich town': 'IPS', 'ipswich': 'IPS',
    'leeds united': 'LEE', 'leeds': 'LEE',
    'liverpool': 'LIV',
    'manchester city': 'MCI',
    'manchester united': 'MUN',
    'newcastle united': 'NEW', 'newcastle': 'NEW',
    'nottingham forest': 'NFO',
    'sunderland': 'SUN',
    'tottenham hotspur': 'TOT', 'tottenham': 'TOT',

    # --- LaLiga (2026-27) ---
    # nombres normalizados: TheSportsDB manda el nombre "pelón" (sin
    # "FC"/"CF"/"CD" ni acentos una vez pasado por normalizar()), pero se
    # dejan alias con el nombre comercial completo por si algún día lo
    # cambian.
    'athletic bilbao': 'ATH', 'athletic club': 'ATH',
    'atletico madrid': 'ATM', 'atletico de madrid': 'ATM',
    'barcelona': 'BCN', 'fc barcelona': 'BCN',
    'celta vigo': 'CEL', 'celta de vigo': 'CEL',
    'deportivo alaves': 'ALA',
    'deportivo de a coruna': 'DEP', 'deportivo la coruna': 'DEP',
    'elche': 'ELC',
    'espanyol': 'ESP', 'rcd espanyol': 'ESP',
    'getafe': 'GET',
    'levante': 'LEV',
    'malaga': 'MAL',
    'osasuna': 'OSA',
    'racing de santander': 'RSA', 'racing santander': 'RSA',
    'rayo vallecano': 'RAY',
    'real betis': 'BET',
    'real madrid': 'RMA',
    'real sociedad': 'RSO',
    'sevilla': 'SEV',
    'valencia': 'VAL',
    'villarreal': 'VIL',

    # --- Serie A (Italia, 2026-27) ---
    # nombres tal como los manda la API (probados a mano contra
    # eventsround.php el 2026-08-26) + algunos alias por si acaso.
    'ac milan': 'MIL', 'milan': 'MIL',
    'roma': 'ROM', 'as roma': 'ROM',
    'atalanta': 'ATA',
    'bologna': 'BOL',
    'cagliari': 'CAG',
    'como': 'COM', 'como 1907': 'COM',
    'fiorentina': 'FIO',
    'frosinone': 'FRO', 'frosinone calcio': 'FRO',
    'genoa': 'GEN',
    'inter milan': 'INM', 'inter': 'INM', 'internazionale': 'INM',
    'juventus': 'JUV',
    'lazio': 'LAZ',
    'lecce': 'LEC',
    'napoli': 'NAP',
    'parma': 'PAR',
    'sassuolo': 'SAS',
    'torino': 'TOR',
    'udinese': 'UDI',
    'venezia': 'VNZ', 'venezia fc': 'VNZ',
    'monza': 'MON', 'ac monza': 'MON',

    # --- Bundesliga (Alemania, 2026-27) ---
    # ojo: la API manda los nombres CORTOS (probado a mano el 2026-08-26:
    # "Koln", "Hamburg", "Mainz", no "1. FC Köln"/"Hamburger SV"/"Mainz
    # 05") — normalizar() no quita puntos, así que si algún día la API
    # cambia a mandar el nombre largo con punto ("1. FC Köln"), hay que
    # agregar esa variante aparte, "1 fc koln" (sin punto) NO le pega.
    'koln': 'KOL', 'fc koln': 'KOL', 'cologne': 'KOL',
    'bayer leverkusen': 'B04', 'leverkusen': 'B04',
    'bayern munich': 'FCB', 'bayern munchen': 'FCB', 'bayern': 'FCB',
    'borussia dortmund': 'BVB', 'dortmund': 'BVB',
    'borussia monchengladbach': 'BMG', 'monchengladbach': 'BMG', 'mgladbach': 'BMG',
    'eintracht frankfurt': 'SGE', 'frankfurt': 'SGE',
    'augsburg': 'AUG', 'fc augsburg': 'AUG',
    'hamburg': 'HSV', 'hamburger sv': 'HSV', 'hamburger': 'HSV',
    'mainz': 'MAI', 'mainz 05': 'MAI',
    'rb leipzig': 'RBL', 'leipzig': 'RBL',
    'freiburg': 'FRI', 'sc freiburg': 'FRI',
    'paderborn': 'PAD', 'sc paderborn 07': 'PAD',
    'schalke 04': 'SCH', 'schalke': 'SCH',
    'elversberg': 'ELV', 'sv elversberg': 'ELV',
    'hoffenheim': 'TSG', 'tsg hoffenheim': 'TSG',
    'union berlin': 'UNB',
    'stuttgart': 'VFB', 'vfb stuttgart': 'VFB',
    'werder bremen': 'WER', 'bremen': 'WER',

    # --- Champions League (equipos que no están en ninguna de las ligas
    # de arriba — los que sí, como Real Madrid o Bayern Múnich, ya
    # funcionan con sus abreviaciones normales) ---
    'aek athens': 'AEK',
    # normalizar() NO convierte "ø" a "o" (no es un acento combinable,
    # normalize() con NFKD no lo descompone) — hay que dejar el string
    # exacto tal como lo manda la API, comprobado a mano el 2026-09-01
    'bodø/glimt': 'BOD', 'bodoglimt': 'BOD', 'bodo glimt': 'BOD', 'bodo/glimt': 'BOD',
    'club brugge': 'BRU', 'brugge': 'BRU',
    'fenerbahce': 'FEN', 'fenerbahce sk': 'FEN',
    'feyenoord': 'FEY',
    'galatasaray': 'GAL',
    'lask': 'LAS', 'lask linz': 'LAS',
    'lens': 'LNS', 'rc lens': 'LNS',
    'lille': 'LIL', 'losc lille': 'LIL',
    'psv eindhoven': 'PSV', 'psv': 'PSV',
    'paris saint-germain': 'PSG', 'paris saint germain': 'PSG', 'psg': 'PSG',
    'porto': 'FCP', 'fc porto': 'FCP',
    'sabah baku': 'SAB',
    'shakhtar donetsk': 'SHK', 'shakhtar': 'SHK',
    'slavia prague': 'SLA', 'slavia praha': 'SLA',
    'slovan bratislava': 'SLB',
    'sporting cp': 'SCP', 'sporting lisbon': 'SCP', 'sporting lisboa': 'SCP',
    'viking': 'VIK', 'viking fk': 'VIK',
}

# "Santos" solo (sin "FC" ni "Laguna") es ambiguo entre Santos Laguna
# (Liga BBVA MX) y Santos FC (Brasileirão) — la API a veces manda el
# nombre corto para ambos. Esto se revisa ANTES que NAME_MAP en
# mapear_equipo(), usando la clave de la liga que se está procesando
# (ver generar_datos.py), así que solo hace falta la excepción del lado
# de Brasil: del lado de "bbva" ya funciona bien con el 'santos': 'SAN'
# normal de arriba.
NAME_MAP_POR_LIGA = {
    'brasil': {'santos': 'STS'},
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
    'AUS': 'Austin FC', 'CLT': 'Charlotte FC', 'CHI': 'Chicago Fire', 'CLB': 'Columbus Crew',
    'CIN': 'FC Cincinnati', 'DAL': 'FC Dallas', 'MIA': 'Inter Miami', 'LAF': 'LAFC',
    'MNU': 'Minnesota United', 'NSH': 'Nashville SC', 'NYC': 'New York City FC',
    'ORL': 'Orlando City', 'PHI': 'Philadelphia Union', 'POR': 'Portland Timbers',
    'RSL': 'Real Salt Lake', 'SDG': 'San Diego FC', 'SEA': 'Seattle Sounders',
    'VAN': 'Vancouver Whitecaps',

    # --- Liga Profesional Argentina ---
    'ALD': 'Aldosivi', 'DEJ': 'Defensa y Justicia', 'BAN': 'Banfield',
    'HUR': 'Huracán', 'UNI': 'Unión', 'PLA': 'Platense',
    'CCO': 'Central Córdoba (SdE)', 'GEM': 'Gimnasia y Esgrima (Mendoza)',
    'IND': 'Independiente', 'ELP': 'Estudiantes de La Plata', 'INS': 'Instituto',
    'VEL': 'Vélez Sarsfield', 'SLO': 'San Lorenzo', 'LAN': 'Lanús',
    'BAR': 'Barracas Central', 'RIV': 'River Plate',
    'GLP': 'Gimnasia y Esgrima (La Plata)', 'RAC': 'Racing Club',
    'IRV': 'Independiente Rivadavia', 'ATU': 'Atlético Tucumán',
    'TAL': 'Talleres de Córdoba', 'NOB': "Newell's Old Boys", 'BOC': 'Boca Juniors',
    'RIE': 'Deportivo Riestra', 'ROS': 'Rosario Central', 'BEL': 'Belgrano',
    'ARG': 'Argentinos Juniors', 'SAR': 'Sarmiento', 'TIA': 'Tigre',
    'ERC': 'Estudiantes de Río Cuarto',

    # --- Brasileirão Série A ---
    'STS': 'Santos', 'ATP': 'Athletico Paranaense', 'CAM': 'Atlético Mineiro',
    'BAH': 'Bahia', 'BOT': 'Botafogo', 'BRA': 'Bragantino', 'CHA': 'Chapecoense',
    'CRI': 'Corinthians', 'COT': 'Coritiba', 'CRU': 'Cruzeiro', 'FLA': 'Flamengo',
    'FLU': 'Fluminense', 'GRE': 'Grêmio', 'INT': 'Internacional', 'MIR': 'Mirassol',
    'PAL': 'Palmeiras', 'REM': 'Remo', 'SAO': 'São Paulo', 'VAS': 'Vasco da Gama',
    'VIT': 'Vitória',

    # --- Premier League ---
    'ARS': 'Arsenal', 'AVL': 'Aston Villa', 'BOU': 'Bournemouth', 'BRE': 'Brentford',
    'BHA': 'Brighton & Hove Albion', 'CHE': 'Chelsea', 'COV': 'Coventry City',
    'CRY': 'Crystal Palace', 'EVE': 'Everton', 'FUL': 'Fulham', 'HUL': 'Hull City',
    'IPS': 'Ipswich Town', 'LEE': 'Leeds United', 'LIV': 'Liverpool',
    'MCI': 'Manchester City', 'MUN': 'Manchester United', 'NEW': 'Newcastle United',
    'NFO': 'Nottingham Forest', 'SUN': 'Sunderland', 'TOT': 'Tottenham Hotspur',

    # --- LaLiga ---
    'RMA': 'Real Madrid', 'BCN': 'FC Barcelona', 'ATM': 'Atlético de Madrid',
    'ATH': 'Athletic Club', 'RSO': 'Real Sociedad', 'SEV': 'Sevilla FC',
    'BET': 'Real Betis', 'VIL': 'Villarreal CF', 'VAL': 'Valencia CF',
    'ESP': 'RCD Espanyol', 'RAY': 'Rayo Vallecano', 'GET': 'Getafe CF',
    'OSA': 'Osasuna', 'CEL': 'Celta de Vigo', 'ALA': 'Deportivo Alavés',
    'ELC': 'Elche CF', 'LEV': 'Levante UD', 'MAL': 'Málaga CF',
    'DEP': 'Deportivo La Coruña', 'RSA': 'Racing de Santander',

    # --- Serie A ---
    'MIL': 'AC Milan', 'ROM': 'AS Roma', 'ATA': 'Atalanta', 'BOL': 'Bologna',
    'CAG': 'Cagliari', 'COM': 'Como', 'FIO': 'Fiorentina', 'FRO': 'Frosinone',
    'GEN': 'Genoa', 'INM': 'Inter de Milán', 'JUV': 'Juventus', 'LAZ': 'Lazio',
    'LEC': 'Lecce', 'NAP': 'Napoli', 'PAR': 'Parma', 'SAS': 'Sassuolo',
    'TOR': 'Torino', 'UDI': 'Udinese', 'VNZ': 'Venezia', 'MON': 'Monza',

    # --- Bundesliga ---
    'KOL': '1. FC Köln', 'B04': 'Bayer Leverkusen', 'FCB': 'Bayern Múnich',
    'BVB': 'Borussia Dortmund', 'BMG': 'Borussia Mönchengladbach',
    'SGE': 'Eintracht Frankfurt', 'AUG': 'FC Augsburgo', 'HSV': 'Hamburgo SV',
    'MAI': 'Mainz 05', 'RBL': 'RB Leipzig', 'FRI': 'SC Friburgo',
    'PAD': 'SC Paderborn 07', 'SCH': 'Schalke 04', 'ELV': 'SV Elversberg',
    'TSG': 'TSG Hoffenheim', 'UNB': 'Union Berlin', 'VFB': 'VfB Stuttgart',
    'WER': 'Werder Bremen',

    # --- Champions League (equipos fuera de las ligas de arriba) ---
    'AEK': 'AEK Athens', 'BOD': 'Bodø/Glimt', 'BRU': 'Club Brugge',
    'FEN': 'Fenerbahçe', 'FEY': 'Feyenoord', 'GAL': 'Galatasaray',
    'LAS': 'LASK', 'LNS': 'Lens', 'LIL': 'Lille', 'PSV': 'PSV Eindhoven',
    'PSG': 'Paris Saint-Germain', 'FCP': 'Porto', 'SAB': 'Sabah Baku',
    'SHK': 'Shakhtar Donetsk', 'SLA': 'Slavia Praga', 'SLB': 'Slovan Bratislava',
    'SCP': 'Sporting CP', 'VIK': 'Viking',
}
