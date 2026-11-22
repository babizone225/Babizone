"""Babizone - joueur : physique, jet-pack, visée à 360°, collisions, contrôles et IA."""
import math
import random
import pygame
from settings import *
from weapon import Weapon, random_primary_key, WEAPON_TIER
from projectile import Particle
from sprites import HAIRS, HAIR_COLORS, ACCESSORIES, BEARDS, draw_character

# --- Personnalisation : tenue, teint, coiffure ---------------------------------
# Chaque tenue = tee-shirt, bande, short, baskets, casque ôtodji, accent
OUTFITS = [
    ("Éléphants",      dict(style="tee", tee=(247, 127, 0), stripe=WHITE, shorts=(0, 140, 85), shoes=WHITE,
                            helmet=(245, 245, 245), accent=GREEN)),
    ("Wax de Treichville", dict(style="tank", tee=(250, 210, 40), stripe=(40, 70, 170), shorts=(40, 70, 160), shoes=(30, 30, 30),
                            helmet=(30, 30, 35), accent=ORANGE)),
    ("Drill noir",     dict(style="jacket", tee=(35, 35, 42), stripe=ORANGE, shorts=(30, 30, 45), shoes=ORANGE,
                            helmet=(215, 55, 55), accent=WHITE)),
    ("Vert Yopougon",  dict(style="tee", tee=(0, 158, 96), stripe=WHITE, shorts=(240, 240, 240), shoes=ORANGE,
                            helmet=ORANGE, accent=WHITE)),
    ("Ciel de Cocody", dict(style="vest", tee=(60, 120, 235), stripe=WHITE, shorts=(30, 30, 30), shoes=(255, 220, 60),
                            helmet=(240, 240, 250), accent=(255, 220, 60))),
    ("Coupé-Décalé",   dict(style="jacket", tee=(160, 70, 205), stripe=(255, 220, 60), shorts=(235, 235, 235), shoes=(30, 30, 30),
                            helmet=(245, 245, 245), accent=(160, 70, 205))),
    ("Chasseur Dozo",  dict(style="vest", tee=(150, 108, 62), stripe=(222, 182, 100), shorts=(78, 66, 46), shoes=(52, 40, 30),
                            helmet=(150, 108, 62), accent=(92, 132, 62))),
    ("Treillis Babi",  dict(style="jacket", tee=(82, 104, 72), stripe=ORANGE, shorts=(60, 72, 56), shoes=(40, 34, 30),
                            helmet=(70, 88, 62), accent=ORANGE)),
]
SKINS = [
    ("Ébène", (70, 44, 28)), ("Brun foncé", (95, 60, 36)), ("Brun", (125, 82, 52)),
    ("Caramel", (160, 110, 70)), ("Doré", (190, 140, 95)), ("Clair", (225, 180, 140)),
]
WEAPON_CHOICES = ["nouchi", "coupe", "dozo", "sniper"]


def build_palette(outfit=0, skin=2, hair=0, hcol=0, acc=0, beard=0):
    pal = dict(OUTFITS[outfit % len(OUTFITS)][1])
    pal["skin"] = SKINS[skin % len(SKINS)][1]
    pal["hair"] = hair % len(HAIRS)
    pal["hair_col"] = HAIR_COLORS[hcol % len(HAIR_COLORS)][1]
    pal["acc"] = acc % len(ACCESSORIES)
    pal["beard"] = beard % len(BEARDS)
    pal["iris"] = tuple(int(v * .85) for v in pal["hair_col"]) if hcol >= 3 else (72, 48, 34)   # yeux assortis aux cheveux colorés
    return pal


def default_profile(name="Joueur"):
    return dict(name=name, outfit=0, skin=2, hair=1, hcol=0, acc=0, beard=0, w1="coupe", w2="nouchi")


def random_profile(name):
    return dict(name=name, outfit=random.randrange(len(OUTFITS)), skin=random.randrange(len(SKINS)),
                hair=random.randrange(len(HAIRS)), hcol=random.randrange(len(HAIR_COLORS)),
                acc=random.choice((0, 0, 1, 2, 3, 4, 5)), beard=random.choice((0, 0, 0, 1, 2, 3)),
                w1=random.choice(("coupe", "dozo", "sniper")), w2="nouchi")


def palette_of(profile):
    return build_palette(profile["outfit"], profile["skin"], profile["hair"], profile.get("hcol", 0),
                         profile.get("acc", 0), profile.get("beard", 0))


def angle_diff(a, b):
    return (b - a + math.pi) % (2 * math.pi) - math.pi


class Intent:
    """Ce que veut faire un joueur à cette frame (humain ou bot)."""

    def __init__(self):
        self.move = 0.0
        self.jet = False
        self.fire = False
        self.reload = False
        self.switch = False
        self.pickup = False
        self.aim = 0.0


# ---------------------------------------------------------------------------
class Player:
    def __init__(self, name, palette, is_bot=False, loadout=("coupe", "nouchi")):
        self.loadout = tuple(loadout)
        self.name = name
        self.pal = palette
        self.is_bot = is_bot
        self.rect = pygame.Rect(0, 0, PLAYER_W, PLAYER_H)
        self.pos = pygame.Vector2(0, 0)
        self.vx = self.vy = 0.0
        self.kills = 0
        self.deaths = 0
        self.fx = []                 # particules à récupérer par le jeu
        self.alive = False
        self.respawn_timer = 0.0
        self.aim = 0.0
        self.facing = 1
        self.anim = 0.0
        self.thrusting = False
        self.on_ground = False
        self.hurt = 0.0
        self.invuln = 0.0
        self.boost = 0.0
        self.health = MAX_HEALTH
        self.fuel = 100.0
        self.fuel_delay = 0.0
        self.weapons = [Weapon(self.loadout[0]), Weapon(self.loadout[1])]
        self.cur = 0
        self.tx = self.ty = 0.0      # cible réseau (clients)
        self.events = []             # sons à jouer (lus par le jeu)
        self.jet_timer = 0.0
        self.empty_timer = 0.0
        self.want_pickup = False
        self.respawn_left = 0.0

    # ----- propriétés utiles ---------------------------------------------------
    @property
    def weapon(self):
        return self.weapons[self.cur]

    @property
    def center(self):
        return self.rect.center

    def shoulder(self):
        return self.rect.centerx, self.rect.top + 28

    def muzzle(self):
        sx, sy = self.shoulder()
        L = self.weapon.spec["length"]
        return sx + math.cos(self.aim) * L, sy + math.sin(self.aim) * L

    # ----- cycle de vie -----------------------------------------------------------
    def respawn(self, spawn):
        self.rect.midbottom = spawn
        self.pos.update(self.rect.x, self.rect.y)
        self.vx = self.vy = 0.0
        self.health = MAX_HEALTH
        self.fuel = 100.0
        self.fuel_delay = 0.0
        self.boost = 0.0
        self.hurt = 0.0
        self.invuln = SPAWN_INVULN
        self.alive = True
        self.weapons = [Weapon(self.loadout[0]), Weapon(self.loadout[1])]
        self.cur = 0

    def die(self):
        self.alive = False
        self.deaths += 1
        self.respawn_timer = RESPAWN_TIME

    def take_damage(self, dmg, angle=0.0):
        """Retourne True si ce coup tue le joueur."""
        if not self.alive or self.invuln > 0:
            return False
        self.health -= dmg
        self.hurt = 0.12
        self.vx += math.cos(angle) * dmg * 4
        self.vy += math.sin(angle) * dmg * 2
        if self.health <= 0:
            self.health = 0
            self.die()
            return True
        return False

    def apply_pickup(self, kind):
        """Applique un bonus. Retourne False s'il est inutile (on le laisse alors au sol)."""
        if kind == "garba":
            if self.health >= MAX_HEALTH:
                return False
            self.health = min(MAX_HEALTH, self.health + 50)
        elif kind == "alloco":
            if self.health >= MAX_HEALTH and self.fuel >= 100:
                return False
            self.health = min(MAX_HEALTH, self.health + 25)
            self.fuel = min(100.0, self.fuel + 40)
        elif kind == "gnamankoudji":
            self.boost = 8.0
            self.fuel = 100.0
        elif kind == "caisse":
            self.weapons[0] = Weapon(random_primary_key())
            self.weapons[1].refill()
            self.cur = 0
        return True

    def take_weapon(self, drop):
        """Ramasse une arme au sol. Retourne l'arme remplacée (à reposer au sol) ou None."""
        cur = self.weapon
        if cur.key == drop.key:                       # même arme : on récupère les munitions
            cur.ammo = min(cur.spec["mag"], cur.ammo + max(drop.ammo, cur.spec["mag"] // 2))
            return None
        self.weapons[self.cur] = Weapon(drop.key, drop.ammo)
        return cur if cur.key != "nouchi" else None   # on ne rejette pas le pistolet de base

    # ----- mise à jour --------------------------------------------------------------
    def update(self, dt, it, gmap):
        """Met à jour la physique et le tir. Retourne la liste des nouveaux projectiles."""
        shots = []
        if not self.alive:
            return shots

        self.invuln = max(0.0, self.invuln - dt)
        self.hurt = max(0.0, self.hurt - dt)
        self.boost = max(0.0, self.boost - dt)

        self.aim = it.aim
        self.facing = 1 if math.cos(self.aim) >= 0 else -1

        # --- déplacement horizontal
        speed = RUN_SPEED * (1.5 if self.boost > 0 else 1.0)
        accel = GROUND_ACCEL if self.on_ground else AIR_ACCEL
        self.vx += (it.move * speed - self.vx) * min(1.0, accel * dt)
        if abs(self.vx) > 20 and self.on_ground:
            self.anim += abs(self.vx) * dt * 0.05

        # --- saut / jet-pack
        self.thrusting = False
        if it.jet:
            if self.on_ground:
                self.vy = JUMP_V
                self.on_ground = False
            elif self.fuel > 0:
                self.thrusting = True
                self.vy -= JET_THRUST * dt
                self.fuel -= JET_BURN * dt
        if self.thrusting:
            self.fuel_delay = JET_DELAY
            self.emit_flame()
            self.jet_timer -= dt
            if self.jet_timer <= 0:
                self.events.append("jet")
                self.jet_timer = 0.11
        else:
            self.fuel_delay -= dt
            if self.fuel_delay <= 0:
                self.fuel += (JET_RECHARGE_GROUND if self.on_ground else JET_RECHARGE_AIR) * dt
        self.fuel = max(0.0, min(100.0, self.fuel))

        # --- gravité
        self.vy += GRAVITY * dt
        self.vy = max(-MAX_RISE, min(MAX_FALL, self.vy))

        self._move(dt, gmap.solids)

        # --- armes
        self.want_pickup = bool(it.pickup)
        self.empty_timer = max(0.0, self.empty_timer - dt)
        for w in self.weapons:
            w.update(dt)
        cur, was_reloading = self.weapon, self.weapon.reloading
        if it.switch:
            self.cur = 1 - self.cur
        if it.reload:
            self.weapon.start_reload()
        if it.fire:
            if self.weapon.reloading and self.empty_timer <= 0 and self.weapon.ammo <= 0:
                self.events.append("empty")
                self.empty_timer = 0.4
            shots = self.weapon.fire(self)
        if self.weapon is cur and self.weapon.reloading and not was_reloading:
            self.events.append("reload")
        return shots

    def emit_flame(self):
        jx = self.rect.centerx - self.facing * 13
        self.fx.append(Particle(jx + random.uniform(-3, 3), self.rect.centery + 4,
                                random.uniform(-40, 40), random.uniform(180, 320), 0.3,
                                random.choice(((255, 170, 40), (255, 90, 30), (255, 230, 150))),
                                size=5))

    # ----- réseau (côté client) -------------------------------------------------------
    def net_apply(self, a):
        """Applique un instantané envoyé par l'hôte."""
        (x, y, vx, vy, aim, hp, fuel, alive, kills, deaths, cur, w0, w1,
         ammo, reloading, invuln, boost, thrust, ground, resp) = a
        if self.alive != bool(alive) or abs(self.tx - x) > 250 or abs(self.ty - y) > 250:
            self.rect.topleft = (x, y)
        self.tx, self.ty = x, y
        self.vx, self.vy, self.aim = vx, vy, aim
        self.health, self.fuel = hp, fuel
        self.alive = bool(alive)
        self.kills, self.deaths = kills, deaths
        if self.weapons[0].key != w0:
            self.weapons[0] = Weapon(w0)
        if self.weapons[1].key != w1:
            self.weapons[1] = Weapon(w1)
        self.cur = cur
        self.weapon.ammo, self.weapon.reloading = ammo, bool(reloading)
        self.invuln, self.boost = invuln / 10.0, boost / 10.0
        self.thrusting, self.on_ground = bool(thrust), bool(ground)
        self.respawn_left = resp / 10.0
        self.respawn_timer = resp / 10.0
        self.facing = 1 if math.cos(aim) >= 0 else -1

    def net_step(self, dt):
        """Lissage de la position affichée entre deux instantanés."""
        k = min(1.0, 22 * dt)
        self.rect.x += round((self.tx - self.rect.x) * k)
        self.rect.y += round((self.ty - self.rect.y) * k)
        if self.on_ground and abs(self.vx) > 20:
            self.anim += abs(self.vx) * dt * 0.05
        self.hurt = max(0.0, self.hurt - dt)

    def net_pack(self):
        w = self.weapon
        return [self.rect.x, self.rect.y, int(self.vx), int(self.vy), round(self.aim, 3),
                int(self.health), int(self.fuel), int(self.alive), self.kills, self.deaths, self.cur,
                self.weapons[0].key, self.weapons[1].key, w.ammo, int(w.reloading),
                int(self.invuln * 10), int(self.boost * 10), int(self.thrusting), int(self.on_ground),
                int(max(0, self.respawn_timer) * 10)]

    def _move(self, dt, solids):
        r = self.rect
        # axe X
        self.pos.x += self.vx * dt
        r.x = round(self.pos.x)
        for s in solids:
            if r.colliderect(s):
                if self.vx > 0:
                    r.right = s.left
                elif self.vx < 0:
                    r.left = s.right
                self.pos.x = r.x
                self.vx = 0.0
        # axe Y
        self.pos.y += self.vy * dt
        r.y = round(self.pos.y)
        for s in solids:
            if r.colliderect(s):
                if self.vy > 0:
                    r.bottom = s.top
                elif self.vy < 0:
                    r.top = s.bottom
                self.pos.y = r.y
                self.vy = 0.0
        # limites du monde
        if r.left < 0:
            r.left, self.vx = 0, 0.0
        if r.right > WORLD_W:
            r.right, self.vx = WORLD_W, 0.0
        if r.top < 0:
            r.top, self.vy = 0, 0.0
        self.pos.update(r.x, r.y)
        # contact avec le sol (test à 1 px pour éviter tout clignotement)
        probe = r.move(0, 1)
        self.on_ground = self.vy >= 0 and probe.collidelist(solids) != -1
        if self.on_ground:
            self.vy = 0.0

    # ----- dessin ------------------------------------------------------------------------
    def draw(self, surf, ox, oy):
        if not self.alive:
            return
        if self.invuln > 0 and int(self.invuln * 12) % 2 == 0:
            return
        draw_character(surf, self, ox, oy)

    def draw_label(self, surf, ox, oy, fnt, color=WHITE, bars=True):
        if not self.alive:
            return
        cx = self.rect.centerx - ox
        top = self.rect.top - oy - (24 if self.pal.get("hair") in (1, 3, 5, 8) else 14)
        img = fnt.render(self.name, True, color)
        surf.blit(img, img.get_rect(midbottom=(cx, top - 10)))
        if bars:
            pygame.draw.rect(surf, (30, 30, 35), (cx - 17, top - 8, 34, 5))
            pygame.draw.rect(surf, (230, 60, 60) if self.health < 35 else (90, 220, 110),
                             (cx - 16, top - 7, int(32 * self.health / MAX_HEALTH), 3))


# ---------------------------------------------------------------------------
#  Contrôleur humain (clavier + souris, ou clavier seul)
# ---------------------------------------------------------------------------
class HumanController:
    def __init__(self, keys, use_mouse):
        self.keys = keys
        self.use_mouse = use_mouse
        self.aim = 0.0
        self._prev_reload = False
        self._prev_switch = False
        self._prev_flip = False
        self._prev_pickup = False
        self.pickup_label = "?"

    def _down(self, k, name):
        return any(k[c] for c in self.keys.get(name, ()))

    def intent(self, player, screen_shoulder, dt):
        k = pygame.key.get_pressed()
        it = Intent()
        it.move = float(self._down(k, "right")) - float(self._down(k, "left"))
        it.jet = self._down(k, "jet")

        reload_now = self._down(k, "reload")
        switch_now = self._down(k, "switch")

        if self.use_mouse:
            mx, my = pygame.mouse.get_pos()
            self.aim = math.atan2(my - screen_shoulder[1], mx - screen_shoulder[0])
            btn = pygame.mouse.get_pressed()
            it.fire = btn[0] or self._down(k, "fire")
            switch_now = switch_now or btn[2]
        else:
            rot = float(self._down(k, "aim_cw")) - float(self._down(k, "aim_ccw"))
            self.aim += rot * AIM_ROT_SPEED * dt
            flip_now = self._down(k, "aim_flip")
            if flip_now and not self._prev_flip:
                self.aim = math.pi - self.aim
            self._prev_flip = flip_now
            it.fire = self._down(k, "fire")

        self.aim = (self.aim + math.pi) % math.tau - math.pi
        it.aim = self.aim
        pick_now = self._down(k, "pickup")
        it.reload = reload_now and not self._prev_reload
        it.switch = switch_now and not self._prev_switch
        it.pickup = pick_now and not self._prev_pickup
        self._prev_reload, self._prev_switch, self._prev_pickup = reload_now, switch_now, pick_now
        return it


# ---------------------------------------------------------------------------
#  IA des bots
# ---------------------------------------------------------------------------
class BotBrain:
    def __init__(self, skill=0.65, reaction=0.3):
        self.skill = skill
        self.reaction = reaction     # délai avant de tirer quand la cible apparaît
        self.react = reaction
        self.aim = random.uniform(-math.pi, math.pi)
        self.target = None
        self.think = 0.0
        self.strafe = 1
        self.noise = 0.0
        self.stuck = 0.0
        self.unstick = 0.0
        self.unstick_dir = 1

    def _weapon_goal(self, me, drops, it):
        """Arme au sol meilleure que la mienne, à portée : on y va (et on la ramasse)."""
        tier = WEAPON_TIER[me.weapon.key]
        best, bd = None, 9999
        for d in drops:
            if WEAPON_TIER[d.key] > tier and d.can_pick(me):
                dx, dy = d.rect.centerx - me.rect.centerx, d.rect.centery - me.rect.centery
                dist = abs(dx) + abs(dy) * 0.6
                if abs(dx) < 520 and abs(dy) < 300 and dist < bd:
                    best, bd = d, dist
        if best is None:
            return False
        dx = best.rect.centerx - me.rect.centerx
        it.move = 1.0 if dx > 18 else (-1.0 if dx < -18 else 0.0)
        it.jet = best.rect.centery < me.rect.centery - 40
        it.pickup = best.reachable_by(me)
        return True

    def intent(self, me, others, gmap, pickups, dt, drops=()):
        it = Intent()
        it.aim = self.aim

        self.think -= dt
        if self.think <= 0:
            self.think = random.uniform(0.3, 0.7)
            alive = [e for e in others if e.alive]
            self.target = min(alive, key=lambda e: math.hypot(e.rect.centerx - me.rect.centerx,
                                                             e.rect.centery - me.rect.centery)) if alive else None
            self.strafe = random.choice((-1, 1))
            self.noise = random.uniform(-1, 1) * (1.0 - self.skill) * 0.22

        t = self.target
        if t is None or not t.alive:
            it.move = self.strafe * 0.3
            self._weapon_goal(me, drops, it)
            return it

        dx = t.rect.centerx - me.rect.centerx
        dy = t.rect.centery - me.rect.centery
        dist = math.hypot(dx, dy)

        # visée avec anticipation et erreur
        lead = dist / 900.0 * 0.5 * self.skill
        ideal = math.atan2(dy + t.vy * lead, dx + t.vx * lead) + self.noise
        turn = (3.0 + 5.0 * self.skill) * dt
        self.aim += max(-turn, min(turn, angle_diff(self.aim, ideal)))
        it.aim = self.aim

        # déplacement
        if dist > 450:
            it.move = 1.0 if dx > 0 else -1.0
        elif dist < 200:
            it.move = -1.0 if dx > 0 else 1.0
        else:
            it.move = self.strafe * 0.6

        # altitude
        it.jet = dy < -50 or (me.vy > 120 and dy < 80 and me.fuel > 35 and not me.on_ground)
        if me.on_ground and random.random() < 0.004:
            it.jet = True

        # besoin de soins : aller chercher Garba / Alloco
        if me.health < 50 and pickups:
            heal = [p for p in pickups if p.kind in ("garba", "alloco")]
            if heal:
                p = min(heal, key=lambda p: abs(p.rect.centerx - me.rect.centerx) + abs(p.rect.centery - me.rect.centery))
                it.move = 1.0 if p.rect.centerx > me.rect.centerx else -1.0
                it.jet = p.rect.centery < me.rect.centery - 30

        # arme au sol plus puissante : on la récupère si le combat n'est pas imminent
        if me.health >= 40 and (dist > 380 or not gmap.line_clear(me.muzzle(), t.rect.center)):
            self._weapon_goal(me, drops, it)

        # coincé sous un plafond ?
        if it.jet and abs(me.vy) < 20 and not me.on_ground:
            self.stuck += dt
        else:
            self.stuck = 0.0
        if self.stuck > 0.5:
            self.unstick, self.unstick_dir, self.stuck = 0.6, random.choice((-1, 1)), 0.0
        if self.unstick > 0:
            self.unstick -= dt
            it.move, it.jet = float(self.unstick_dir), True

        # tir
        los = gmap.line_clear(me.muzzle(), t.rect.center)
        aimed = abs(angle_diff(self.aim, math.atan2(dy, dx))) < 0.10 + (1 - self.skill) * 0.12
        if not los:
            self.react = self.reaction
        else:
            self.react = max(0.0, self.react - dt)
        it.fire = bool(los and aimed and dist < 500 + 300 * self.skill and self.react <= 0)
        return it
