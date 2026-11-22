"""Babizone - données des 4 arènes (Cocody, Abobo, Yopougon, Aéroport).

Pur Python (aucune dépendance à pygame) : facile à modifier et à tester.
Plateforme = (x, y, largeur, hauteur, type).
Décor      = ("maquis"|"stand", x0, x1, y_toit, "LIBELLÉ", couleur_ou_None).
Spawn      = (x, y_pieds).  Bonus = (x, y_centre).
"""
from settings import WORLD_W, WORLD_H, GROUND_Y, ORANGE

G = GROUND_Y
ROUTE = (0, G, WORLD_W, WORLD_H - G, "route")

ARENA_ORDER = ["cocody", "abobo", "yop", "aeroport"]

ARENAS = {
    # ------------------------------------------------------------------ COCODY
    "cocody": dict(
        name="Cocody",
        desc="Villas, pont HKB et lagune Ébrié. Beaucoup de hauteur.",
        sky=((30, 85, 185), (255, 196, 130)),
        sun=(0.72, 0.6, (255, 240, 200)),
        far="cocody", mid="cocody",
        platforms=[
            ROUTE,
            (100, 780, 320, 20, "beton"),
            (560, 660, 260, 20, "beton"),
            (900, 540, 600, 24, "pont"),
            (1190, 564, 40, G - 564, "pilier"),
            (1580, 660, 260, 20, "beton"),
            (1980, 780, 320, 20, "beton"),
            (220, 540, 200, 16, "echafaudage"),
            (1980, 540, 200, 16, "echafaudage"),
            (1050, 340, 300, 16, "echafaudage"),
            (700, 884, 150, 56, "gbaka"),
            (1560, 884, 150, 56, "gbaka"),
        ],
        decor=[
            ("maquis", 100, 420, 780, "RESTO CHEZ NANA", None),
            ("stand", 580, 800, 660, "JUS BISSAP", (160, 50, 120)),
            ("stand", 1600, 1820, 660, "ATTIÉKÉ", (240, 190, 30)),
            ("maquis", 1980, 2300, 780, "BAR LE CHIC", None),
        ],
        spawns=[(100, G), (2300, G), (560, G), (1850, G),
                (260, 779), (690, 659), (1710, 659), (2140, 779),
                (1000, 539), (1400, 539), (320, 539), (2090, 539), (1200, 339)],
        pickups=[(260, 755), (690, 635), (1050, 515), (1350, 515), (1710, 635),
                 (2140, 755), (320, 515), (2090, 515), (1200, 315),
                 (100, 915), (2300, 915), (1000, 915), (1450, 915)],
    ),
    # ------------------------------------------------------------------ ABOBO
    "abobo": dict(
        name="Abobo",
        desc="Marché dense, toits de tôle en escalier. Combats serrés.",
        sky=((70, 35, 95), (255, 140, 50)),
        sun=(0.3, 0.66, (255, 205, 120)),
        far="abobo", mid="abobo",
        platforms=[
            ROUTE,
            (80, 790, 260, 18, "toit_tole"),
            (400, 690, 240, 18, "toit_tole"),
            (700, 590, 260, 18, "toit_tole"),
            (1010, 480, 380, 18, "toit_tole"),
            (1440, 590, 260, 18, "toit_tole"),
            (1760, 690, 240, 18, "toit_tole"),
            (2060, 790, 260, 18, "toit_tole"),
            (160, 560, 200, 16, "echafaudage"),
            (2040, 560, 200, 16, "echafaudage"),
            (1100, 330, 200, 16, "echafaudage"),
            (950, 884, 150, 56, "gbaka"),
            (1300, 884, 150, 56, "gbaka"),
        ],
        decor=[
            ("stand", 100, 320, 790, "ALLOCO", (240, 190, 30)),
            ("stand", 420, 620, 690, "GARBA", ORANGE),
            ("stand", 720, 940, 590, "BRAISÉ", (210, 60, 50)),
            ("maquis", 1020, 1380, 480, "MARCHÉ D'ABOBO", None),
            ("stand", 1460, 1680, 590, "KEDJENOU", (60, 150, 90)),
            ("stand", 1780, 1980, 690, "ATTIÉKÉ", (240, 190, 30)),
            ("stand", 2080, 2300, 790, "FOUTOU", (150, 90, 50)),
        ],
        spawns=[(100, G), (2300, G), (560, G), (1840, G),
                (210, 789), (520, 689), (830, 589), (1200, 479),
                (1570, 589), (1880, 689), (2190, 789),
                (260, 559), (2140, 559), (1200, 329)],
        pickups=[(210, 765), (520, 665), (830, 565), (1200, 455), (1570, 565),
                 (1880, 665), (2190, 765), (260, 535), (2140, 535), (1200, 305),
                 (100, 915), (2300, 915), (850, 915), (1180, 915)],
    ),
    # ------------------------------------------------------------------ YOPOUGON
    "yop": dict(
        name="Yopougon",
        desc="Maquis, gbakas et pont. L'ambiance de « Babi » par excellence.",
        sky=((28, 22, 78), (255, 128, 62)),
        sun=(0.72, 0.64, (255, 226, 140)),
        far="plateau", mid="yop",
        platforms=[
            ROUTE,
            (120, 760, 340, 18, "toit_tole"),
            (620, 680, 280, 18, "toit_tole"),
            (950, 520, 500, 24, "pont"),
            (1180, 544, 40, G - 544, "pilier"),
            (1500, 680, 280, 18, "toit_tole"),
            (1940, 760, 340, 18, "toit_tole"),
            (200, 520, 220, 16, "echafaudage"),
            (1980, 520, 220, 16, "echafaudage"),
            (1050, 330, 300, 16, "echafaudage"),
            (780, 860, 140, 80, "conteneur"),
            (1580, 860, 140, 80, "conteneur"),
            (1030, 884, 150, 56, "gbaka"),
            (1240, 884, 150, 56, "gbaka"),
        ],
        decor=[
            ("maquis", 120, 460, 760, "MAQUIS CHEZ MAMAN", None),
            ("stand", 640, 880, 680, "GARBA 500F", ORANGE),
            ("stand", 1520, 1760, 680, "ALLOCO", (240, 190, 30)),
            ("maquis", 1940, 2280, 760, "CHEZ TANTIE ADJOUA", None),
        ],
        spawns=[(100, G), (2300, G), (560, G), (1850, G),
                (300, 759), (760, 679), (1640, 679), (2100, 759),
                (1000, 519), (1400, 519), (300, 519), (2090, 519), (1200, 329)],
        pickups=[(290, 735), (760, 655), (1100, 495), (1300, 495), (1650, 655),
                 (2110, 735), (300, 495), (2080, 495), (1200, 305),
                 (100, 915), (2300, 915), (950, 915), (1470, 915)],
    ),
    # ------------------------------------------------------------------ AÉROPORT
    "aeroport": dict(
        name="Aéroport",
        desc="Port-Bouët : avions, hangars et tour de contrôle.",
        sky=((10, 20, 70), (240, 120, 90)),
        sun=(0.3, 0.7, (255, 200, 120)),
        far="aeroport", mid="aeroport",
        platforms=[
            ROUTE,
            (200, 800, 460, 54, "avion"),
            (1740, 800, 460, 54, "avion"),
            (780, 680, 260, 18, "hangar"),
            (1360, 680, 260, 18, "hangar"),
            (1100, 420, 200, 24, "cabine"),
            (1180, 444, 40, G - 444, "tour"),
            (300, 520, 220, 16, "echafaudage"),
            (1880, 520, 220, 16, "echafaudage"),
            (1130, 260, 140, 16, "echafaudage"),
            (680, 860, 140, 80, "conteneur"),
            (1260, 860, 140, 80, "conteneur"),
        ],
        decor=[
            ("stand", 800, 1020, 680, "DUTY FREE", (60, 120, 220)),
            ("stand", 1380, 1600, 680, "BAGAGES", (160, 100, 40)),
        ],
        spawns=[(100, G), (2300, G), (1100, G), (1700, G),
                (430, 799), (1970, 799), (910, 679), (1490, 679),
                (1130, 419), (1270, 419), (410, 519), (1990, 519), (1200, 259)],
        pickups=[(430, 775), (1970, 775), (910, 655), (1490, 655), (1130, 395),
                 (1270, 395), (410, 495), (1990, 495), (1200, 235),
                 (100, 915), (2300, 915), (1100, 915), (1700, 915)],
    ),
}


# Palette « bande dessinée » de chaque arène (murs, corniches, volets)
LOOKS = {
    "yop": dict(plaster=(226, 188, 118), trim=(238, 224, 188), shutter=(46, 112, 92)),
    "cocody": dict(plaster=(240, 230, 206), trim=(255, 250, 236), shutter=(44, 112, 152)),
    "abobo": dict(plaster=(214, 120, 92), trim=(240, 204, 154), shutter=(40, 122, 100)),
    "aeroport": dict(plaster=(170, 178, 198), trim=(226, 230, 242), shutter=(62, 102, 172)),
}
for _k, _v in LOOKS.items():
    ARENAS[_k]["look"] = _v
