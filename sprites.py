"""Babizone - personnages et armes dessinés en code, style « cartoon » :
contours noirs épais, grosse tête, ombrage à 2 tons (cel-shading).

Tout est vectoriel (aucun fichier image) : teint, coiffure, couleur de cheveux
et tenue sont donc librement combinables.
"""
import math
import pygame
from settings import SUPERSAMPLE

INK = (24, 18, 22)
GRIP = 14                      # distance épaule -> main qui tient la crosse

HAIRS = ["Casque ôtodji", "Afro", "Tresses", "Chignon", "Casquette", "Bonnet", "Rasé", "Locks", "Pics"]
ACCESSORIES = ["Aucun", "Lunettes de protection", "Lunettes rondes", "Bandana", "Bandeau", "Écharpe"]
BEARDS = ["Aucune", "Moustache", "Bouc", "Barbe"]
HAIR_COLORS = [("Noir", (28, 22, 22)), ("Brun", (96, 60, 36)), ("Blond", (232, 196, 90)),
               ("Rouge", (205, 45, 65)), ("Bleu", (50, 110, 235)), ("Turquoise", (60, 200, 190)),
               ("Violet", (150, 70, 200)), ("Orange", (242, 125, 30))]


def shade(c, f=0.74):
    return tuple(max(0, min(255, int(v * f))) for v in c[:3])


def light(c, f=1.25):
    return tuple(max(0, min(255, int(v * f))) for v in c[:3])



# ---------------------------------------------------------------------------
#  Dessin en haute résolution (K = facteur) puis réduction => traits lissés
# ---------------------------------------------------------------------------
_K = 2


def _pt(p):
    return (p[0] * _K, p[1] * _K)


def _w(w):
    return max(1, int(round(w * _K))) if w else 0


def _line(surf, col, a, b, w=1):
    pygame.draw.line(surf, col, _pt(a), _pt(b), _w(w) or 1)


def _lines(surf, col, pts, closed=False, w=1):
    pygame.draw.lines(surf, col, closed, [_pt(p) for p in pts], _w(w) or 1)


def _circle(surf, col, c, r, w=0):
    pygame.draw.circle(surf, col, (int(c[0] * _K), int(c[1] * _K)), max(1, int(r * _K)), _w(w))


def _ellipse(surf, col, rect, w=0):
    x, y, ww, hh = rect
    pygame.draw.ellipse(surf, col, (int(x * _K), int(y * _K), int(ww * _K), int(hh * _K)), _w(w))


def _rect(surf, col, rect, w=0, border_radius=0):
    x, y, ww, hh = rect
    pygame.draw.rect(surf, col, (int(x * _K), int(y * _K), int(ww * _K), int(hh * _K)), _w(w),
                     border_radius=int(border_radius * _K))


def _polygon(surf, col, pts, w=0):
    pygame.draw.polygon(surf, col, [_pt(p) for p in pts], _w(w))

# ---------------------------------------------------------------------------
#  Primitives avec contour
# ---------------------------------------------------------------------------
def poly(surf, pts, fill, w=2):
    pts = [(float(x), float(y)) for x, y in pts]
    _polygon(surf, fill, pts)
    _polygon(surf, INK, pts, w)


def disc(surf, c, r, fill, w=2):
    _circle(surf, fill, c, r)
    _circle(surf, INK, c, r, w)


def chain(surf, pts, width, fill):
    """Membre à plusieurs segments : on trace tous les contours, puis tous les remplissages."""
    ow = width + 4
    for a, b in zip(pts, pts[1:]):
        _line(surf, INK, a, b, ow)
    for p in pts:
        _circle(surf, INK, p, ow / 2)
    for a, b in zip(pts, pts[1:]):
        _line(surf, fill, a, b, width)
    for p in pts:
        _circle(surf, fill, p, width / 2)


def arc_pts(cx, cy, r, t0, t1, f, step=15):
    """Points d'un arc (degrés, y vers le bas), miroir horizontal selon la direction f."""
    pts, t = [], t0
    sgn = 1 if t1 >= t0 else -1
    while (t <= t1) if sgn > 0 else (t >= t1):
        a = math.radians(t)
        pts.append((cx + f * r * math.cos(a), cy + r * math.sin(a)))
        t += step * sgn
    return pts


def hair_cap(surf, hx, hy, f, col, depth=7, r=14.5, t0=165, t1=345):
    cx, cy = hx, hy
    outer = arc_pts(hx, hy, r, t0, t1, f)
    inner = []
    for t in range(t1, t0 - 1, -15):
        d = 3 + (depth - 3) * math.sin(math.radians((t - t0) / (t1 - t0) * 180))
        a = math.radians(t)
        inner.append((hx + f * (r - d) * math.cos(a), hy + (r - d) * math.sin(a)))
    poly(surf, outer + inner, col)
    _lines(surf, light(col, 1.45), arc_pts(cx, cy, r - 3.2, 215, 300, f), False, 2)


# ---------------------------------------------------------------------------
#  Armes (coordonnées locales : x = vers le canon, y = vers le bas, origine = main)
# ---------------------------------------------------------------------------
DARK, METAL = (36, 38, 46), (78, 82, 94)
TAN, TAN_D = (160, 120, 76), (112, 82, 52)
WOOD, WOOD_L = (116, 72, 40), (172, 116, 64)


def _r(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


WEAPONS = {
    "nouchi": [   # pistolet
        ("p", DARK, [(-5, 0), (9, 0), (9, 3), (3, 3), (1, 12), (-6, 12), (-6, 3)]),
        ("p", METAL, _r(-5, -6, 12, 0)),
        ("p", DARK, _r(12, -4, 14, -1)),
        ("p", TAN, [(-6, 3), (1, 3), (0, 11), (-6, 11)]),
        ("p", (255, 210, 90), _r(10, -7, 12, -6)),
    ],
    "coupe": [    # fusil d'assaut à crosse beige
        ("p", TAN, [(-23, -8), (-6, -5), (-6, 5), (-23, 10)]),
        ("p", TAN_D, [(-23, 6), (-6, 3), (-6, 5), (-23, 10)]),
        ("p", DARK, [(2, 5), (8, 5), (9, 16), (3, 17)]),                # chargeur
        ("p", DARK, [(-4, 5), (2, 5), (0, 14), (-7, 13)]),              # poignée
        ("p", DARK, _r(-6, -8, 17, 5)),                                 # boîtier
        ("p", METAL, _r(17, -7, 31, 3)),                                # garde-main
        ("p", DARK, _r(31, -5, 43, -2)),                                # canon
        ("p", METAL, _r(41, -6, 46, -1)),                               # bouche
        ("p", DARK, _r(1, -12, 8, -8)),                                 # mire
        ("p", DARK, _r(36, -9, 39, -5)),
        ("l", (150, 155, 170), (20, -3), (29, -3), 2),
    ],
    "dozo": [     # fusil à pompe du chasseur dozo
        ("p", WOOD, [(-24, -6), (-6, -5), (-6, 4), (-24, 10)]),
        ("p", WOOD_L, [(-24, -6), (-6, -5), (-6, -2), (-24, 0)]),
        ("p", METAL, _r(-6, -7, 9, 4)),
        ("p", METAL, _r(9, 0, 40, 4)),                                  # tube
        ("p", WOOD_L, _r(16, 0, 32, 7)),                                # pompe
        ("p", DARK, _r(9, -6, 50, -1)),                                 # canon
        ("p", (242, 125, 30), _r(36, -6, 40, 4)),                       # sangle orange
        ("p", DARK, _r(49, -7, 52, 0)),
    ],
    "sniper": [   # fusil de précision avec lunette
        ("p", TAN, [(-26, -6), (-6, -7), (-6, 5), (-26, 10)]),
        ("p", TAN_D, [(-26, 6), (-6, 3), (-6, 5), (-26, 10)]),
        ("p", DARK, _r(-6, -8, 15, 5)),
        ("p", DARK, [(-3, 5), (3, 5), (1, 13), (-5, 12)]),
        ("p", DARK, _r(15, -4, 60, -1)),
        ("p", METAL, _r(56, -7, 66, 1)),
        ("p", METAL, _r(-1, -15, 25, -9)),                              # lunette
        ("p", DARK, _r(-2, -16, 2, -8)),
        ("p", (120, 220, 235), _r(24, -14, 27, -10)),
        ("p", DARK, _r(4, -9, 7, -8)),
        ("p", DARK, _r(18, -9, 21, -8)),
        ("l", (30, 30, 38), (38, -1), (33, 10), 3),                     # bipied
        ("l", (30, 30, 38), (38, -1), (43, 10), 3),
    ],
}
# distance (le long de la visée) entre la main de la crosse et la main de l'avant
FOREND = {"nouchi": 0, "coupe": 22, "dozo": 22, "sniper": 24}


def draw_weapon(surf, key, grip, ang, flip):
    c, s = math.cos(ang), math.sin(ang)

    def tf(p):
        x, y = p
        if flip:
            y = -y
        return (grip[0] + x * c - y * s, grip[1] + x * s + y * c)

    for shp in WEAPONS[key]:
        if shp[0] == "p":
            poly(surf, [tf(p) for p in shp[2]], shp[1], 2)
        else:
            _line(surf, shp[1], tf(shp[2]), tf(shp[3]), shp[4])


# ---------------------------------------------------------------------------
#  Personnage
# ---------------------------------------------------------------------------
def _arm(surf, shoulder, hand, col, glove):
    mid = ((shoulder[0] + hand[0]) / 2, (shoulder[1] + hand[1]) / 2 + 5)
    chain(surf, [shoulder, mid, hand], 7, col)
    disc(surf, hand, 4, glove, 2)


CANVAS_W, CANVAS_H, ORG_X, ORG_Y = 250, 230, 125, 150      # toile locale (px logiques) et origine (pieds)
UP = 4                                                      # hauteur supplémentaire des jambes
CHAR_SCALE = 1.15                                           # le personnage est dessiné 15 % plus grand que sa hitbox


def draw_character(surf, p, ox, oy, supersample=None, out_scale=1):
    """Dessine le personnage en haute résolution puis le réduit (anticrénelage).
    out_scale > 1 sert à l'aperçu agrandi de l'écran « Mon personnage »."""
    global _K
    ss = supersample or SUPERSAMPLE
    _K = ss * CHAR_SCALE
    tmp = pygame.Surface((CANVAS_W * ss, CANVAS_H * ss), pygame.SRCALPHA)
    _render(tmp, p, ORG_X / CHAR_SCALE, ORG_Y / CHAR_SCALE)
    size = (CANVAS_W * out_scale, CANVAS_H * out_scale)
    if size != tmp.get_size():
        tmp = pygame.transform.smoothscale(tmp, size)
    surf.blit(tmp, (p.rect.centerx - ox - ORG_X * out_scale, p.rect.bottom - oy - ORG_Y * out_scale))


def _lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def _arm(surf, shoulder, hand, skin, glove, sleeve=None, style="tee"):
    mid = ((shoulder[0] + hand[0]) / 2, (shoulder[1] + hand[1]) / 2 + 3)
    if sleeve is not None and style == "jacket":                   # manche longue
        chain(surf, [shoulder, mid, hand], 8.5, sleeve)
    else:
        chain(surf, [shoulder, mid, hand], 7.5, skin)                # bras musclé
        _line(surf, light(skin, 1.22), _lerp(shoulder, mid, .25), _lerp(mid, hand, .5), 2)
        if sleeve is not None and style == "tee":                    # manche courte
            chain(surf, [shoulder, _lerp(shoulder, mid, .8)], 10, sleeve)
    disc(surf, hand, 4.6, glove, 2)                                  # main gantée
    _circle(surf, shade(glove, 0.8), (hand[0] + 1.2, hand[1] + 1.2), 1.6)


def _render(surf, p, cx, by):
    bb = by - UP                                  # le haut du corps est relevé : jambes plus longues
    pal = p.pal
    f = p.facing
    skin = pal["skin"]
    skin_d = shade(skin, 0.74)
    tee = (255, 255, 255) if p.hurt > 0 else pal["tee"]
    pants, boots, accent = pal["shorts"], pal["shoes"], pal["accent"]
    style = pal.get("style", "tee")
    hair = pal.get("hair", 0)
    hc = pal.get("hair_col", (28, 22, 22))
    acc = pal.get("acc", 0)
    beard = pal.get("beard", 0)
    ca, sa = math.cos(p.aim), math.sin(p.aim)
    run = math.sin(p.anim) if p.on_ground else 0.0

    shoulder = (cx, bb - 24)
    grip = (shoulder[0] + ca * GRIP, shoulder[1] + sa * GRIP)
    wkey = p.weapon.key
    fo = FOREND[wkey]
    hand2 = (grip[0] + ca * fo, grip[1] + sa * fo) if fo else (grip[0] - ca * 2, grip[1] - sa * 2 + 2)
    hx, hy = cx + f, bb - 43 + (1 if run < -0.5 else 0)
    glove = (46, 40, 44)
    sleeve = tee if style in ("tee", "jacket") else None

    # ---- derrière : bras éloigné, jet-pack, accessoires arrière ----------------------------
    _arm(surf, (cx - f * 3, bb - 24), hand2, skin_d, shade(glove, 1.1), sleeve and shade(sleeve, 0.8), style)

    jx = cx - f * 15
    poly(surf, _r(jx - 6.5, bb - 37, jx + 6.5, bb - 14), (80, 84, 100))
    _rect(surf, (210, 215, 230), (jx - 4, bb - 36, 3, 18))                   # reflet métal
    _rect(surf, accent, (jx - 6.5, bb - 28, 13, 4))
    _rect(surf, INK, (jx - 6.5, bb - 28, 13, 4), 1)
    poly(surf, [(jx - 5.5, bb - 14), (jx + 5.5, bb - 14), (jx + 3.5, bb - 8), (jx - 3.5, bb - 8)], (52, 54, 64))
    _circle(surf, (150, 215, 255), (jx, bb - 33), 2.2)
    if acc == 5:                                                             # queue de l'écharpe
        chain(surf, [(cx - f * 4, bb - 33), (cx - f * 13, bb - 28), (cx - f * 16, bb - 18)], 5, accent)

    if hair == 1:
        disc(surf, (hx - f * 2, hy - 6), 19.5, hc, 2)
    elif hair == 2:
        for k in range(3):
            bx = hx - f * (8 + k * 3)
            pts = [(bx, hy - 5), (bx - f * 2, hy + 4), (bx - f * 3, hy + 12 + k * 2), (bx - f * 2, hy + 19 + k * 2)]
            chain(surf, pts, 4.4, hc)
            _circle(surf, accent, pts[-1], 2.2)
    elif hair == 7:
        for k in range(5):
            bx = hx - f * (5 + k * 2.6)
            chain(surf, [(bx, hy - 8 + k), (bx - f * 2, hy + 4 + k), (bx - f * 3, hy + 14 + k * 2)], 4.4, hc)
    elif hair == 4:
        poly(surf, [(hx - f * 12, hy - 2), (hx - f * 6, hy - 6), (hx - f * 5, hy + 7), (hx - f * 13, hy + 9)], hc)

    # ---- jambes + bottes détaillées ------------------------------------------------------------
    for s_ in (-1, 1):
        hip = (cx + s_ * 5.5, by - 20)
        if p.on_ground:
            foot = (hip[0] + s_ * run * 8, by - 5)
            knee = ((hip[0] + foot[0]) / 2 + f * 2, by - 12)
        else:
            foot = (hip[0] + s_ * 4 + f * 2, by - 6)
            knee = (hip[0] + f * 5, by - 13)
        col = pants if s_ == 1 else shade(pants, 0.8)
        chain(surf, [hip, knee, foot], 10, col)
        _line(surf, light(col, 1.3), (hip[0] + f * 2, hip[1] + 1), (knee[0] + f * 2, knee[1]), 1.6)
        bx, byy = foot[0] + f * 2 - 8, foot[1] + 1 - 5
        _rect(surf, boots, (bx, byy, 16, 9), border_radius=3)
        _rect(surf, shade(boots, 0.6), (bx - 1, byy + 6.5, 18, 3.5), border_radius=1)     # semelle épaisse
        _rect(surf, INK, (bx - 1, byy, 18, 10), 2, border_radius=3)
        for k in range(3):                                                                # lacets
            _line(surf, (235, 235, 235), (bx + 7 + f * 2 + k * 3, byy + 1.5), (bx + 9 + f * 2 + k * 3, byy + 3), 1)

    # ---- torse selon le style de tenue ----------------------------------------------------------
    torso = [(cx - 13, bb - 36), (cx + 13, bb - 36), (cx + 11, bb - 16), (cx - 11, bb - 16)]
    stripe = pal["stripe"]
    if style == "jacket":
        poly(surf, torso, stripe)
        poly(surf, [(cx - 13, bb - 36), (cx - 3, bb - 36), (cx - 2, bb - 16), (cx - 11, bb - 16)], tee)
        poly(surf, [(cx + 3, bb - 36), (cx + 13, bb - 36), (cx + 11, bb - 16), (cx + 2, bb - 16)], tee)
        poly(surf, [(cx - 6, bb - 37), (cx - 1, bb - 37), (cx - 4, bb - 31)], shade(tee, 0.8), 1)
        poly(surf, [(cx + 1, bb - 37), (cx + 6, bb - 37), (cx + 4, bb - 31)], shade(tee, 0.8), 1)
    elif style == "vest":
        poly(surf, torso, stripe if stripe != (255, 255, 255) else (236, 232, 220))
        poly(surf, [(cx - 13, bb - 36), (cx - 4, bb - 36), (cx - 3, bb - 16), (cx - 11, bb - 16)], tee)
        poly(surf, [(cx + 4, bb - 36), (cx + 13, bb - 36), (cx + 11, bb - 16), (cx + 3, bb - 16)], tee)
        _rect(surf, shade(tee, 0.7), (cx - 11, bb - 26, 7, 6))                              # poche
    else:
        poly(surf, torso, tee)
        if style == "tank":
            poly(surf, [(cx - 5, bb - 36), (cx + 5, bb - 36), (cx, bb - 27)], skin, 2)       # col en V
        _polygon(surf, stripe, [(cx - 12.4, bb - 29), (cx + 12.4, bb - 29), (cx + 11.7, bb - 25), (cx - 11.7, bb - 25)])
    poly(surf, [(cx - f * 13, bb - 36), (cx - f * 6, bb - 36), (cx - f * 5, bb - 16), (cx - f * 11, bb - 16)], shade(tee, 0.78), 1)
    _line(surf, light(tee, 1.35), (cx + f * 7, bb - 34), (cx + f * 6, bb - 20), 2)           # reflet
    poly(surf, _r(cx - 11.5, bb - 19, cx + 11.5, bb - 15), (42, 34, 32), 1)                  # ceinture
    _rect(surf, accent, (cx - 3.5, bb - 19, 7, 4))
    _polygon(surf, INK, torso, 2)

    if acc in (3, 5):                                                                        # bandana / écharpe autour du cou
        poly(surf, [(cx - 10, bb - 37), (cx + 10, bb - 37), (cx + f * 2, bb - 25)], accent)
        _line(surf, light(accent, 1.4), (cx - 6, bb - 35), (cx + f * 1, bb - 29), 1.6)
        _circle(surf, shade(accent, 0.8), (cx - f * 9, bb - 36), 3)

    # ---- tête ----------------------------------------------------------------------------------------
    disc(surf, (hx - f * 7, hy + 1), 3.2, skin_d, 2)                                          # oreille
    _circle(surf, skin_d, (hx, hy), 13)
    _circle(surf, skin, (hx + f * 2, hy - 1), 11)
    _circle(surf, light(skin, 1.18), (hx + f * 4, hy - 5), 5)                                 # reflet du front
    _circle(surf, INK, (hx, hy), 13, 2)

    if hair != 0:
        eye = (hx + f * 5.5, hy - 1)
        _ellipse(surf, (255, 255, 255), (eye[0] - 4.6, eye[1] - 5.6, 9.2, 11))
        _circle(surf, pal.get("iris", (72, 48, 34)), (eye[0] + f * 1.2, eye[1] + .2), 3.4)
        _circle(surf, INK, (eye[0] + f * 1.4, eye[1] + .2), 1.7)
        _circle(surf, (255, 255, 255), (eye[0] + f * .4, eye[1] - 1.3), 1)
        _ellipse(surf, INK, (eye[0] - 4.6, eye[1] - 5.6, 9.2, 11), 1.3)
        _line(surf, INK, (eye[0] - 4.8, eye[1] - 5), (eye[0] + 4.8, eye[1] - 5.8), 2.4)      # paupière
        _line(surf, INK, (hx + f * 0.5, hy - 9), (hx + f * 11, hy - 5.5), 3.4)               # sourcil froncé
        poly(surf, [(hx + f * 12.2, hy - .5), (hx + f * 15, hy + 2.8), (hx + f * 11.2, hy + 3.6)], skin, 1.3)
        _line(surf, INK, (hx + f * 6, hy + 8.5), (hx + f * 11.5, hy + 8.5), 2)               # bouche
        if beard == 3:                                                                       # barbe
            poly(surf, [(hx - f * 9, hy + 1), (hx - f * 5, hy + 8), (hx + f * 3, hy + 15), (hx + f * 11, hy + 12),
                        (hx + f * 6, hy + 9.5), (hx + f * 12, hy + 7), (hx + f * 7, hy + 4), (hx - f * 2, hy + 5)], hc, 1.6)
        elif beard == 2:                                                                     # bouc
            poly(surf, [(hx + f * 3, hy + 11), (hx + f * 9, hy + 10), (hx + f * 8, hy + 17), (hx + f * 4, hy + 16)], hc, 1.6)
        elif beard == 1:                                                                     # moustache en guidon
            poly(surf, [(hx + f * 6, hy + 5.6), (hx + f * 11.5, hy + 4.6), (hx + f * 14.5, hy + 3.4), (hx + f * 14, hy + 7.4),
                        (hx + f * 10.5, hy + 7), (hx + f * 6, hy + 7.8)], hc, 1.5)

    if hair == 0:
        dome = arc_pts(hx, hy - 1, 15.8, 30, -210, f, step=15)
        poly(surf, dome, pal["helmet"])
        _lines(surf, light(pal["helmet"], 1.1), arc_pts(hx, hy - 1, 12.6, -200, -135, f), False, 2)
        _lines(surf, accent, arc_pts(hx, hy - 1, 11.5, -170, -20, f), False, 3)
        visor = [(hx + f * 3, hy - 7), (hx + f * 15.5, hy - 7), (hx + f * 15.5, hy + 3.5), (hx + f * 4, hy + 4.5)]
        poly(surf, visor, (26, 32, 52))
        _line(surf, (170, 200, 255), (hx + f * 6, hy - 5), (hx + f * 11.5, hy - 5), 2)
    elif hair == 1:
        hair_cap(surf, hx, hy, f, hc, depth=9, r=15)
    elif hair == 2:
        hair_cap(surf, hx, hy, f, hc, depth=8)
    elif hair == 3:
        disc(surf, (hx - f * 3, hy - 17), 7, hc, 2)
        hair_cap(surf, hx, hy, f, hc, depth=7)
    elif hair == 4:
        hair_cap(surf, hx, hy, f, accent, depth=10, r=15)
        poly(surf, [(hx + f * 7, hy - 9), (hx + f * 22, hy - 5), (hx + f * 21, hy - 1), (hx + f * 7, hy - 4)], shade(accent, 0.8))
        _circle(surf, INK, (hx, hy - 14), 2)
    elif hair == 5:
        col5 = stripe if stripe != (255, 255, 255) else accent
        hair_cap(surf, hx, hy, f, col5, depth=12, r=16)
        hair_cap(surf, hx, hy + 1, f, shade(accent, 0.9), depth=4, r=14.5, t0=160, t1=350)
        disc(surf, (hx, hy - 17), 4, (245, 245, 245), 2)
    elif hair == 6:
        hair_cap(surf, hx, hy, f, hc, depth=4)
    elif hair == 7:
        hair_cap(surf, hx, hy, f, hc, depth=8)
    elif hair == 8:                                                                           # cheveux en pics
        hair_cap(surf, hx, hy, f, hc, depth=6, r=14.8)
        for k, ang in enumerate(range(-165, -10, 30)):
            a1, a2 = math.radians(ang - 11), math.radians(ang + 11)
            tip = math.radians(ang + 5)
            poly(surf, [(hx + f * 13.5 * math.cos(a1), hy + 13.5 * math.sin(a1)),
                        (hx + f * (21 + k % 2 * 5) * math.cos(tip), hy + (21 + k % 2 * 5) * math.sin(tip)),
                        (hx + f * 13.5 * math.cos(a2), hy + 13.5 * math.sin(a2))], hc, 1.8)

    if hair != 0 and acc == 1:                                                                # lunettes de protection
        _line(surf, INK, (hx - f * 13, hy - 9.5), (hx + f * 12, hy - 11), 5.5)
        _line(surf, (74, 52, 40), (hx - f * 13, hy - 9.5), (hx + f * 12, hy - 11), 3)
        _ellipse(surf, (255, 196, 70), (hx + f * 3 - 7.5, hy - 17, 15, 10))
        _ellipse(surf, (255, 240, 170), (hx + f * 3 - 5, hy - 15.5, 6, 3.5))
        _ellipse(surf, INK, (hx + f * 3 - 7.5, hy - 17, 15, 10), 2)
    elif hair != 0 and acc == 2:                                                              # lunettes rondes
        e = (hx + f * 6, hy - 1)
        _circle(surf, (150, 210, 255), e, 6.4)
        _circle(surf, (235, 250, 255), (e[0] - 1.6, e[1] - 2), 1.8)
        _circle(surf, INK, e, 6.4, 2)
        _line(surf, INK, (e[0] - f * 6.4, e[1] - 1), (hx - f * 8, hy + 0), 1.8)
    elif acc == 4:                                                                            # bandeau
        _lines(surf, INK, arc_pts(hx, hy - 1, 13.2, 182, 355, f), False, 7)
        _lines(surf, accent, arc_pts(hx, hy - 1, 13.2, 182, 355, f), False, 4.2)
        chain(surf, [(hx - f * 12, hy - 4), (hx - f * 18, hy - 1), (hx - f * 21, hy + 6)], 3.4, accent)

    # ---- arme + bras proche -----------------------------------------------------------------------------
    draw_weapon(surf, wkey, grip, p.aim, ca < 0)
    _arm(surf, shoulder, grip, skin, glove, sleeve, style)


# ---------------------------------------------------------------------------
#  Icônes d'armes (pour les armes au sol) : dessinées une seule fois, lissées, mises en cache
# ---------------------------------------------------------------------------
_ICONS = {}


def weapon_icon(key, scale=0.9):
    k = (key, scale)
    if k not in _ICONS:
        global _K
        old, _K = _K, 3
        big = pygame.Surface((130 * 3, 60 * 3), pygame.SRCALPHA)
        draw_weapon(big, key, (44, 30), 0.0, False)
        _K = old
        _ICONS[k] = pygame.transform.smoothscale(big, (int(130 * scale), int(60 * scale)))
    return _ICONS[k]
