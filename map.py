"""Babizone - carte : plateformes, décors, bonus (Garba, Alloco...). Gère les 4 arènes."""
import math
import random
import pygame
from settings import *
from arenas import ARENAS
from scenery import font, blit_center_text, draw_gbaka, build_layers
from artkit import INK, shade, light, ink_rect, parpaing, plaster_wall, arch_window, balcony, rebar, rubble


class Platform:
    def __init__(self, x, y, w, h, kind):
        self.rect = pygame.Rect(x, y, w, h)
        self.kind = kind


# ---------------------------------------------------------------------------
#  Bonus thématiques
# ---------------------------------------------------------------------------
PICKUP_KINDS = {
    "garba": "Garba : +50 santé",
    "alloco": "Alloco : +25 santé, jet-pack rechargé en partie",
    "gnamankoudji": "Gnamankoudji : vitesse x1.5 pendant 8 s",
    "caisse": "Caisse d'armes : nouvelle arme + munitions",
}


class Pickup:
    SIZE = 28

    def __init__(self, kind, center):
        self.kind = kind
        self.rect = pygame.Rect(0, 0, self.SIZE, self.SIZE)
        self.rect.center = center
        self.t = random.uniform(0, 6)
        self.dead = False

    def update(self, dt):
        self.t += dt

    def draw(self, surf, ox, oy):
        bob = math.sin(self.t * 3) * 3
        cx = self.rect.centerx - ox
        cy = self.rect.centery - oy + bob
        ring = {"garba": ORANGE, "alloco": (240, 200, 40),
                "gnamankoudji": (255, 120, 60), "caisse": (120, 220, 255)}[self.kind]
        pulse = 18 + math.sin(self.t * 5) * 2
        pygame.draw.circle(surf, ring, (int(cx), int(cy)), int(pulse), 2)

        if self.kind == "garba":
            pygame.draw.ellipse(surf, (240, 240, 240), (cx - 14, cy + 2, 28, 10))
            pygame.draw.ellipse(surf, (246, 236, 190), (cx - 11, cy - 6, 22, 13))
            pygame.draw.ellipse(surf, (200, 105, 40), (cx - 9, cy - 9, 18, 8))
            pygame.draw.circle(surf, (30, 20, 10), (int(cx + 5), int(cy - 6)), 1)
            pygame.draw.circle(surf, (220, 40, 40), (int(cx - 9), int(cy + 1)), 4)
        elif self.kind == "alloco":
            pygame.draw.polygon(surf, (205, 170, 115),
                                [(cx - 11, cy + 11), (cx + 11, cy + 11), (cx + 8, cy - 2), (cx - 8, cy - 2)])
            for i in range(4):
                pygame.draw.ellipse(surf, (240, 170, 30), (cx - 12 + i * 6, cy - 11 + (i % 2) * 3, 10, 7))
                pygame.draw.ellipse(surf, (150, 80, 20), (cx - 12 + i * 6, cy - 11 + (i % 2) * 3, 10, 7), 1)
            pygame.draw.circle(surf, (210, 30, 30), (int(cx + 6), int(cy + 4)), 3)
        elif self.kind == "gnamankoudji":
            pygame.draw.rect(surf, (214, 140, 30), (cx - 7, cy - 4, 14, 18), border_radius=3)
            pygame.draw.rect(surf, (214, 140, 30), (cx - 3, cy - 11, 6, 8))
            pygame.draw.rect(surf, (200, 40, 40), (cx - 4, cy - 14, 8, 4))
            pygame.draw.rect(surf, (255, 240, 200), (cx - 5, cy + 1, 10, 7))
            blit_center_text(surf, "G", 14, (120, 60, 10), (cx, cy + 5))
        else:
            pygame.draw.rect(surf, (150, 105, 60), (cx - 13, cy - 11, 26, 22))
            pygame.draw.rect(surf, (90, 60, 30), (cx - 13, cy - 11, 26, 22), 2)
            pygame.draw.line(surf, (90, 60, 30), (cx - 13, cy - 11), (cx + 13, cy + 11), 2)
            pygame.draw.line(surf, (90, 60, 30), (cx + 13, cy - 11), (cx - 13, cy + 11), 2)
            pygame.draw.rect(surf, ORANGE, (cx - 13, cy - 2, 26, 4))


# ---------------------------------------------------------------------------
#  La carte
# ---------------------------------------------------------------------------
class GameMap:
    def __init__(self, key="yop"):
        self.key = key
        self.cfg = ARENAS[key]
        self.platforms = [Platform(*d) for d in self.cfg["platforms"]]
        self.solids = [p.rect for p in self.platforms]
        self.spawn_points = list(self.cfg["spawns"])
        self.pickup_points = list(self.cfg["pickups"])
        self.look = self.cfg["look"]
        self._sky_cache = {}
        self.fg = self._build_foreground()
        self.layers = build_layers(self.cfg["far"], self.cfg["mid"])

    # ----- utilitaires de jeu ------------------------------------------------
    def line_clear(self, a, b):
        """Vrai si aucun mur entre les points a et b (pour l'IA)."""
        dx, dy = b[0] - a[0], b[1] - a[1]
        n = int(math.hypot(dx, dy) // 12) + 1
        for i in range(1, n):
            x = a[0] + dx * i / n
            y = a[1] + dy * i / n
            for r in self.solids:
                if r.collidepoint(x, y):
                    return False
        return True

    # ----- rendu -------------------------------------------------------------
    def get_sky(self, w, h):
        key = (w, h)
        if key in self._sky_cache:
            return self._sky_cache[key]
        s = pygame.Surface((w, h))
        top, bottom = self.cfg["sky"]
        for y in range(h):
            t = y / (h - 1)
            t = t * t * 0.4 + t * 0.6
            pygame.draw.line(s, [int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)], (0, y), (w, y))
        fx, fy, scol = self.cfg["sun"]
        halo = pygame.Surface((w, h), pygame.SRCALPHA)
        sx, sy = int(w * fx), int(h * fy)
        for r, a in ((190, 25), (130, 40), (90, 60)):
            pygame.draw.circle(halo, (*scol, a), (sx, sy), r)
        s.blit(halo, (0, 0))
        pygame.draw.circle(s, scol, (sx, sy), 62)
        rng = random.Random(5)
        for _ in range(7):
            cx, cy = rng.randint(0, w), rng.randint(30, int(h * 0.45))
            cl = pygame.Surface((220, 50), pygame.SRCALPHA)
            for k in range(4):
                pygame.draw.ellipse(cl, (255, 200, 170, 60), (k * 40, rng.randint(8, 16), 90, 28))
            s.blit(cl, (cx, cy))
        self._sky_cache[key] = s
        return s

    def draw_background(self, surf, cam_x, cam_y):
        vw, vh = surf.get_size()
        surf.blit(self.get_sky(vw, vh), (0, 0))
        for f, layer in self.layers:
            surf.blit(layer, (-int(cam_x * f), -int(cam_y)))

    def draw_foreground(self, surf, cam_x, cam_y):
        vw, vh = surf.get_size()
        surf.blit(self.fg, (0, 0), pygame.Rect(int(cam_x), int(cam_y), vw, vh))

    # ----- premier plan --------------------------------------------------------
    def _support_bottom(self, x, y):
        best = GROUND_Y
        for q in self.platforms:
            r = q.rect
            if q.kind in ("route", "pilier", "tour") or not (r.left <= x <= r.right):
                continue
            if r.top >= y + 4:
                best = min(best, r.top)
        return best

    def _build_foreground(self):
        s = pygame.Surface((WORLD_W, WORLD_H), pygame.SRCALPHA)
        pole_style = {"toit_tole": ((110, 75, 45), 6), "beton": ((150, 150, 162), 9),
                      "hangar": ((100, 105, 125), 6)}
        for p in self.platforms:
            r = p.rect
            if p.kind in pole_style:
                col, pw = pole_style[p.kind]
                for x in (r.left + 12, r.right - 12):
                    pygame.draw.rect(s, col, (x - pw // 2, r.bottom, pw, self._support_bottom(x, r.top) - r.bottom))
            elif p.kind == "echafaudage":
                for x0 in (r.left + 12, r.right - 42):
                    bot = self._support_bottom(x0 + 15, r.top)
                    pygame.draw.rect(s, (140, 140, 152), (x0, r.bottom, 4, bot - r.bottom))
                    pygame.draw.rect(s, (140, 140, 152), (x0 + 26, r.bottom, 4, bot - r.bottom))
                    for yy in range(r.bottom, bot - 40, 40):
                        pygame.draw.line(s, (120, 120, 132), (x0, yy), (x0 + 30, yy + 40), 2)
                        pygame.draw.line(s, (120, 120, 132), (x0 + 30, yy), (x0, yy + 40), 2)
            elif p.kind == "avion":
                self._avion_gear(s, r)

        for i, d in enumerate(self.cfg["decor"]):
            self._back_wall(s, d[1], d[2], d[3], i)
        for i, d in enumerate(self.cfg["decor"]):
            rr = random.Random(77 + i)
            rubble(s, d[1] - 24, GROUND_Y, 56, rr)
            rubble(s, d[2] - 20, GROUND_Y, 50, rr)
            if d[0] == "maquis":
                self._draw_maquis(s, d[1], d[2], d[3], d[4])
            else:
                self._draw_stand(s, d[1], d[2], d[3], d[4], d[5])

        for i, p in enumerate(self.platforms):
            getattr(self, "_draw_" + p.kind)(s, p, i)
        for i, p in enumerate(self.platforms):          # accessoires de toit (fers à béton, réservoirs)
            self._roof_props(s, p, i)
        return s.convert_alpha()

    # ----- plateformes (style bande dessinée : contours noirs + 2 tons) -----------------
    def _draw_route(self, s, p, i):
        r = p.rect
        rng = random.Random(5)
        pygame.draw.rect(s, (62, 58, 70), r)                                   # bitume
        pygame.draw.rect(s, (46, 42, 54), (r.x, r.y + 52, r.w, r.h - 52))
        pygame.draw.rect(s, (170, 96, 56), (r.x, r.y, r.w, 13))                # bord de latérite rouge
        pygame.draw.rect(s, (214, 130, 80), (r.x, r.y, r.w, 4))
        for x in range(0, r.w, 14):
            pygame.draw.circle(s, (140, 76, 46), (x + rng.randint(0, 8), r.y + rng.randint(5, 11)), 2)
        pygame.draw.line(s, INK, (r.x, r.y + 13), (r.right, r.y + 13), 3)
        pygame.draw.line(s, INK, (r.x, r.y), (r.right, r.y), 3)
        for x in range(30, r.w, 120):                                          # marquage au sol
            pygame.draw.rect(s, (240, 214, 90), (x, r.y + 36, 52, 6))
            pygame.draw.rect(s, INK, (x, r.y + 36, 52, 6), 1)
        for _ in range(26):                                                    # fissures et nids-de-poule
            cx = rng.randint(10, r.w - 40)
            cy = r.y + rng.randint(20, 90)
            pygame.draw.lines(s, (30, 26, 34), False, [(cx, cy), (cx + 9, cy + 4), (cx + 14, cy - 2), (cx + 24, cy + 3)], 2)
        for px in range(220, r.w, 520):
            pygame.draw.ellipse(s, (80, 104, 138), (px, r.y + 60, 64, 14))
            pygame.draw.ellipse(s, (130, 160, 195), (px + 8, r.y + 62, 24, 4))
            pygame.draw.ellipse(s, INK, (px, r.y + 60, 64, 14), 2)

    def _draw_toit_tole(self, s, p, i):
        r = p.rect
        pygame.draw.rect(s, (176, 104, 58), r)
        for x in range(r.left + 2, r.right, 7):
            pygame.draw.line(s, (132, 74, 42), (x, r.top), (x, r.bottom), 2)
            pygame.draw.line(s, (214, 140, 88), (x + 3, r.top), (x + 3, r.bottom - 3), 1)
        pygame.draw.rect(s, (230, 170, 112), (r.x, r.y, r.w, 3))
        pygame.draw.rect(s, (112, 62, 36), (r.x, r.bottom - 4, r.w, 4))
        for x in range(r.left + 10, r.right - 6, 38):                         # rivets
            pygame.draw.circle(s, (70, 40, 26), (x, r.centery), 2)
        pygame.draw.rect(s, INK, r, 3)

    def _draw_beton(self, s, p, i):
        r = p.rect
        ink_rect(s, r, (206, 206, 214), 3)
        pygame.draw.rect(s, (62, 138, 92), (r.x, r.y - 9, r.w, 9), border_radius=4)       # jardinière
        pygame.draw.rect(s, INK, (r.x, r.y - 9, r.w, 9), 2, border_radius=4)
        for x in range(r.x + 8, r.right - 8, 18):
            pygame.draw.circle(s, (96, 178, 112), (x, r.y - 11), 5)

    def _draw_hangar(self, s, p, i):
        r = p.rect
        pygame.draw.rect(s, (142, 152, 170), r)
        for x in range(r.left + 2, r.right, 8):
            pygame.draw.line(s, (108, 118, 138), (x, r.top), (x, r.bottom), 2)
        pygame.draw.rect(s, (62, 122, 212), (r.x, r.y, r.w, 5))
        pygame.draw.rect(s, INK, r, 3)

    def _draw_echafaudage(self, s, p, i):
        r = p.rect
        pygame.draw.rect(s, (126, 92, 60), r)
        for x in range(r.left + 4, r.right, 22):
            pygame.draw.line(s, (84, 58, 38), (x, r.top + 2), (x, r.bottom - 2), 2)
        pygame.draw.rect(s, (176, 134, 90), (r.x, r.y, r.w, 3))
        pygame.draw.rect(s, INK, r, 3)

    def _draw_pont(self, s, p, i):
        r = p.rect
        ink_rect(s, r, (126, 128, 142), 3)
        for x in range(r.left, r.right, 22):
            pygame.draw.line(s, INK, (x, r.y - 16), (x, r.y), 2)
        pygame.draw.line(s, INK, (r.x, r.y - 16), (r.right, r.y - 16), 3)
        pygame.draw.line(s, (232, 232, 238), (r.x, r.y - 14), (r.right, r.y - 14), 1)
        for x in (r.left + 60, r.centerx, r.right - 60):
            pygame.draw.line(s, INK, (x, r.y), (x, r.y - 62), 5)
            pygame.draw.line(s, (96, 98, 112), (x, r.y), (x, r.y - 62), 2)
            pygame.draw.circle(s, (255, 236, 160), (x, r.y - 64), 8)
            pygame.draw.circle(s, INK, (x, r.y - 64), 8, 2)

    def _draw_pilier(self, s, p, i):
        r = p.rect
        parpaing(s, r, (152, 152, 164), rng=random.Random(3))
        pygame.draw.rect(s, (112, 112, 126), (r.right - 8, r.y, 8, r.h))
        for k, col in enumerate((ORANGE, WHITE, GREEN)):                       # graff aux couleurs ivoiriennes
            pygame.draw.rect(s, col, (r.x, 760 + k * 12, r.w, 12))
            pygame.draw.rect(s, INK, (r.x, 760 + k * 12, r.w, 12), 1)
        blit_center_text(s, "225", 30, INK, (r.centerx, 730))
        pygame.draw.rect(s, INK, r, 3)

    def _draw_conteneur(self, s, p, i):
        r = p.rect
        col = [(204, 74, 52), (54, 116, 176), (64, 146, 96), (232, 174, 44)][i % 4]
        pygame.draw.rect(s, col, r)
        dark = shade(col, 0.7)
        for x in range(r.left + 6, r.right - 4, 9):
            pygame.draw.line(s, dark, (x, r.top + 5), (x, r.bottom - 5), 3)
            pygame.draw.line(s, light(col), (x + 2, r.top + 5), (x + 2, r.bottom - 5), 1)
        pygame.draw.rect(s, shade(col, 0.82), (r.x, r.bottom - 10, r.w, 10))
        pygame.draw.rect(s, INK, r, 3)
        pygame.draw.line(s, INK, (r.right - 14, r.top + 12), (r.right - 14, r.bottom - 12), 3)

    def _draw_gbaka(self, s, p, i):
        r = p.rect
        flip = (r.x > 1200)
        draw_gbaka(s, r.x, r.y, r.w, "YOP-ADJAMÉ" if not flip else "ABOBO-PLATEAU",
                   ORANGE if not flip else GREEN, flip)

    def _avion_gear(self, s, r):
        for gx in (r.x + 60, r.centerx + 30, r.right - 70):
            pygame.draw.line(s, (60, 60, 70), (gx, r.bottom), (gx, GROUND_Y - 8), 4)
            pygame.draw.circle(s, (25, 25, 30), (gx, GROUND_Y - 8), 8)

    def _draw_avion(self, s, p, i):
        r = p.rect
        nose_right = r.x < 1200
        d = 1 if nose_right else -1
        mid = r.centerx
        # aile + réacteur (décor non solide, sous le fuselage)
        pygame.draw.polygon(s, (190, 195, 210), [(mid - 40, r.bottom - 12), (mid + 40, r.bottom - 12),
                                                 (mid - d * 30, r.bottom + 30), (mid - d * 90, r.bottom + 30)])
        pygame.draw.ellipse(s, (95, 98, 112), (mid - 28, r.bottom + 2, 58, 22))
        # dérive (queue)
        tail = r.left if nose_right else r.right
        pygame.draw.polygon(s, ORANGE, [(tail, r.y + 6), (tail + d * 62, r.y + 6),
                                        (tail + d * 14, r.y - 78), (tail - d * 8, r.y - 78)])
        pygame.draw.polygon(s, GREEN, [(tail + d * 4, r.y + 6), (tail + d * 30, r.y + 6),
                                       (tail + d * 8, r.y - 40), (tail - d * 4, r.y - 40)])
        # fuselage
        pygame.draw.rect(s, (240, 242, 248), r, border_radius=r.h // 2)
        pygame.draw.rect(s, INK, r, 3, border_radius=r.h // 2)
        pygame.draw.rect(s, ORANGE, (r.x + 40, r.y + 34, r.w - 80, 7))
        for wx in range(r.x + 60, r.right - 70, 24):
            pygame.draw.rect(s, (60, 85, 125), (wx, r.y + 12, 12, 10), border_radius=3)
        nose_x = r.right - 34 if nose_right else r.left + 14
        pygame.draw.rect(s, (40, 55, 90), (nose_x, r.y + 12, 20, 11), border_radius=4)
        blit_center_text(s, "AIR BABI", 22, (40, 40, 60), (r.centerx - d * 20, r.y + 28))

    def _draw_cabine(self, s, p, i):
        r = p.rect
        glass = pygame.Surface((r.w - 20, 42), pygame.SRCALPHA)
        glass.fill((120, 190, 230, 120))
        s.blit(glass, (r.x + 10, r.y - 42))
        for gx in range(r.x + 10, r.right - 10, 36):
            pygame.draw.line(s, (50, 60, 80), (gx, r.y - 42), (gx, r.y), 2)
        pygame.draw.rect(s, (70, 80, 100), (r.x - 8, r.y - 54, r.w + 16, 12))
        pygame.draw.line(s, (70, 80, 100), (r.centerx, r.y - 54), (r.centerx, r.y - 100), 3)
        pygame.draw.circle(s, (255, 70, 70), (r.centerx, r.y - 102), 4)
        pygame.draw.rect(s, (170, 172, 185), r)
        pygame.draw.rect(s, (110, 112, 128), (r.x, r.y + 16, r.w, 8))
        pygame.draw.rect(s, (230, 230, 240), (r.x, r.y, r.w, 3))

    def _draw_tour(self, s, p, i):
        r = p.rect
        pygame.draw.rect(s, (182, 184, 196), r)
        pygame.draw.rect(s, (130, 132, 148), (r.x, r.y, 5, r.h))
        pygame.draw.rect(s, (130, 132, 148), (r.right - 5, r.y, 5, r.h))
        for k, y in enumerate(range(r.y + 30, r.y + 150, 24)):
            pygame.draw.rect(s, (220, 50, 50) if k % 2 == 0 else WHITE, (r.x, y, r.w, 24))

    def _back_wall(self, s, x0, x1, roof_y, idx):
        """Mur du bâtiment sous le toit : enduit abîmé, parpaings apparents, fenêtres à arcades."""
        rng = random.Random(900 + idx)
        lk = self.look
        top = roof_y + 16
        wx0, wx1 = x0 - 8, x1 + 8
        ww, hh = wx1 - wx0, GROUND_Y - top
        plaster_wall(s, (wx0, top, ww, hh), lk["plaster"], rng)
        if hh >= 230:                                   # grand mur : étages de fenêtres au-dessus des comptoirs
            for yy in range(top + 96, GROUND_Y - 150, 112):
                n = 2 if ww < 300 else 3
                step = (ww - 36) / n
                for c in range(n):
                    arch_window(s, int(wx0 + 18 + c * step + step / 2 - 14), yy, 28, 64, shutter=lk["shutter"], lit=rng.random() < 0.3)
        elif ww >= 300:                                 # petit mur large : fenêtres sur les côtés de l'enseigne
            for wx in (wx0 + 16, wx1 - 16 - 26):
                arch_window(s, wx, top + 34, 26, 62, shutter=None, lit=rng.random() < 0.3)
        pygame.draw.rect(s, lk["trim"], (wx0 - 4, GROUND_Y - 14, ww + 8, 14))      # soubassement
        pygame.draw.rect(s, INK, (wx0 - 4, GROUND_Y - 14, ww + 8, 14), 3)

    def _roof_props(self, s, p, i):
        r = p.rect
        rng = random.Random(40 + i)
        if p.kind == "toit_tole" and i % 2 == 0:        # fers à béton d'un étage futur
            rebar(s, r.right - 34, r.y, 4, rng)
        elif p.kind in ("toit_tole", "beton") and i % 3 == 1:   # réservoir d'eau
            tx = r.x + 26
            pygame.draw.rect(s, (36, 40, 52), (tx - 12, r.y - 8, 4, 8))
            pygame.draw.rect(s, (36, 40, 52), (tx + 8, r.y - 8, 4, 8))
            pygame.draw.ellipse(s, (222, 224, 232), (tx - 18, r.y - 34, 36, 28))
            pygame.draw.ellipse(s, (160, 168, 186), (tx - 6, r.y - 30, 20, 14))
            pygame.draw.ellipse(s, INK, (tx - 18, r.y - 34, 36, 28), 3)

    # ----- décors de maquis / stands -------------------------------------------
    def _draw_maquis(self, s, x0, x1, roof_y, label):
        g = GROUND_Y
        pts = [(x0 + (x1 - x0) * t / 20, roof_y + 22 + math.sin(math.pi * t / 20) * 10) for t in range(21)]
        pygame.draw.lines(s, (40, 30, 30), False, pts, 1)
        for k, (px, py) in enumerate(pts[::2]):
            pygame.draw.circle(s, [(255, 90, 90), (255, 230, 90), (90, 220, 130), (120, 180, 255)][k % 4], (int(px), int(py + 3)), 4)
        sign = pygame.Rect(0, 0, min(220, x1 - x0 - 90), 34)
        sign.midtop = ((x0 + x1) // 2, roof_y + 36)
        pygame.draw.rect(s, (24, 90, 60), sign, border_radius=4)
        pygame.draw.rect(s, (240, 220, 140), sign, 2, border_radius=4)
        blit_center_text(s, label, 22, (250, 240, 200), sign.center)
        for tx in (x0 + 70, x0 + 190):
            if tx + 50 > x1 - 50:
                continue
            pygame.draw.rect(s, (235, 235, 240), (tx - 28, g - 32, 56, 6))
            pygame.draw.rect(s, (150, 150, 160), (tx - 3, g - 26, 6, 26))
            for cx in (tx - 44, tx + 30):
                pygame.draw.rect(s, (200, 40, 40), (cx, g - 24, 14, 5))
                pygame.draw.rect(s, (200, 40, 40), (cx + (0 if cx < tx else 11), g - 40, 3, 20))
                pygame.draw.rect(s, (150, 30, 30), (cx + 3, g - 19, 3, 19))
                pygame.draw.rect(s, (150, 30, 30), (cx + 9, g - 19, 3, 19))
        bx = x1 - 50
        pygame.draw.rect(s, (40, 40, 48), (bx, g - 22, 34, 22))
        pygame.draw.rect(s, (255, 130, 30), (bx + 3, g - 24, 28, 5))
        pygame.draw.circle(s, (255, 190, 80), (bx + 17, g - 28), 5)

    def _draw_stand(self, s, x0, x1, roof_y, label, color):
        g = GROUND_Y
        cw = (x1 - x0) - 100
        counter = pygame.Rect(x0 + 50, g - 42, cw, 42)
        vx = counter.centerx + 40
        pygame.draw.circle(s, (110, 70, 40), (vx, g - 70), 10)
        pygame.draw.rect(s, (30, 140, 90), (vx - 12, g - 60, 24, 20))
        pygame.draw.rect(s, ORANGE, (vx - 12, g - 52, 24, 4))
        pygame.draw.rect(s, (150, 100, 60), counter)
        pygame.draw.rect(s, (90, 60, 35), counter, 2)
        pygame.draw.rect(s, (240, 235, 220), (counter.x, counter.y, counter.w, 5))
        for k in range(8):
            c = color if k % 2 == 0 else WHITE
            pygame.draw.rect(s, c, (counter.x + k * cw // 8, roof_y + 20, cw // 8 + 1, 18))
        blit_center_text(s, label, 24, BLACK, (counter.centerx, roof_y + 54))
        for k in range(3):
            pygame.draw.line(s, (40, 30, 30), (counter.x + 30 + k * cw // 3, roof_y + 38),
                             (counter.x + 30 + k * cw // 3, roof_y + 66), 1)
            pygame.draw.circle(s, (255, 235, 140), (counter.x + 30 + k * cw // 3, roof_y + 70), 5)
