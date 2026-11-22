"""Babizone - commandes tactiles (style Mini Militia : deux sticks + boutons).

  stick gauche : gauche/droite = courir, vers le haut = saut puis jet-pack
  stick droit  : direction = visée à 360°, poussé à fond = tir automatique
  boutons      : recharger, changer d'arme, ramasser, pause

Les sticks apparaissent là où le pouce se pose (zones gauche / droite de l'écran).
Fonctionne avec de vrais doigts (multi-touch) et, pour tester sur PC, avec la souris
(un seul « doigt » à la fois).
"""
import math
import pygame
from settings import *
from player import Intent

STICK_R = 105
DEAD = 0.18


def to_logical(nx, ny):
    """Coordonnées normalisées d'un doigt (0..1 sur la fenêtre) -> coordonnées du jeu (1280x720),
    en tenant compte des bandes noires quand l'écran n'est pas en 16:9."""
    try:
        ww, wh = pygame.display.get_window_size()
    except Exception:
        ww, wh = SCREEN_W, SCREEN_H
    scale = min(ww / SCREEN_W, wh / SCREEN_H) or 1.0
    ox, oy = (ww - SCREEN_W * scale) / 2, (wh - SCREEN_H * scale) / 2
    return (nx * ww - ox) / scale, (ny * wh - oy) / scale


class TouchControls:
    use_mouse = False
    pickup_label = "bouton PRENDRE"

    def __init__(self, fonts):
        self.f_s, self.f_m = fonts[0], fonts[1]
        self.default_left = (190, 565)
        self.default_right = (1090, 565)
        # nom : (centre, rayon, texte)
        self.buttons = {
            "reload": ((1215, 400), 42, "R"),
            "switch": ((1215, 305), 42, "ARME"),
            "pickup": ((960, 400), 46, "PRENDRE"),
            "pause": ((52, 52), 34, "II"),
        }
        self.fingers = {}            # id -> dict(role, base, pos)
        self.pending = set()         # actions à impulsion (reload, switch, pickup, pause)
        self.aim = 0.0
        self._cache = {}

    # ----- événements --------------------------------------------------------------------
    def handle(self, e, emulate_mouse=True):
        """Traite un événement pygame. Retourne True si l'événement a été utilisé."""
        t = e.type
        if t == getattr(pygame, "FINGERDOWN", -1):
            return self._down(("f", e.finger_id), to_logical(e.x, e.y))
        if t == getattr(pygame, "FINGERMOTION", -1):
            return self._move(("f", e.finger_id), to_logical(e.x, e.y))
        if t == getattr(pygame, "FINGERUP", -1):
            return self._up(("f", e.finger_id))
        if emulate_mouse and not getattr(e, "touch", False):      # souris = un doigt (test sur PC)
            if t == pygame.MOUSEBUTTONDOWN and e.button == 1:
                return self._down(("m", 0), e.pos)
            if t == pygame.MOUSEMOTION and ("m", 0) in self.fingers:
                return self._move(("m", 0), e.pos)
            if t == pygame.MOUSEBUTTONUP and e.button == 1:
                return self._up(("m", 0))
        return False

    def _hit_button(self, p):
        for name, (c, r, _) in self.buttons.items():
            if (p[0] - c[0]) ** 2 + (p[1] - c[1]) ** 2 <= (r + 12) ** 2:
                return name
        return None

    def _down(self, fid, p):
        name = self._hit_button(p)
        if name:
            self.pending.add(name)
            self.fingers[fid] = dict(role="btn:" + name, base=p, pos=p)
            return True
        if p[1] < 160:
            return False
        role = "L" if p[0] < SCREEN_W / 2 else "R"
        if any(f["role"] == role for f in self.fingers.values()):
            return False
        self.fingers[fid] = dict(role=role, base=p, pos=p)
        return True

    def _move(self, fid, p):
        f = self.fingers.get(fid)
        if not f:
            return False
        f["pos"] = p
        return True

    def _up(self, fid):
        return self.fingers.pop(fid, None) is not None

    def consume(self, name):
        if name in self.pending:
            self.pending.discard(name)
            return True
        return False

    # ----- lecture des sticks ---------------------------------------------------------------
    def _vec(self, role):
        for f in self.fingers.values():
            if f["role"] == role:
                dx, dy = f["pos"][0] - f["base"][0], f["pos"][1] - f["base"][1]
                d = math.hypot(dx, dy)
                if d > STICK_R:
                    dx, dy, d = dx * STICK_R / d, dy * STICK_R / d, STICK_R
                return dx / STICK_R, dy / STICK_R, d / STICK_R
        return None

    def intent(self, player, screen_shoulder, dt):
        it = Intent()
        left, right = self._vec("L"), self._vec("R")
        if left:
            dx, dy, _ = left
            if abs(dx) > DEAD:
                it.move = math.copysign(min(1.0, (abs(dx) - DEAD) / 0.55), dx)
            it.jet = dy < -0.45
        if right and right[2] > DEAD:
            self.aim = math.atan2(right[1], right[0])
            it.fire = right[2] > 0.55
        it.aim = self.aim
        it.reload = self.consume("reload")
        it.switch = self.consume("switch")
        it.pickup = self.consume("pickup")
        return it

    # ----- dessin -------------------------------------------------------------------------------
    def _disc(self, r, rgba):
        key = (r, rgba)
        if key not in self._cache:
            s = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(s, rgba, (r + 2, r + 2), r)
            pygame.draw.circle(s, (255, 255, 255, min(255, rgba[3] + 70)), (r + 2, r + 2), r, 3)
            self._cache[key] = s
        return self._cache[key]

    def _blit_disc(self, surf, c, r, rgba):
        d = self._disc(int(r), rgba)
        surf.blit(d, d.get_rect(center=(int(c[0]), int(c[1]))))

    def draw(self, surf, near_drop=False):
        for role, default in (("L", self.default_left), ("R", self.default_right)):
            active = next((f for f in self.fingers.values() if f["role"] == role), None)
            if active:
                v = self._vec(role)
                self._blit_disc(surf, active["base"], STICK_R, (255, 255, 255, 50))
                kx = active["base"][0] + v[0] * STICK_R
                ky = active["base"][1] + v[1] * STICK_R
                hot = (role == "R" and v[2] > 0.55) or (role == "L" and v[1] < -0.45)
                self._blit_disc(surf, (kx, ky), 44, (255, 140, 30, 190) if hot else (255, 255, 255, 140))
            else:
                self._blit_disc(surf, default, STICK_R, (255, 255, 255, 28))
                self._blit_disc(surf, default, 40, (255, 255, 255, 55))
                label = "BOUGER / VOLER" if role == "L" else "VISER / TIRER"
                img = self.f_s.render(label, True, (255, 255, 255))
                surf.blit(img, img.get_rect(center=(default[0], default[1] + STICK_R + 22)))
        for name, (c, r, txt) in self.buttons.items():
            pressed = any(f["role"] == "btn:" + name for f in self.fingers.values())
            hot = name == "pickup" and near_drop
            rgba = (255, 200, 40, 200) if hot else ((255, 255, 255, 120) if pressed else (30, 30, 50, 130))
            self._blit_disc(surf, c, r, rgba)
            img = self.f_s.render(txt, True, (20, 20, 20) if hot else (255, 255, 255))
            surf.blit(img, img.get_rect(center=c))
