"""Babizone - décors d'arrière-plan (couches parallaxe) pour chaque arène."""
import math
import random
import pygame
from settings import *
from artkit import INK, shade, light, ink_rect, grand_facade, plaster_wall, arch_window, balcony, rubble

_FONTS = {}


def font(size):
    if size not in _FONTS:
        _FONTS[size] = pygame.font.Font(None, size)
    return _FONTS[size]


def blit_center_text(surf, text, size, color, center):
    img = font(size).render(text, True, color)
    surf.blit(img, img.get_rect(center=center))


def draw_gbaka(surf, x, y, w, label, stripe, flip=False):
    """Minibus abidjanais. Zone occupée : (x, y, w, 56)."""
    h = 44

    def mx(off, width):
        return x + off if not flip else x + w - off - width

    pygame.draw.rect(surf, (238, 238, 228), (x, y, w, h), border_radius=8)
    pygame.draw.rect(surf, INK, (x, y, w, h), 3, border_radius=8)
    pygame.draw.rect(surf, stripe, (x, y + 26, w, 14))
    for i in range(5):
        pygame.draw.rect(surf, (70, 100, 140), (mx(10 + i * 24, 18), y + 7, 18, 14), border_radius=2)
    pygame.draw.rect(surf, (120, 160, 205), (mx(w - 24, 16), y + 7, 16, 17), border_radius=3)
    blit_center_text(surf, label, 17, (20, 20, 20), (x + w // 2 - (6 if not flip else -6), y + 33))
    pygame.draw.rect(surf, (255, 225, 120), (mx(w - 5, 5), y + 29, 5, 6))
    pygame.draw.rect(surf, (60, 60, 70), (x, y + 40, w, 4))
    for wx in (28, w - 28):
        pygame.draw.circle(surf, (20, 20, 25), (x + wx, y + h), 11)
        pygame.draw.circle(surf, (170, 170, 180), (x + wx, y + h), 5)
        pygame.draw.circle(surf, INK, (x + wx, y + h), 11, 2)


def _layer(factor):
    w = int(WORLD_W * factor) + SCREEN_W + 40
    return pygame.Surface((w, WORLD_H), pygame.SRCALPHA), w


def _palm(s, bx, by, height, rng):
    top = (bx + rng.randint(-25, 25), by - height)
    pygame.draw.line(s, (96, 70, 48), (bx, by), top, 7)
    for a in (-2.7, -2.1, -1.5, -0.9, -0.4, 0.1, 0.8):
        ex = top[0] + math.cos(a) * 55
        ey = top[1] + math.sin(a) * 22 + 26
        pygame.draw.line(s, (36, 120, 70), top, (ex, ey), 5)
        pygame.draw.line(s, (60, 160, 90), top, (ex, ey), 2)


def _bridge(s, w, hz, p1, p2, span_end, scale=1.0):
    deck = hz - 30
    c1, c2 = (215, 215, 232), (232, 232, 245)
    ph = int(250 * scale)
    pygame.draw.line(s, c1, (0, deck), (span_end, deck), 6)
    for p in (p1, p2):
        pygame.draw.line(s, c1, (p - 16, deck), (p, deck - ph), 6)
        pygame.draw.line(s, c1, (p + 16, deck), (p, deck - ph), 6)
        for k in range(1, 9):
            pygame.draw.line(s, c2, (p, deck - ph), (p - k * 22, deck), 1)
            pygame.draw.line(s, c2, (p, deck - ph), (p + k * 22, deck), 1)


# ===========================================================================
#  COUCHES LOINTAINES (parallaxe 0.12)
# ===========================================================================
def far_city(seed, cols, landmarks, water, win_col):
    """Skyline de tours. landmarks : 'pyramide', 'cathedrale', 'pont', 'ivoire', 'voiles'."""
    s, w = _layer(0.12)
    rng = random.Random(seed)
    hz = 900
    pygame.draw.rect(s, water, (0, hz, w, WORLD_H - hz))
    wl = tuple(min(255, c + 45) for c in water)
    for ry in range(hz + 6, hz + 40, 9):
        pygame.draw.line(s, wl, (0, ry), (w, ry), 1)

    x = -20
    while x < w:
        tw, th = rng.randint(36, 80), rng.randint(140, 430)
        col = tuple(rng.randint(*c) for c in cols)
        pygame.draw.rect(s, col, (x, hz - th, tw, th))
        for wy in range(hz - th + 10, hz - 10, 16):
            for wx in range(x + 6, x + tw - 8, 12):
                if rng.random() < 0.35:
                    pygame.draw.rect(s, win_col, (wx, wy, 5, 8))
        x += tw + rng.randint(-6, 10)

    if "pyramide" in landmarks:
        px = int(w * 0.35)
        pygame.draw.polygon(s, (112, 82, 150), [(px - 120, hz), (px + 120, hz), (px + 50, hz - 270), (px - 50, hz - 270)])
        for i in range(-110, 111, 28):
            pygame.draw.line(s, (150, 118, 185), (px + i, hz), (px + i * 0.42, hz - 270), 2)
        for gy in range(hz - 270, hz, 36):
            half = 120 - 70 * (hz - gy) / 270
            pygame.draw.line(s, (150, 118, 185), (px - half, gy), (px + half, gy), 1)
    if "cathedrale" in landmarks:
        cx = int(w * 0.62)
        pygame.draw.rect(s, (128, 96, 165), (cx - 18, hz - 400, 36, 400))
        pygame.draw.rect(s, (128, 96, 165), (cx - 60, hz - 330, 120, 30))
        pygame.draw.polygon(s, (150, 118, 185), [(cx - 18, hz - 400), (cx + 18, hz - 400), (cx, hz - 450)])
    if "ivoire" in landmarks:                      # tour de l'hôtel Ivoire
        cx = int(w * 0.62)
        pygame.draw.rect(s, (96, 150, 200), (cx - 26, hz - 420, 52, 420))
        pygame.draw.ellipse(s, (130, 185, 230), (cx - 46, hz - 440, 92, 26))
        for yy in range(hz - 400, hz, 22):
            pygame.draw.line(s, (170, 215, 250), (cx - 26, yy), (cx + 26, yy), 1)
    if "pont" in landmarks:
        _bridge(s, w, hz, int(w * 0.1), int(w * 0.3), int(w * 0.5))
    if "voiles" in landmarks:                      # voiliers sur la lagune
        for bx in (int(w * 0.55), int(w * 0.78), int(w * 0.9)):
            pygame.draw.polygon(s, (250, 250, 250), [(bx, hz + 20), (bx, hz - 30), (bx + 22, hz + 20)])
            pygame.draw.polygon(s, (255, 190, 120), [(bx - 4, hz + 20), (bx - 4, hz - 10), (bx - 16, hz + 20)])
            pygame.draw.rect(s, (60, 50, 70), (bx - 18, hz + 20, 44, 6))
    return s.convert_alpha()


def far_abobo():
    s, w = _layer(0.12)
    rng = random.Random(31)
    hz = 900
    cols = [(110, 55, 110), (150, 75, 100), (185, 98, 80)]
    for li, col in enumerate(cols):
        base = hz - 90 + li * 40
        pts = [(0, hz + 40)]
        for x in range(0, w + 40, 40):
            pts.append((x, base - 50 - math.sin(x * 0.007 + li * 2) * 45 - math.sin(x * 0.019 + li) * 18))
        pts.append((w + 40, hz + 40))
        pygame.draw.polygon(s, col, pts)
        for x in range(10, w, 26):               # petites maisons colorées sur les collines
            hy = base - 50 - math.sin(x * 0.007 + li * 2) * 45 - math.sin(x * 0.019 + li) * 18
            hc = rng.choice(((240, 200, 120), (220, 120, 90), (130, 180, 210), (170, 210, 140)))
            pygame.draw.rect(s, tuple(int(c * (0.6 + li * 0.15)) for c in hc), (x, hy + 4, 18, 12))
            pygame.draw.rect(s, (90, 80, 95), (x - 2, hy, 22, 5))
    mx = int(w * 0.4)                             # mosquée et minaret
    pygame.draw.rect(s, (225, 205, 175), (mx - 70, hz - 120, 140, 120))
    pygame.draw.ellipse(s, (60, 140, 110), (mx - 45, hz - 190, 90, 130))
    pygame.draw.rect(s, (225, 205, 175), (mx + 80, hz - 330, 26, 330))
    pygame.draw.polygon(s, (60, 140, 110), [(mx + 76, hz - 330), (mx + 110, hz - 330), (mx + 93, hz - 380)])
    pygame.draw.circle(s, (250, 220, 120), (mx + 93, hz - 385), 5)
    wx = int(w * 0.75)                            # château d'eau
    pygame.draw.rect(s, (150, 120, 130), (wx - 6, hz - 230, 12, 230))
    pygame.draw.ellipse(s, (170, 140, 150), (wx - 45, hz - 290, 90, 80))
    pygame.draw.rect(s, (125, 70, 105), (0, hz + 20, w, WORLD_H))
    return s.convert_alpha()


def _plane_silhouette(s, x, y, size, col, nose_right=True):
    d = 1 if nose_right else -1
    pygame.draw.ellipse(s, col, (x - size, y - size // 8, size * 2, size // 4))
    pygame.draw.polygon(s, col, [(x - d * size // 4, y), (x + d * size // 6, y), (x - d * size // 2, y + size // 2), (x - d * size // 1.5, y + size // 2)])
    pygame.draw.polygon(s, col, [(x - d * size * 0.85, y), (x - d * size * 0.7, y), (x - d * size * 0.95, y - size // 3)])


def far_aeroport():
    s, w = _layer(0.12)
    rng = random.Random(47)
    hz = 900
    pygame.draw.rect(s, (36, 50, 120), (0, hz, w, WORLD_H - hz))      # océan
    for ry in range(hz + 4, hz + 50, 8):
        for rx in range(rng.randint(0, 40), w, 70):
            pygame.draw.line(s, (255, 170, 110), (rx, ry), (rx + 26, ry), 1)
    for bx in range(30, w, 190):                                       # hangars lointains
        pygame.draw.rect(s, (40, 40, 86), (bx, hz - 70, 120, 70))
        pygame.draw.polygon(s, (40, 40, 86), [(bx, hz - 70), (bx + 120, hz - 70), (bx + 60, hz - 100)])
    tx = int(w * 0.55)                                                 # tour de contrôle
    pygame.draw.rect(s, (60, 60, 110), (tx - 12, hz - 260, 24, 260))
    pygame.draw.polygon(s, (60, 60, 110), [(tx - 50, hz - 260), (tx + 50, hz - 260), (tx + 36, hz - 300), (tx - 36, hz - 300)])
    pygame.draw.rect(s, (255, 220, 120), (tx - 36, hz - 296, 72, 10))
    pygame.draw.line(s, (60, 60, 110), (tx, hz - 300), (tx, hz - 340), 3)
    pygame.draw.circle(s, (255, 70, 70), (tx, hz - 342), 4)
    _plane_silhouette(s, int(w * 0.2), 560, 70, (50, 45, 100))         # avions dans le ciel
    _plane_silhouette(s, int(w * 0.78), 470, 46, (70, 60, 110), nose_right=False)
    for lx in range(0, w, 30):                                         # balises de piste
        pygame.draw.circle(s, (255, 255, 255), (lx, hz - 4), 2)
    return s.convert_alpha()


# ===========================================================================
#  COUCHES MÉDIANES (parallaxe 0.38)
# ===========================================================================
def _poles(s, w, gy, step=420):
    poles = list(range(120, w, step))
    for px in poles:
        pygame.draw.line(s, (50, 40, 40), (px, gy), (px, gy - 190), 5)
        pygame.draw.line(s, (50, 40, 40), (px - 22, gy - 180), (px + 22, gy - 180), 4)
    for a, b in zip(poles, poles[1:]):
        for dy in (-180, -170):
            pts = [(a + (b - a) * t / 12, gy + dy + math.sin(math.pi * t / 12) * 18) for t in range(13)]
            pygame.draw.lines(s, (40, 35, 40), False, pts, 1)


def _billboards(s, w, gy, items):
    for bx, txt, col in items:
        if bx < w - 200:
            pygame.draw.rect(s, (60, 50, 50), (bx + 20, gy - 110, 8, 110))
            pygame.draw.rect(s, (60, 50, 50), (bx + 150, gy - 110, 8, 110))
            pygame.draw.rect(s, col, (bx, gy - 200, 180, 80), border_radius=6)
            pygame.draw.rect(s, INK, (bx, gy - 200, 180, 80), 4, border_radius=6)
            blit_center_text(s, txt, 26, WHITE, (bx + 90, gy - 160))


FACADES = [((236, 214, 150), (246, 236, 206), (44, 112, 92)), ((226, 160, 118), (244, 220, 180), (40, 90, 130)),
           ((150, 200, 214), (226, 240, 244), (200, 90, 60)), ((232, 196, 120), (250, 240, 214), (150, 56, 56))]
SHOPS = ["PHARMACIE", "MAQUIS", "BOUTIQUE", "COIFFURE", "MOBILE MONEY", "CAFÉ", "QUINCAILLERIE", "BAR DU COIN"]
LAUNDRY = [(230, 80, 80), (80, 160, 230), (250, 220, 90), (255, 255, 255), (60, 170, 110)]


def mid_town(seed, walls, tint, hmin, hmax, gbakas, boards, palm_step=330, gap=(-14, 16)):
    """Quartier populaire (Yopougon, Abobo) : maisons à toit de tôle + grands immeubles à arcades."""
    s, w = _layer(0.38)
    rng = random.Random(seed)
    gy = 930
    pygame.draw.rect(s, (60, 48, 70), (0, gy, w, WORLD_H - gy))
    for px in range(60, w, palm_step):
        _palm(s, px + rng.randint(-40, 40), gy, rng.randint(150, 220), rng)
    x, n = -30, 0
    while x < w:
        n += 1
        if n % 4 == 0:                                       # grand immeuble colonial
            pl, tr, sh = rng.choice(FACADES)
            fw, fh = rng.randint(300, 400), rng.randint(250, 330)
            grand_facade(s, x, gy, fw, fh, pl, tr, sh, rng, floors=3, label=rng.choice(SHOPS),
                         font=font(16), laundry=LAUNDRY)
            x += fw + rng.randint(6, 24)
            continue
        hw, hh = rng.randint(90, 160), rng.randint(hmin, hmax)
        col = rng.choice(walls)
        ink_rect(s, (x, gy - hh, hw, hh), col, 3)
        pygame.draw.rect(s, (146, 146, 158), (x - 6, gy - hh - 10, hw + 12, 12))
        for lx in range(x - 6, x + hw + 6, 5):
            pygame.draw.line(s, (108, 108, 120), (lx, gy - hh - 10), (lx, gy - hh + 1), 1)
        pygame.draw.rect(s, INK, (x - 6, gy - hh - 10, hw + 12, 12), 2)
        for wy in range(gy - hh + 22, gy - 60, 46):
            for wx in range(x + 12, x + hw - 28, 38):
                lit = rng.random() < 0.5
                pygame.draw.rect(s, (255, 215, 110) if lit else (50, 55, 80), (wx, wy, 22, 24))
                pygame.draw.rect(s, INK, (wx, wy, 22, 24), 2)
        pygame.draw.rect(s, (84, 58, 42), (x + hw - 28, gy - 46, 18, 46))
        pygame.draw.rect(s, INK, (x + hw - 28, gy - 46, 18, 46), 2)
        if rng.random() < 0.3:
            pygame.draw.circle(s, (225, 225, 230), (x + hw // 2, gy - hh - 22), 10)
            pygame.draw.circle(s, INK, (x + hw // 2, gy - hh - 22), 10, 2)
            pygame.draw.line(s, INK, (x + hw // 2, gy - hh - 22), (x + hw // 2, gy - hh - 10), 2)
        if rng.random() < 0.25:                               # linge qui sèche
            ly = gy - hh // 2
            pygame.draw.line(s, INK, (x, ly), (x + hw, ly), 1)
            for lx in range(x + 8, x + hw - 8, 18):
                c = rng.choice(LAUNDRY)
                pygame.draw.rect(s, c, (lx, ly, 10, 16))
                pygame.draw.rect(s, INK, (lx, ly, 10, 16), 1)
        x += hw + rng.randint(*gap)
    _poles(s, w, gy)
    for gx, lab, col, flip in gbakas:
        if gx < w:
            draw_gbaka(s, gx, gy - 55, 150, lab, col, flip)
    _billboards(s, w, gy, boards)
    s.fill(tint, special_flags=pygame.BLEND_RGB_SUB)
    return s.convert_alpha()


def mid_cocody():
    s, w = _layer(0.38)
    rng = random.Random(61)
    gy = 930
    pygame.draw.rect(s, (70, 110, 90), (0, gy, w, WORLD_H - gy))
    for px in range(40, w, 300):
        _palm(s, px + rng.randint(-30, 30), gy, rng.randint(170, 240), rng)
    x = -20
    while x < w:                                   # villas modernes à toit plat
        vw, vh = rng.randint(130, 220), rng.randint(90, 190)
        col = rng.choice(((245, 240, 230), (235, 225, 205), (215, 225, 235), (250, 235, 215)))
        ink_rect(s, (x, gy - vh, vw, vh), col, 3)
        pygame.draw.rect(s, (90, 90, 105), (x - 5, gy - vh - 6, vw + 10, 8))
        pygame.draw.rect(s, INK, (x - 5, gy - vh - 6, vw + 10, 8), 2)
        for fy in range(gy - vh + 18, gy - 30, 44):
            for fx in range(x + 14, x + vw - 34, 46):
                pygame.draw.rect(s, (70, 120, 170), (fx, fy, 30, 28))
                pygame.draw.rect(s, INK, (fx, fy, 30, 28), 2)
                pygame.draw.rect(s, (235, 235, 240), (fx - 4, fy + 24, 38, 4))
        pygame.draw.rect(s, (110, 80, 60), (x + vw // 2 - 12, gy - 50, 24, 50))
        pygame.draw.rect(s, (40, 110, 60), (x - 6, gy - 22, vw + 12, 22), border_radius=10)   # haie
        x += vw + rng.randint(10, 60)
    for lx in range(200, w, 360):                  # lampadaires
        pygame.draw.line(s, (70, 70, 85), (lx, gy), (lx, gy - 150), 4)
        pygame.draw.line(s, (70, 70, 85), (lx, gy - 150), (lx + 30, gy - 150), 4)
        pygame.draw.circle(s, (255, 240, 170), (lx + 32, gy - 146), 7)
    for gx, lab, col, flip in ((260, "WORO-WORO", (240, 120, 30), False), (1100, "COCODY", (60, 120, 220), True),
                               (1800, "DEUX-PLATEAUX", (30, 150, 100), False)):
        if gx < w:
            draw_gbaka(s, gx, gy - 55, 150, lab, col, flip)
    _billboards(s, w, gy, ((620, "RIVIERA GOLF", (30, 120, 90)), (1450, "BABI CITY", (200, 60, 120))))
    s.fill((30, 50, 30), special_flags=pygame.BLEND_RGB_SUB)
    return s.convert_alpha()


def mid_aeroport():
    s, w = _layer(0.38)
    rng = random.Random(73)
    gy = 930
    pygame.draw.rect(s, (46, 48, 62), (0, gy, w, WORLD_H - gy))
    x = 40                                         # terminal
    ink_rect(s, (x, gy - 130, 760, 130), (150, 160, 185), 3)
    pygame.draw.rect(s, (110, 120, 150), (x - 10, gy - 140, 780, 16))
    pygame.draw.rect(s, INK, (x - 10, gy - 140, 780, 16), 3)
    for wx in range(x + 14, x + 740, 40):
        pygame.draw.rect(s, (255, 225, 140) if rng.random() < 0.6 else (60, 90, 140), (wx, gy - 100, 28, 60))
    blit_center_text(s, "AÉROPORT FÉLIX HOUPHOUËT-BOIGNY", 28, (240, 240, 250), (x + 380, gy - 118))
    for px in range(900, w, 520):                  # avions parqués (tail fins)
        pygame.draw.polygon(s, (240, 240, 245), [(px, gy), (px + 30, gy), (px + 20, gy - 110), (px - 6, gy - 110)])
        pygame.draw.polygon(s, ORANGE, [(px, gy - 70), (px + 28, gy - 70), (px + 22, gy - 108), (px - 4, gy - 108)])
        pygame.draw.ellipse(s, (235, 235, 240), (px - 200, gy - 52, 260, 40))
        pygame.draw.rect(s, ORANGE, (px - 180, gy - 28, 220, 6))
    for lx in range(0, w, 40):                     # balises bleues de piste
        pygame.draw.circle(s, (90, 150, 255), (lx, gy - 6), 3)
    for fx in range(0, w, 24):                     # clôture
        pygame.draw.line(s, (90, 95, 110), (fx, gy - 50), (fx, gy), 1)
    pygame.draw.line(s, (90, 95, 110), (0, gy - 50), (w, gy - 50), 2)
    for cx in range(300, w, 700):                  # camions de bagages
        pygame.draw.rect(s, (240, 190, 50), (cx, gy - 40, 70, 28))
        pygame.draw.rect(s, (70, 90, 130), (cx + 50, gy - 38, 18, 16))
        for wx in (cx + 14, cx + 56):
            pygame.draw.circle(s, (20, 20, 25), (wx, gy - 10), 8)
    s.fill((25, 30, 20), special_flags=pygame.BLEND_RGB_SUB)
    return s.convert_alpha()


# ===========================================================================
#  Fabrique : retourne la liste [(facteur, surface)] pour une arène
# ===========================================================================
YOP_WALLS = [(233, 196, 106), (205, 98, 76), (116, 170, 200), (150, 200, 120), (230, 150, 90)]
ABOBO_WALLS = [(220, 120, 80), (200, 80, 90), (240, 190, 90), (110, 150, 190), (180, 130, 190), (150, 190, 110)]


def build_layers(far_key, mid_key):
    if far_key == "plateau":
        far = far_city(11, ((88, 112), (60, 80), (125, 150)), ("pyramide", "cathedrale", "pont"),
                       (74, 58, 128), (255, 205, 110))
    elif far_key == "cocody":
        far = far_city(17, ((60, 95), (110, 150), (160, 200)), ("pont", "ivoire", "voiles"),
                       (50, 120, 185), (215, 240, 255))
    elif far_key == "abobo":
        far = far_abobo()
    else:
        far = far_aeroport()

    if mid_key == "yop":
        mid = mid_town(23, YOP_WALLS, (50, 88, 50), 70, 150,
                       ((150, "YOPOUGON", ORANGE, False), (880, "ADJAMÉ", GREEN, True),
                        (1500, "COCODY", (60, 120, 220), False), (2000, "PLATEAU", (220, 60, 60), True)),
                       ((330, "BABI VIBE", (200, 60, 120)), (1150, "ALLOCO & POISSON", (230, 150, 30)),
                        (1850, "225 FOREVER", (30, 140, 90))))
    elif mid_key == "abobo":
        mid = mid_town(37, ABOBO_WALLS, (60, 95, 60), 110, 230,
                       ((100, "ABOBO-GARE", (220, 60, 60), False), (700, "ADJAMÉ", GREEN, True),
                        (1300, "YOPOUGON", ORANGE, False), (1900, "ANYAMA", (60, 120, 220), True)),
                       ((420, "MARCHÉ GOUTO", (180, 90, 40)), (1250, "ABOBO LA BONNE", (60, 140, 100)),
                        (1900, "BRAISÉ CHEZ ZIZI", (200, 50, 50))), palm_step=420, gap=(-30, 4))
    elif mid_key == "cocody":
        mid = mid_cocody()
    else:
        mid = mid_aeroport()
    return [(0.12, far), (0.38, mid)]
