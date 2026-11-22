"""Babizone - boîte à outils « bande dessinée » pour les décors :
contours noirs, ombrage à 2 tons, parpaings, façades à arcades, fer forgé, fers à béton...
"""
import math
import random
import pygame

INK = (28, 20, 24)


def shade(c, f=0.78):
    return tuple(max(0, min(255, int(v * f))) for v in c[:3])


def light(c, f=1.18):
    return tuple(max(0, min(255, int(v * f))) for v in c[:3])


def ink_rect(s, rect, fill, w=3, shadow=0.78, lip=True):
    """Rectangle rempli + bande d'ombre en bas + reflet en haut + contour noir."""
    x, y, ww, hh = [int(v) for v in rect]
    pygame.draw.rect(s, fill, (x, y, ww, hh))
    if hh > 8:
        pygame.draw.rect(s, shade(fill, shadow), (x, y + hh - max(3, hh // 4), ww, max(3, hh // 4)))
        if lip:
            pygame.draw.rect(s, light(fill), (x, y, ww, 2))
    pygame.draw.rect(s, INK, (x, y, ww, hh), w)


def parpaing(s, rect, base, mortar=None, bw=26, bh=13, rng=None):
    """Mur en parpaings (blocs de béton) : briques décalées avec quelques blocs plus sombres."""
    x, y, w, h = [int(v) for v in rect]
    rng = rng or random.Random(x * 7 + y)
    mortar = mortar or shade(base, 0.62)
    pygame.draw.rect(s, base, (x, y, w, h))
    for row, yy in enumerate(range(y, y + h, bh)):
        pygame.draw.line(s, mortar, (x, yy), (x + w - 1, yy), 1)
        off = (bw // 2) if row % 2 else 0
        for xx in range(x - off, x + w, bw):
            if x <= xx < x + w:
                pygame.draw.line(s, mortar, (xx, yy), (xx, min(yy + bh, y + h - 1)), 1)
            if rng.random() < 0.18:
                bx0, bx1 = max(x, xx + 1), min(x + w, xx + bw)
                bh2 = min(bh - 1, y + h - yy - 1)
                if bx1 > bx0 and bh2 > 0:
                    pygame.draw.rect(s, shade(base, 0.9), (bx0, yy + 1, bx1 - bx0, bh2))


def plaster_wall(s, rect, plaster, rng, w=3):
    """Mur enduit avec plaques arrachées laissant voir les parpaings (comme la référence)."""
    x, y, ww, hh = [int(v) for v in rect]
    block = (150, 150, 158)
    parpaing(s, (x, y, ww, hh), block, rng=rng)
    pygame.draw.rect(s, plaster, (x, y, ww, hh))
    for _ in range(max(2, ww // 70)):          # plaques de parpaing apparentes
        px, py = rng.randint(x + 6, x + max(8, ww - 50)), rng.randint(y + 20, y + max(24, hh - 60))
        pw, ph = rng.randint(24, 50), rng.randint(20, 46)
        pts = [(px, py + rng.randint(0, 6)), (px + pw * .5, py - rng.randint(0, 6)), (px + pw, py + rng.randint(0, 6)),
               (px + pw + rng.randint(-5, 5), py + ph), (px + pw * .4, py + ph + rng.randint(0, 6)), (px - 3, py + ph * .6)]
        pygame.draw.polygon(s, block, pts)
        parpaing(s, (int(px), int(py + 6), int(pw - 6), int(ph - 8)), block, rng=rng)
        pygame.draw.polygon(s, INK, pts, 2)
    pygame.draw.rect(s, shade(plaster, 0.84), (x, y + hh - 10, ww, 10))
    pygame.draw.rect(s, shade(plaster, 0.84), (x + ww - 8, y, 8, hh))
    pygame.draw.rect(s, INK, (x, y, ww, hh), w)


def arch_window(s, x, y, w, h, glass=(142, 182, 212), shutter=None, lit=False):
    """Fenêtre à arcade avec croisillons et volets (style colonial)."""
    gl = (255, 220, 130) if lit else glass
    r = w // 2
    pygame.draw.rect(s, gl, (x, y + r, w, h - r))
    pygame.draw.circle(s, gl, (x + r, y + r), r)
    pygame.draw.circle(s, INK, (x + r, y + r), r, 2)
    pygame.draw.line(s, INK, (x, y + r), (x, y + h), 2)
    pygame.draw.line(s, INK, (x + w - 1, y + r), (x + w - 1, y + h), 2)
    pygame.draw.line(s, INK, (x, y + h), (x + w, y + h), 3)
    pygame.draw.line(s, INK, (x + r, y), (x + r, y + h), 2)
    pygame.draw.line(s, INK, (x, y + r + (h - r) // 2), (x + w, y + r + (h - r) // 2), 2)
    pygame.draw.line(s, (255, 255, 255), (x + 3, y + r + 4), (x + 3, y + r + 14), 2)
    if shutter:
        for sx in (x - w // 2 - 2, x + w + 2):
            pygame.draw.rect(s, shutter, (sx, y + 2, w // 2, h - 2))
            for ly in range(y + 6, y + h - 2, 5):
                pygame.draw.line(s, shade(shutter, 0.7), (sx, ly), (sx + w // 2 - 1, ly), 1)
            pygame.draw.rect(s, INK, (sx, y + 2, w // 2, h - 2), 2)


def balcony(s, x0, x1, y, h=24, laundry=None):
    """Balcon en fer forgé : dalle, garde-corps à barreaux et motifs en volutes."""
    pygame.draw.rect(s, (190, 186, 176), (x0 - 6, y, x1 - x0 + 12, 7))
    pygame.draw.rect(s, INK, (x0 - 6, y, x1 - x0 + 12, 7), 2)
    pygame.draw.line(s, INK, (x0, y - h), (x1, y - h), 3)
    for bx in range(int(x0) + 4, int(x1), 9):
        pygame.draw.line(s, INK, (bx, y), (bx, y - h), 2)
    for bx in range(int(x0) + 10, int(x1) - 6, 27):
        pygame.draw.circle(s, INK, (bx, y - h // 2), 5, 2)
    if laundry:
        rng = random.Random(int(x0))
        pygame.draw.line(s, INK, (x0 + 4, y - h - 14), (x1 - 4, y - h - 14), 1)
        for lx in range(int(x0) + 10, int(x1) - 14, 20):
            c = rng.choice(laundry)
            pygame.draw.rect(s, c, (lx, y - h - 14, 13, 22))
            pygame.draw.rect(s, INK, (lx, y - h - 14, 13, 22), 1)
            pygame.draw.line(s, light(c), (lx + 3, y - h - 12), (lx + 3, y - h + 5), 1)


def rebar(s, x, y, n, rng, length=34):
    """Fers à béton qui dépassent d'un poteau : le détail des chantiers d'Abidjan."""
    for i in range(n):
        bx = x + i * 6
        top = y - rng.randint(length // 2, length)
        pygame.draw.line(s, (92, 66, 54), (bx, y), (bx + rng.randint(-3, 3), top), 3)
        pygame.draw.line(s, (150, 98, 70), (bx, y), (bx, top + 4), 1)


def rubble(s, x, y, w, rng, col=(150, 148, 154)):
    """Tas de gravats au sol."""
    for _ in range(max(3, w // 12)):
        rx = x + rng.randint(0, w)
        rw, rh = rng.randint(8, 22), rng.randint(6, 14)
        pts = [(rx, y), (rx + rw * .3, y - rh), (rx + rw * .8, y - rh * .8), (rx + rw, y)]
        c = shade(col, rng.uniform(.8, 1.1))
        pygame.draw.polygon(s, c, pts)
        pygame.draw.polygon(s, INK, pts, 2)


def sign(s, rect, text, font, bg, fg=(255, 255, 255), w=3):
    x, y, ww, hh = [int(v) for v in rect]
    pygame.draw.rect(s, bg, (x, y, ww, hh), border_radius=4)
    pygame.draw.rect(s, shade(bg, 0.7), (x, y + hh - 5, ww, 5))
    pygame.draw.rect(s, INK, (x, y, ww, hh), w, border_radius=4)
    img = font.render(text, True, fg)
    s.blit(img, img.get_rect(center=(x + ww // 2, y + hh // 2 - 1)))


def grand_facade(s, x, base_y, w, h, plaster, trim, shutter, rng, floors=3, label=None, font=None, laundry=None):
    """Grand immeuble colonial / moderne : arcades, corniches, balcons, volets, enseigne."""
    top = base_y - h
    plaster_wall(s, (x, top, w, h), plaster, rng)
    pygame.draw.rect(s, trim, (x - 6, top - 12, w + 12, 14))                    # corniche
    pygame.draw.rect(s, INK, (x - 6, top - 12, w + 12, 14), 3)
    for k in range(0, w, 14):
        pygame.draw.rect(s, shade(trim, 0.8), (x - 4 + k, top - 4, 8, 6))
    fh = (h - 30) // floors
    ww = 28
    cols = max(2, (w - 20) // 70)
    for fl in range(floors):
        fy = top + 18 + fl * fh
        for c in range(cols):
            wx = x + 18 + c * ((w - 36 - ww) // max(1, cols - 1)) if cols > 1 else x + w // 2 - ww // 2
            wy = fy + 4
            wh = fh - 34 if fl < floors - 1 else fh - 22
            arch_window(s, int(wx), int(wy), ww, max(40, int(wh)), shutter=shutter if fl > 0 else None, lit=rng.random() < 0.25)
        if fl > 0 and fl < floors:
            balcony(s, x + 8, x + w - 8, fy + fh - 12, laundry=laundry if rng.random() < 0.7 else None)
    pygame.draw.rect(s, trim, (x, base_y - 22, w, 22))                           # soubassement
    pygame.draw.rect(s, INK, (x, base_y - 22, w, 22), 3)
    if label and font:
        sign(s, (x + w // 2 - 70, base_y - 64, 140, 30), label, font, shutter)
    pygame.draw.rect(s, (60, 42, 34), (x + 10, base_y - 74, 24, 52), border_radius=10)   # porte
    pygame.draw.rect(s, INK, (x + 10, base_y - 74, 24, 52), 2, border_radius=10)
