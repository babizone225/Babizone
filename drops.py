"""Babizone - armes laissées au sol (par un joueur éliminé ou échangées) et ramassage."""
import math
import random
import pygame
from settings import *
from sprites import weapon_icon
from weapon import WEAPON_SPECS

DROP_TTL = 25.0            # durée de vie d'une arme au sol (s)
DROP_W, DROP_H = 44, 22
PICK_REACH = (36, 26)      # marge de ramassage autour du joueur


class DroppedWeapon:
    def __init__(self, key, ammo, x, y, vx=0.0, vy=0.0, owner=None, delay=0.0, ttl=DROP_TTL):
        self.key = key
        self.ammo = int(ammo)
        self.rect = pygame.Rect(0, 0, DROP_W, DROP_H)
        self.rect.center = (int(x), int(y))
        self.pos = pygame.Vector2(self.rect.x, self.rect.y)
        self.vx, self.vy = vx, vy
        self.owner, self.delay, self.ttl = owner, delay, ttl     # owner/delay : évite de re-ramasser aussitôt son arme jetée
        self.on_ground = False
        self.dead = False

    @property
    def name(self):
        return WEAPON_SPECS[self.key]["name"]

    def can_pick(self, player):
        return player is not self.owner or self.delay <= 0

    def reachable_by(self, player):
        return self.can_pick(player) and player.rect.inflate(*PICK_REACH).colliderect(self.rect)

    def update(self, dt, solids):
        self.ttl -= dt
        self.delay = max(0.0, self.delay - dt)
        if self.ttl <= 0:
            self.dead = True
            return
        r = self.rect
        self.vy = min(self.vy + 1400 * dt, 900)
        self.pos.x += self.vx * dt
        r.x = round(self.pos.x)
        for s in solids:
            if r.colliderect(s):
                if self.vx > 0:
                    r.right = s.left
                else:
                    r.left = s.right
                self.pos.x = r.x
                self.vx = -self.vx * 0.3
        self.pos.y += self.vy * dt
        r.y = round(self.pos.y)
        for s in solids:
            if r.colliderect(s):
                if self.vy > 0:
                    r.bottom = s.top
                else:
                    r.top = s.bottom
                self.pos.y = r.y
                self.vy = 0.0 if self.vy > 0 else abs(self.vy) * 0.2
        r.left = max(0, r.left)
        r.right = min(WORLD_W, r.right)
        self.pos.update(r.x, r.y)
        self.on_ground = r.move(0, 1).collidelist(solids) != -1 and self.vy >= 0
        if self.on_ground:
            self.vx *= max(0.0, 1.0 - 9 * dt)

    def draw(self, surf, ox, oy, t=0.0):
        if self.ttl < 5 and int(self.ttl * 6) % 2 == 0:       # clignote avant de disparaître
            return
        bob = math.sin(t * 3 + self.rect.x) * 2 if self.on_ground else 0
        cx, cy = self.rect.centerx - ox, self.rect.centery - oy + bob
        col = WEAPON_SPECS[self.key]["color"]
        pygame.draw.circle(surf, col, (int(cx), int(cy)), int(25 + math.sin(t * 5) * 2), 2)
        icon = weapon_icon(self.key)
        surf.blit(icon, icon.get_rect(center=(int(cx), int(cy))))
