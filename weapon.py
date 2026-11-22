"""Babizone - armes : cadence de tir, rechargement, dispersion, dégâts."""
import math
import random
from projectile import Projectile, Particle

# damage = dégâts par projectile | cooldown = secondes entre 2 tirs
# spread = dispersion (degrés)   | recoil = recul appliqué au tireur
WEAPON_SPECS = {
    "nouchi": dict(
        name="Pistolet Nouchi", damage=14, cooldown=0.26, mag=12, reload=1.0,
        speed=950, spread=1.5, pellets=1, life=1.0, color=(255, 230, 120),
        length=32, recoil=30, width=3, trail=0.025, gravity=0),
    "coupe": dict(
        name="Mitraillette Coupé-Décalé", damage=8, cooldown=0.075, mag=32, reload=1.5,
        speed=1000, spread=4.5, pellets=1, life=0.9, color=(255, 170, 60),
        length=69, recoil=45, width=3, trail=0.03, gravity=0),
    "dozo": dict(
        name="Fusil Dozo", damage=10, cooldown=0.85, mag=6, reload=1.9,
        speed=850, spread=8.0, pellets=7, life=0.45, color=(255, 120, 90),
        length=76, recoil=260, width=2, trail=0.02, gravity=250),
    "sniper": dict(
        name="Sniper du Plateau", damage=70, cooldown=1.1, mag=4, reload=2.3,
        speed=1800, spread=0.2, pellets=1, life=1.3, color=(120, 255, 255),
        length=92, recoil=200, width=4, trail=0.05, gravity=0),
}

PRIMARY_KEYS = ("coupe", "dozo", "sniper")
WEAPON_TIER = {"nouchi": 0, "coupe": 1, "dozo": 2, "sniper": 3}     # sert à choisir le butin et à guider les bots


def random_primary_key():
    return random.choice(PRIMARY_KEYS)


class Weapon:
    def __init__(self, key, ammo=None):
        self.key = key
        self.spec = WEAPON_SPECS[key]
        self.ammo = self.spec["mag"] if ammo is None else max(0, min(self.spec["mag"], int(ammo)))
        self.cooldown = 0.0
        self.reloading = False
        self.reload_timer = 0.0

    @property
    def name(self):
        return self.spec["name"]

    def refill(self):
        self.ammo = self.spec["mag"]
        self.reloading = False
        self.cooldown = 0.0

    def update(self, dt):
        if self.cooldown > 0:
            self.cooldown -= dt
        if self.reloading:
            self.reload_timer -= dt
            if self.reload_timer <= 0:
                self.reloading = False
                self.ammo = self.spec["mag"]

    def start_reload(self):
        if not self.reloading and self.ammo < self.spec["mag"]:
            self.reloading = True
            self.reload_timer = self.spec["reload"]

    def fire(self, owner):
        """Tire depuis `owner` (qui expose .aim, .muzzle(), .vx, .vy, .fx)."""
        if self.reloading or self.cooldown > 0:
            return []
        if self.ammo <= 0:
            self.start_reload()
            return []

        s = self.spec
        self.ammo -= 1
        self.cooldown = s["cooldown"]
        ox, oy = owner.muzzle()

        shots = []
        for _ in range(s["pellets"]):
            a = owner.aim + math.radians(random.uniform(-s["spread"], s["spread"]))
            sp = s["speed"] * random.uniform(0.97, 1.03)
            shots.append(Projectile(
                ox, oy, math.cos(a) * sp, math.sin(a) * sp, s["damage"], owner,
                s["life"], s["color"], width=s["width"], trail=s["trail"],
                gravity=s["gravity"]))

        # recul + flash de bouche
        owner.vx -= math.cos(owner.aim) * s["recoil"]
        owner.vy -= math.sin(owner.aim) * s["recoil"] * 0.6
        for _ in range(4):
            a = owner.aim + random.uniform(-0.5, 0.5)
            v = random.uniform(120, 300)
            owner.fx.append(Particle(ox, oy, math.cos(a) * v, math.sin(a) * v,
                                     0.12, (255, 235, 160), size=3))

        if self.ammo == 0:
            self.start_reload()
        return shots
