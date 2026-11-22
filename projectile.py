"""Babizone - projectiles (balles) et particules."""
import math
import pygame
from settings import WORLD_W, WORLD_H


class Particle:
    """Petite particule visuelle (étincelles, flammes, éclats...)."""

    __slots__ = ("x", "y", "vx", "vy", "life", "max_life", "color",
                 "size", "gravity", "dead")

    def __init__(self, x, y, vx, vy, life, color, size=3, gravity=0.0):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.life = self.max_life = life
        self.color = color
        self.size = size
        self.gravity = gravity
        self.dead = False

    def update(self, dt):
        self.life -= dt
        if self.life <= 0:
            self.dead = True
            return
        self.vy += self.gravity * dt
        self.x += self.vx * dt
        self.y += self.vy * dt

    def draw(self, surf, ox, oy):
        r = max(1, int(self.size * self.life / self.max_life))
        pygame.draw.circle(surf, self.color, (int(self.x - ox), int(self.y - oy)), r)


class Projectile:
    """Balle : avance par sous-pas pour ne jamais traverser un mur ou un joueur."""

    def __init__(self, x, y, vx, vy, damage, owner, life, color,
                 width=3, trail=0.03, gravity=0.0):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.damage = damage
        self.owner = owner
        self.life = life
        self.color = color
        self.width = width
        self.trail = trail
        self.gravity = gravity
        self.dead = False

    @property
    def angle(self):
        return math.atan2(self.vy, self.vx)

    def update(self, dt, solids, players):
        """Retourne None, ("wall", (x, y)) ou ("player", joueur)."""
        self.life -= dt
        if self.life <= 0:
            self.dead = True
            return None

        self.vy += self.gravity * dt
        dist = math.hypot(self.vx, self.vy) * dt
        steps = int(dist // 6) + 1
        sx, sy = self.vx * dt / steps, self.vy * dt / steps

        for _ in range(steps):
            self.x += sx
            self.y += sy
            px, py = int(self.x), int(self.y)

            if self.x < 0 or self.x > WORLD_W or self.y > WORLD_H or self.y < -300:
                self.dead = True
                return ("wall", (self.x, self.y))

            for s in solids:
                if s.collidepoint(px, py):
                    self.dead = True
                    return ("wall", (self.x, self.y))

            for p in players:
                if (p is not self.owner and p.alive and p.invuln <= 0
                        and p.rect.collidepoint(px, py)):
                    self.dead = True
                    return ("player", p)
        return None

    def draw(self, surf, ox, oy):
        tx = self.x - self.vx * self.trail
        ty = self.y - self.vy * self.trail
        pygame.draw.line(surf, self.color,
                         (tx - ox, ty - oy), (self.x - ox, self.y - oy), self.width)
