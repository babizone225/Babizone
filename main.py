"""Babizone - Abidjan Militia
Menus (jouer / personnage / paramètres), 4 arènes, niveaux de bots, multi local et en ligne.
"""
import asyncio
import json
import traceback
import webbrowser
import math
import os
import random
import sys
import pygame

try:
    import net
except Exception:          # navigateur (mobile) : pas de réseau direct
    net = None
from settings import *
from arenas import ARENAS, ARENA_ORDER
from map import GameMap, Pickup, PICKUP_KINDS
from player import (Player, HumanController, BotBrain, Intent, OUTFITS, SKINS, HAIRS,
                    WEAPON_CHOICES, default_profile, random_profile, palette_of)
from sprites import HAIR_COLORS, ACCESSORIES, BEARDS, draw_character
from weapon import WEAPON_SPECS, WEAPON_TIER
from audio import Audio
from drops import DroppedWeapon, DROP_TTL
from touch import TouchControls
from projectile import Particle, Projectile
from ui import Form, Row, draw_text, VKeyboard

# Dans le .exe, le profil et le journal d'erreurs sont enregistrés À CÔTÉ de l'exécutable (pas dans un dossier temporaire)
BASE_DIR = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.path.dirname(os.path.abspath(__file__))
SAVE_FILE = os.path.join(BASE_DIR, "babizone_profil.json")
CRASH_FILE = os.path.join(BASE_DIR, "babizone_erreur.txt")
BOT_NAMES = ["Yao", "Awa", "Kouadio", "Aya", "Zadi", "Koffi", "Adjoua"]
LEVELS = [
    dict(name="Facile", skill=(0.30, 0.50), reaction=0.70, dmg=0.7, bots=2),
    dict(name="Normal", skill=(0.50, 0.75), reaction=0.35, dmg=1.0, bots=3),
    dict(name="Difficile", skill=(0.80, 0.97), reaction=0.12, dmg=1.15, bots=4),
]
NET_RATE = 1 / 30.0
WEB = sys.platform == "emscripten"          # version navigateur (mobile) : pas de réseau direct
MAX_DROPS = 10
NET_SOUNDS = ("shot_nouchi", "shot_coupe", "shot_dozo", "shot_sniper", "hit", "die", "pickup", "weapon", "reload", "wall")


def clean_profile(d):
    """Valide un profil (venant d'un fichier ou du réseau)."""
    p = default_profile("Joueur")
    try:
        p["name"] = str(d.get("name", "Joueur"))[:12] or "Joueur"
        p["outfit"] = int(d.get("outfit", 0)) % len(OUTFITS)
        p["skin"] = int(d.get("skin", 2)) % len(SKINS)
        p["hair"] = int(d.get("hair", 1)) % len(HAIRS)
        p["hcol"] = int(d.get("hcol", 0)) % len(HAIR_COLORS)
        p["acc"] = int(d.get("acc", 0)) % len(ACCESSORIES)
        p["beard"] = int(d.get("beard", 0)) % len(BEARDS)
        p["w1"] = d.get("w1") if d.get("w1") in WEAPON_CHOICES else "coupe"
        p["w2"] = d.get("w2") if d.get("w2") in WEAPON_CHOICES else "nouchi"
    except (TypeError, ValueError, AttributeError):
        pass
    return p


def make_keys(solo=True):
    k = pygame
    keys = dict(left=[k.K_q, k.K_a], right=[k.K_d], jet=[k.K_z, k.K_w, k.K_SPACE],
                reload=[k.K_r], switch=[k.K_e], fire=[k.K_f], pickup=[k.K_g])
    if solo:
        keys["left"].append(k.K_LEFT)
        keys["right"].append(k.K_RIGHT)
        keys["jet"].append(k.K_UP)
    return keys


class Camera:
    def __init__(self, vw, vh):
        self.w, self.h = vw, vh
        self.x = self.y = 0.0

    def _clamp(self):
        self.x = max(0, min(WORLD_W - self.w, self.x))
        self.y = max(0, min(WORLD_H - self.h, self.y))

    def snap(self, rect):
        self.x, self.y = rect.centerx - self.w / 2, rect.centery - self.h / 2
        self._clamp()

    def follow(self, rect, dt):
        k = min(1.0, 8 * dt)
        self.x += (rect.centerx - self.w / 2 - self.x) * k
        self.y += (rect.centery - self.h / 2 - self.y) * k
        self._clamp()


class Game:
    # ======================================================================
    #  Initialisation
    # ======================================================================
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Babizone - Abidjan Militia")
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.SCALED)
        self.clock = pygame.time.Clock()
        self.f_s = pygame.font.Font(None, 22)
        self.f_m = pygame.font.Font(None, 32)
        self.f_l = pygame.font.Font(None, 64)
        self.f_xl = pygame.font.Font(None, 128)
        self.fonts = (self.f_s, self.f_m, self.f_l)

        self.maps = {}
        self.map = self.get_map("yop")
        self.profile, self.settings = self.load_save()
        self.audio = Audio()
        self.audio.configure(self.settings["sfx"], self.settings["music"] == 0)
        self.touch = TouchControls(self.fonts)
        self.touch_seen = sys.platform in ("android", "ios")
        self.touch_mode = False
        self.vkb = None
        self.out_pickup = False
        self.drops = []
        self.over_rects = []
        self.pause_rects = []
        self.update_touch_mode()

        self.state = "menu"
        self.t = 0.0
        self.paused = False
        self.msg = ("", 0.0)
        self.net_role = None
        self.host = None
        self.conn = None
        self.clients = {}
        self.pending = []
        self.pub = None
        self.lobby_names = []
        self.lobby_arena = "yop"
        self.lobby_wait = 0.0
        self.rank_rows = []
        self.cfg = {}
        self.events = []
        self.views = []
        self.players = []
        self.controllers = {}
        self.brains = {}
        self.projectiles, self.particles, self.pickups, self.feed = [], [], [], []
        self.build_forms()
        pygame.mouse.set_visible(True)

    def get_map(self, key):
        if key not in self.maps:
            self.draw_wait("Chargement de l'arène...")      # la construction du décor peut prendre quelques secondes
            self.maps[key] = GameMap(key)
        return self.maps[key]

    def set_msg(self, txt, secs=4.0):
        self.msg = (txt, secs)

    # ----- profil -------------------------------------------------------------------
    def load_save(self):
        data = {}
        try:
            with open(SAVE_FILE, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError):
            pass
        st = dict(sfx=3, music=0, touch=0)         # sfx : 0..4 | music : 0 oui, 1 non | touch : 0 auto, 1 oui, 2 non
        try:
            for k, hi in (("sfx", 4), ("music", 1), ("touch", 2)):
                st[k] = max(0, min(hi, int(data.get("settings", {}).get(k, st[k]))))
        except (TypeError, ValueError, AttributeError):
            pass
        return clean_profile(data if isinstance(data, dict) else {}), st

    def save_profile(self):
        try:
            with open(SAVE_FILE, "w", encoding="utf-8") as f:
                json.dump(dict(self.profile, settings=self.settings), f, ensure_ascii=False)
        except OSError:
            pass

    def update_touch_mode(self):
        t = self.settings["touch"]
        self.touch_mode = (t == 1) or (t == 0 and self.touch_seen)

    # ----- formulaires ----------------------------------------------------------------
    def build_forms(self):
        self.menu_form = Form([
            Row("play", "JOUER", "button"),
            Row("perso", "MON PERSONNAGE", "button"),
            Row("params", "PARAMÈTRES", "button"),
            Row("avis", "DONNER MON AVIS", "button", visible=lambda: bool(FEEDBACK_URL) and not WEB),
            Row("quit", "QUITTER", "button"),
        ], self.fonts, row_w=460)

        def mode():
            return self.setup_form.idx("mode")

        def joining():
            return mode() == 2 and self.setup_form.idx("role") == 1

        self.setup_form = Form([
            Row("mode", "Mode", options=["Solo", "Multi local (2 joueurs)"] + ([] if WEB else ["Multi en ligne"])),
            Row("role", "En ligne", options=["Héberger une partie", "Rejoindre un ami"],
                visible=lambda: mode() == 2),
            Row("level", "Niveau des bots", options=[l["name"] for l in LEVELS], index=1,
                visible=lambda: not joining()),
            Row("arena", "Arène", options=[ARENAS[k]["name"] for k in ARENA_ORDER],
                visible=lambda: not joining()),
            Row("bots", "Nombre de bots", options=[0, 1, 2, 3], index=2,
                visible=lambda: mode() >= 1 and not joining()),
            Row("code", "Code ou IP de l'ami", "text", maxlen=22, visible=joining),
            Row("go", lambda: ["LANCER LA PARTIE", "LANCER LA PARTIE", "CRÉER LE SALON"][mode()]
                if not joining() else "REJOINDRE", "button"),
            Row("back", "RETOUR", "button"),
        ], self.fonts, row_w=740, row_h=46, gap=8)

        self.perso_form = Form([
            Row("outfit", "Tenue", options=[o[0] for o in OUTFITS]),
            Row("skin", "Teint", options=[s[0] for s in SKINS]),
            Row("hair", "Coiffure", options=HAIRS),
            Row("hcol", "Cheveux", options=[c[0] for c in HAIR_COLORS]),
            Row("acc", "Accessoire", options=ACCESSORIES),
            Row("beard", "Barbe", options=BEARDS),
            Row("w1", "Arme 1", options=[WEAPON_SPECS[k]["name"] for k in WEAPON_CHOICES]),
            Row("w2", "Arme 2", options=[WEAPON_SPECS[k]["name"] for k in WEAPON_CHOICES]),
            Row("ok", "VALIDER", "button"),
        ], self.fonts, row_w=600, row_h=46, gap=8, cx=900)

        self.params_form = Form([
            Row("name", "Pseudo", "text", maxlen=12),
            Row("sfx", "Effets sonores", options=["Muet", "25 %", "50 %", "75 %", "100 %"], index=3),
            Row("music", "Musique", options=["Oui", "Non"]),
            Row("touch", "Commandes tactiles", options=["Auto", "Toujours", "Jamais"]),
            Row("ok", "ENREGISTRER", "button"),
        ], self.fonts, row_w=680)

        self.lobby_host_form = Form([
            Row("start", "LANCER LA PARTIE", "button"),
            Row("back", "ANNULER", "button"),
        ], self.fonts, row_w=460, row_h=46, gap=8)
        self.lobby_client_form = Form([Row("back", "QUITTER LE SALON", "button")],
                                      self.fonts, row_w=460, row_h=46)

    def enter_perso(self):
        p = self.profile
        f = self.perso_form
        f.row("outfit").index, f.row("skin").index, f.row("hair").index = p["outfit"], p["skin"], p["hair"]
        f.row("hcol").index = p["hcol"]
        f.row("acc").index, f.row("beard").index = p["acc"], p["beard"]
        f.row("w1").index = WEAPON_CHOICES.index(p["w1"])
        f.row("w2").index = WEAPON_CHOICES.index(p["w2"])
        f.sel = 0
        self.state = "perso"

    def leave_perso(self):
        f = self.perso_form
        self.profile.update(outfit=f.idx("outfit"), skin=f.idx("skin"), hair=f.idx("hair"), hcol=f.idx("hcol"),
                            acc=f.idx("acc"), beard=f.idx("beard"),
                            w1=WEAPON_CHOICES[f.idx("w1")], w2=WEAPON_CHOICES[f.idx("w2")])
        self.save_profile()
        self.state = "menu"

    def enter_params(self):
        self.params_form.row("name").text = self.profile["name"]
        self.params_form.row("name").fresh = True
        for k in ("sfx", "music", "touch"):
            self.params_form.row(k).index = self.settings[k]
        self.params_form.sel = 0
        self.state = "params"

    def leave_params(self, save=True):
        if save:
            self.profile["name"] = self.params_form.row("name").text.strip() or "Joueur"
            self.settings = {k: self.params_form.idx(k) for k in ("sfx", "music", "touch")}
            self.audio.configure(self.settings["sfx"], self.settings["music"] == 0)
            self.update_touch_mode()
            self.save_profile()
        self.state = "menu"

    # ======================================================================
    #  Réseau : fermeture, sorties vers le menu
    # ======================================================================
    def net_close(self, why=None):
        for c in self.clients.values():
            if why:
                c["conn"].send({"t": "bye", "why": why})
            c["conn"].close()
        for c in self.pending:
            c.close()
        self.clients, self.pending = {}, []
        if self.host:
            self.host.close()
        if self.conn:
            self.conn.close()
        self.host = self.conn = None
        self.net_role = None

    def to_menu(self, msg=None):
        self.net_close("L'hôte a quitté la partie." if self.net_role == "host" or self.state == "lobby_host" else None)
        self.state = "menu"
        pygame.mouse.set_visible(True)
        if msg:
            self.set_msg(msg)

    def quit(self):
        self.net_close()
        pygame.quit()
        sys.exit()

    # ======================================================================
    #  Démarrage d'une partie
    # ======================================================================
    @staticmethod
    def unique_name(name, used):
        base, n = name, 2
        while name in used:
            name, n = f"{base}{n}", n + 1
        used.add(name)
        return name

    def new_player(self, profile, is_bot=False, used=None):
        name = self.unique_name(profile["name"], used) if used is not None else profile["name"]
        p = Player(name, palette_of(profile), is_bot=is_bot, loadout=(profile["w1"], profile["w2"]))
        p.profile = dict(profile, name=name)
        return p

    def reset_match_state(self):
        self.state = "play"
        self.paused = False
        self.time_left = float(MATCH_TIME)
        self.projectiles, self.particles, self.pickups, self.feed = [], [], [], []
        self.drops = []
        self.pickup_timer = 2.0
        self.events = []
        self.snap_timer = 0.0
        self.controllers, self.brains, self.views = {}, {}, []
        pygame.mouse.set_visible(False)

    def make_views(self, humans):
        self.views = []
        if len(humans) == 1:
            cam = Camera(SCREEN_W, SCREEN_H)
            cam.snap(humans[0].rect)
            self.views.append((humans[0], cam, self.screen.subsurface(pygame.Rect(0, 0, SCREEN_W, SCREEN_H))))
        else:
            half = SCREEN_W // 2
            for i, p in enumerate(humans):
                rect = pygame.Rect(i * half, 0, half, SCREEN_H)
                cam = Camera(rect.w, rect.h)
                cam.snap(p.rect)
                self.views.append((p, cam, self.screen.subsurface(rect)))

    def start_match(self, cfg):
        """cfg : mode ('solo'|'local'|'host'), arena, level, bots, friends (ids)."""
        self.cfg = cfg
        mode = cfg["mode"]
        lvl = LEVELS[cfg["level"]]
        self.map = self.get_map(cfg["arena"])
        self.bot_dmg = lvl["dmg"]
        self.net_role = "host" if mode == "host" else None
        self.reset_match_state()

        used = set()
        p1 = self.new_player(self.profile, used=used)
        players = [p1]
        self.controllers[p1] = self.make_controller(solo=(mode != "local"))
        humans = [p1]

        if mode == "local":
            k = pygame
            keys2 = dict(left=[k.K_LEFT], right=[k.K_RIGHT], jet=[k.K_UP],
                         aim_ccw=[k.K_o], aim_cw=[k.K_p], aim_flip=[k.K_l],
                         fire=[k.K_RCTRL, k.K_RETURN], reload=[k.K_RSHIFT], switch=[k.K_m], pickup=[k.K_n])
            prof2 = dict(default_profile("Joueur 2"), outfit=3, skin=1, hair=2, hcol=1, w1="dozo")
            p2 = self.new_player(prof2, used=used)
            players.append(p2)
            humans.append(p2)
            self.controllers[p2] = HumanController(keys2, use_mouse=False)
            self.controllers[p2].pickup_label = "N"

        if mode == "host":
            for cid in cfg["friends"]:
                c = self.clients.get(cid)
                if not c or c["conn"].closed:
                    continue
                p = self.new_player(c["profile"], used=used)
                p.cid, p.remote = cid, Intent()
                c["player"] = p
                players.append(p)

        n_bots = lvl["bots"] if mode == "solo" else cfg["bots"]
        names = random.sample(BOT_NAMES, min(n_bots, len(BOT_NAMES)))
        for nm in names:
            b = self.new_player(random_profile(nm), is_bot=True, used=used)
            players.append(b)
            self.brains[b] = BotBrain(random.uniform(*lvl["skill"]), lvl["reaction"])
        self.players = players

        spawns = self.map.spawn_points[:]
        random.shuffle(spawns)
        for p, sp in zip(players, spawns):
            p.respawn(sp)
        self.make_views(humans)

        if mode == "host":
            infos = [dict(name=p.name, profile=p.profile, bot=p.is_bot) for p in players]
            for cid, c in self.clients.items():
                p = c.get("player")
                if p in players:
                    c["conn"].send({"t": "start", "arena": cfg["arena"], "you": players.index(p),
                                    "players": infos, "tl": MATCH_TIME})

    def client_start(self, m):
        self.net_role = "client"
        self.map = self.get_map(m["arena"])
        self.reset_match_state()
        players = []
        for info in m["players"]:
            prof = clean_profile(info["profile"])
            p = Player(info["name"], palette_of(prof), is_bot=info["bot"], loadout=(prof["w1"], prof["w2"]))
            players.append(p)
        self.players = players
        me = players[m["you"]]
        self.controllers[me] = self.make_controller(solo=True)
        self.time_left = float(m.get("tl", MATCH_TIME))
        self.out_reload = self.out_switch = self.out_pickup = False
        self.out_timer = 0.0
        self.make_views([me])

    # ======================================================================
    #  Effets visuels (partagés entre simulation, hôte et clients)
    # ======================================================================
    def make_burst(self, kind, x, y, color=None):
        out = self.particles
        if kind == "wall":
            for _ in range(5):
                a, v = random.uniform(0, math.tau), random.uniform(60, 240)
                out.append(Particle(x, y, math.cos(a) * v, math.sin(a) * v, 0.25, (255, 220, 120), size=3))
        elif kind == "blood":
            for _ in range(6):
                a, v = random.uniform(0, math.tau), random.uniform(60, 220)
                out.append(Particle(x, y, math.cos(a) * v, math.sin(a) * v, 0.35, (210, 40, 40), size=3, gravity=500))
        elif kind == "die":
            col = tuple(color) if color else (210, 40, 40)
            for _ in range(28):
                a, v = random.uniform(0, math.tau), random.uniform(80, 420)
                c = random.choice((col, (210, 40, 40), (240, 240, 240)))
                out.append(Particle(x, y, math.cos(a) * v, math.sin(a) * v - 120,
                                    random.uniform(0.5, 1.0), c, size=5, gravity=900))
        elif kind == "pickup":
            for _ in range(12):
                a, v = random.uniform(0, math.tau), random.uniform(60, 220)
                out.append(Particle(x, y, math.cos(a) * v, math.sin(a) * v, 0.5, (255, 240, 140), size=4))

    def burst(self, kind, x, y, color=None):
        self.make_burst(kind, x, y, color)
        if self.net_role == "host":
            self.events.append(["burst", kind, int(x), int(y), list(color) if color else None])

    def add_feed(self, txt, color=WHITE, to_clients=True):
        self.feed.insert(0, [txt, 5.0, tuple(color)])
        del self.feed[5:]
        if self.net_role == "host" and to_clients:
            self.events.append(["feed", txt, list(color)])

    # ======================================================================
    #  Événements clavier / souris
    # ======================================================================
    def current_form(self):
        return {"menu": self.menu_form, "setup": self.setup_form, "perso": self.perso_form,
                "params": self.params_form, "lobby_host": self.lobby_host_form,
                "lobby_client": self.lobby_client_form}.get(self.state)

    def fh(self, form, e):
        """Traite un événement pour un formulaire, avec les petits bruitages de menu."""
        before = form.sel
        act = form.handle(e)
        if act:
            self.audio.play("click")
        elif form.sel != before:
            self.audio.play("move")
        elif form.changed:
            self.audio.play("click")
        form.changed = False
        return act

    def handle_events(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                self.quit()
            if self.vkb:                                   # clavier à l'écran ouvert
                if self.vkb.handle(e):
                    self.vkb = None
                    self.audio.play("click")
                continue
            if e.type == getattr(pygame, "FINGERDOWN", -1) and not self.touch_seen:
                self.touch_seen = True                      # un doigt a touché l'écran : mode tactile
                self.update_touch_mode()
            getattr(self, "ev_" + self.state)(e)
            form = self.current_form()
            if form and form.kb_request:
                row, form.kb_request = form.kb_request, None
                if self.touch_mode:
                    self.vkb = VKeyboard(row, self.fonts)

    # ----- sons -------------------------------------------------------------------------
    def listeners(self):
        return [p.rect.center for p, _, _ in self.views if p.alive]

    def sound(self, name, x=None, y=None, vol=1.0, net=True):
        """Joue un son (positionnel si x, y donnés) et le signale aux amis connectés."""
        if x is None:
            self.audio.play(name, vol)
            return
        self.audio.play_at(name, x, y, self.listeners(), vol)
        if net and self.net_role == "host" and name in NET_SOUNDS:
            self.events.append(["sfx", name, int(x), int(y)])

    def update_music(self):
        if self.state == "play":
            want = "battle"
        elif self.state in ("menu", "setup", "perso", "params", "lobby_host", "lobby_client"):
            want = "menu"
        else:
            want = None
        self.audio.music(want)

    # ----- contrôleurs (clavier/souris ou tactile) ---------------------------------------------
    def make_controller(self, solo=True, label="G"):
        if self.touch_mode:
            return self.touch
        c = HumanController(make_keys(solo=solo), use_mouse=True)
        c.pickup_label = label
        return c

    def sync_controller(self):
        """Bascule clavier <-> tactile en cours de partie (premier toucher détecté)."""
        if not self.views:
            return
        me = self.views[0][0]
        cur = self.controllers.get(me)
        if cur is None:
            return
        is_touch = isinstance(cur, TouchControls)
        solo = self.cfg.get("mode") != "local" if self.net_role != "client" else True
        if self.touch_mode and not is_touch:
            self.controllers[me] = self.touch
        elif not self.touch_mode and is_touch:
            self.controllers[me] = self.make_controller(solo=solo)

    def ev_menu(self, e):
        act = self.fh(self.menu_form, e)
        if act == "play":
            self.state = "setup"
        elif act == "perso":
            self.enter_perso()
        elif act == "params":
            self.enter_params()
        elif act == "avis":
            try:
                webbrowser.open(FEEDBACK_URL)
            except Exception:
                pass
        elif act in ("quit", "__back__"):
            self.quit()

    def ev_setup(self, e):
        act = self.fh(self.setup_form, e)
        f = self.setup_form
        if act in ("back", "__back__"):
            self.state = "menu"
        elif act == "go":
            mode = f.idx("mode")
            joining = mode == 2 and f.idx("role") == 1
            arena = ARENA_ORDER[f.idx("arena")]
            if mode == 0:
                self.start_match(dict(mode="solo", arena=arena, level=f.idx("level"), bots=0, friends=[]))
            elif mode == 1:
                self.start_match(dict(mode="local", arena=arena, level=f.idx("level"),
                                      bots=f.val("bots"), friends=[]))
            elif joining:
                self.try_join(f.val("code"))
            else:
                self.open_lobby(arena)

    def ev_perso(self, e):
        act = self.fh(self.perso_form, e)
        if act in ("ok", "__back__"):
            self.leave_perso()

    def ev_params(self, e):
        act = self.fh(self.params_form, e)
        if act == "ok":
            self.leave_params(True)
        elif act == "__back__":
            self.leave_params(False)

    def ev_lobby_host(self, e):
        act = self.fh(self.lobby_host_form, e)
        if act in ("back", "__back__"):
            self.to_menu()
        elif act == "start":
            f = self.setup_form
            self.start_match(dict(mode="host", arena=ARENA_ORDER[f.idx("arena")], level=f.idx("level"),
                                  bots=f.val("bots"), friends=list(self.clients.keys())))

    def ev_lobby_client(self, e):
        act = self.fh(self.lobby_client_form, e)
        if act in ("back", "__back__"):
            self.to_menu()

    def ev_play(self, e):
        if self.touch_mode:
            self.touch.handle(e)
            if self.touch.consume("pause") and self.net_role is None:
                self.paused = not self.paused
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                self.to_menu()
            elif e.key in (pygame.K_PAUSE, pygame.K_t) and self.net_role is None:
                self.paused = not self.paused
        elif self.paused and e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for name, rect in self.pause_rects:
                if rect.collidepoint(e.pos):
                    self.audio.play("click")
                    if name == "resume":
                        self.paused = False
                    else:
                        self.to_menu()

    def ev_gameover(self, e):
        action = None
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_RETURN, pygame.K_KP_ENTER) and self.net_role != "client":
                action = "again"
            elif e.key == pygame.K_ESCAPE:
                action = "menu"
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for name, rect in self.over_rects:
                if rect.collidepoint(e.pos):
                    action = name
        if action == "again":
            self.audio.play("click")
            if self.net_role == "host":
                self.cfg["friends"] = [cid for cid, c in self.clients.items() if not c["conn"].closed]
            self.start_match(self.cfg)
        elif action == "menu":
            self.audio.play("click")
            self.to_menu()

    # ======================================================================
    #  Salon en ligne
    # ======================================================================
    def open_lobby(self, arena):
        try:
            self.host = net.Host(net.PORT)
        except OSError:
            self.set_msg("Impossible d'ouvrir le port %d (déjà utilisé ?)" % net.PORT)
            return
        self.clients, self.pending = {}, []
        self.next_cid = 1
        self.lan_ip = net.local_ip()
        self.local_ips = [ip for ip in net.all_local_ips() if ip != self.lan_ip][:3]
        self.pub = net.PublicIP()
        self.lobby_host_form.sel = 0
        self.state = "lobby_host"

    def try_join(self, text):
        target = net.parse_target(text)
        if not target:
            self.set_msg("Code invalide. Exemple : GAXAA-UXTLK ou 192.168.1.20")
            return
        self.draw_wait("Connexion à %s:%d ..." % target)
        try:
            self.conn = net.connect(*target, timeout=4.0)
        except OSError:
            self.set_msg("Connexion impossible. Vérifie le code, l'hôte et le pare-feu.")
            return
        self.conn.send({"t": "hello", "profile": self.profile})
        self.net_role = "client"
        self.lobby_names, self.lobby_wait = [], 0.0
        self.lobby_client_form.sel = 0
        self.state = "lobby_client"

    def lobby_broadcast(self):
        names = [self.profile["name"] + " (hôte)"] + [c["name"] for c in self.clients.values()]
        arena = ARENA_ORDER[self.setup_form.idx("arena")]
        for c in self.clients.values():
            c["conn"].send({"t": "lobby", "names": names, "arena": arena})

    def update_lobby_host(self, dt):
        changed = False
        self.pending += self.host.accept()
        for conn in self.pending[:]:
            for m in conn.poll():
                if m.get("t") == "hello":
                    self.pending.remove(conn)
                    if len(self.clients) >= net.MAX_FRIENDS:
                        conn.send({"t": "bye", "why": "Le salon est plein."})
                        conn.close()
                    else:
                        prof = clean_profile(m.get("profile", {}))
                        self.clients[self.next_cid] = dict(conn=conn, name=prof["name"], profile=prof, player=None)
                        self.next_cid += 1
                        changed = True
                    break
            if conn.closed and conn in self.pending:
                self.pending.remove(conn)
        for cid in list(self.clients):
            c = self.clients[cid]
            c["conn"].poll()
            if c["conn"].closed:
                del self.clients[cid]
                changed = True
        if changed or int(self.t * 2) != int((self.t - dt) * 2):
            self.lobby_broadcast()

    def update_lobby_client(self, dt):
        self.lobby_wait += dt
        for m in self.conn.poll():
            self.lobby_wait = 0.0
            t = m.get("t")
            if t == "lobby":
                self.lobby_names, self.lobby_arena = m["names"], m["arena"]
            elif t == "start":
                self.client_start(m)
                return
            elif t == "bye":
                self.to_menu(m.get("why", "L'hôte a fermé le salon."))
                return
        if self.conn.closed:
            self.to_menu("Connexion perdue.")
        elif self.lobby_wait > 8:
            self.to_menu("L'hôte ne répond pas.")

    # ======================================================================
    #  Hôte : commandes des amis et instantanés
    # ======================================================================
    def host_receive(self):
        for conn in self.host.accept():
            conn.send({"t": "bye", "why": "Partie déjà commencée."})
            conn.close()
        for cid, c in list(self.clients.items()):
            p = c.get("player")
            for m in c["conn"].poll():
                if m.get("t") == "in" and p is not None and getattr(p, "remote", None) is not None:
                    it = p.remote
                    it.move = max(-1.0, min(1.0, float(m.get("m", 0))))
                    it.jet, it.fire = bool(m.get("j")), bool(m.get("f"))
                    it.aim = float(m.get("a", 0))
                    it.reload = it.reload or bool(m.get("r"))
                    it.switch = it.switch or bool(m.get("s"))
                    it.pickup = it.pickup or bool(m.get("g"))
            if c["conn"].closed:                       # l'ami part : un bot prend sa place
                del self.clients[cid]
                if p is not None and p in self.players:
                    p.is_bot = True
                    p.remote = None
                    self.brains[p] = BotBrain(0.6, 0.35)
                    self.add_feed(f"{p.name} a quitté la partie", (200, 200, 210))

    def host_send_snapshot(self):
        snap = {"t": "snap", "tl": round(self.time_left, 1),
                "p": [p.net_pack() for p in self.players],
                "pr": [[int(pr.x), int(pr.y), int(pr.vx), int(pr.vy), *pr.color, pr.width, int(pr.trail * 1000)]
                       for pr in self.projectiles],
                "pk": [[pk.kind, pk.rect.centerx, pk.rect.centery] for pk in self.pickups],
                "dr": [[d.key, d.rect.centerx, d.rect.centery, d.ammo] for d in self.drops],
                "ev": self.events}
        self.events = []
        for c in self.clients.values():
            c["conn"].send(snap)

    # ======================================================================
    #  Simulation (solo / local / hôte)
    # ======================================================================
    def pick_spawn(self, me):
        enemies = [p for p in self.players if p is not me and p.alive]
        best, best_d = None, -1
        for sp in random.sample(self.map.spawn_points, min(5, len(self.map.spawn_points))):
            d = min((math.hypot(sp[0] - e.rect.centerx, sp[1] - e.rect.centery) for e in enemies), default=9999)
            if d > best_d:
                best, best_d = sp, d
        return best

    def update_play(self, dt):
        if self.net_role == "client":
            return self.update_client(dt)
        if self.paused:
            return
        host = self.net_role == "host"
        if host:
            self.host_receive()
        self.sync_controller()
        self.time_left -= dt

        cam_of = {p: cam for p, cam, _ in self.views}
        for p in self.players:
            if p.alive:
                if p.is_bot:
                    others = [o for o in self.players if o is not p]
                    it = self.brains[p].intent(p, others, self.map, self.pickups, dt, self.drops)
                elif p in self.controllers:
                    cam = cam_of[p]
                    sh = p.shoulder()
                    it = self.controllers[p].intent(p, (sh[0] - cam.x, sh[1] - cam.y), dt)
                elif getattr(p, "remote", None) is not None:
                    it = p.remote
                else:
                    it = Intent()
                shots = p.update(dt, it, self.map)
                if shots and not self.map.line_clear(p.shoulder(), p.muzzle()):
                    shots = []                      # canon collé contre un mur : la balle ne traverse pas
                self.projectiles.extend(shots)
                if shots:
                    self.sound("shot_" + p.weapon.key, *p.rect.center)
                for ev in p.events:                          # jet, reload, empty
                    self.sound(ev, *p.rect.center, vol=0.7 if ev == "jet" else 1.0)
                p.events.clear()
                if getattr(p, "remote", None) is not None:
                    p.remote.reload = p.remote.switch = p.remote.pickup = False
            else:
                p.respawn_timer -= dt
                if p.respawn_timer <= 0:
                    p.respawn(self.pick_spawn(p))
                    if not p.is_bot:
                        self.sound("spawn", *p.rect.center)
            self.particles.extend(p.fx)
            p.fx.clear()

        for pr in self.projectiles:
            ev = pr.update(dt, self.map.solids, self.players)
            if ev is None:
                continue
            kind, data = ev
            if kind == "wall":
                self.burst("wall", *data)
                self.sound("wall", *data)
            else:
                victim = data
                mult = self.bot_dmg if pr.owner.is_bot else 1.0
                killed = victim.take_damage(pr.damage * mult, pr.angle)
                self.burst("blood", pr.x, pr.y)
                self.sound("hit", pr.x, pr.y)
                if killed:
                    pr.owner.kills += 1
                    self.burst("die", victim.rect.centerx, victim.rect.centery, victim.pal["tee"])
                    self.sound("die", *victim.rect.center)
                    self.drop_loot(victim)
                    self.add_feed(f"{pr.owner.name} a sorti {victim.name}", ORANGE)
        self.projectiles = [p for p in self.projectiles if not p.dead]

        self.pickup_timer -= dt
        if self.pickup_timer <= 0 and len(self.pickups) < MAX_PICKUPS:
            self.pickup_timer = PICKUP_INTERVAL
            used = [pk.rect.center for pk in self.pickups]
            free = [pt for pt in self.map.pickup_points if pt not in used]
            if free:
                kind = random.choices(["garba", "alloco", "gnamankoudji", "caisse"], [3, 3, 2, 2])[0]
                self.pickups.append(Pickup(kind, random.choice(free)))
        for pk in self.pickups:
            pk.update(dt)
            for p in self.players:
                if p.alive and p.rect.colliderect(pk.rect) and p.apply_pickup(pk.kind):
                    pk.dead = True
                    self.burst("pickup", *pk.rect.center)
                    self.sound("pickup", *pk.rect.center)
                    if p in self.controllers:
                        self.add_feed(PICKUP_KINDS[pk.kind], (255, 240, 140), to_clients=False)
                    break
        self.pickups = [pk for pk in self.pickups if not pk.dead]

        self.handle_weapon_pickups()
        for d in self.drops:
            d.update(dt, self.map.solids)
        self.drops = [d for d in self.drops if not d.dead]

        self.tick_effects(dt)
        for p, cam, _ in self.views:
            cam.follow(p.rect, dt)

        if host:
            self.snap_timer += dt
            if self.snap_timer >= NET_RATE:
                self.snap_timer = 0.0
                self.host_send_snapshot()

        if self.time_left <= 0 or any(p.kills >= KILL_LIMIT for p in self.players):
            rows = [(p.name, p.kills, p.deaths, p.pal["tee"])
                    for p in sorted(self.players, key=lambda q: (-q.kills, q.deaths))]
            self.finish(rows)

    def drop_loot(self, victim):
        """Le joueur éliminé laisse tomber son arme la plus puissante."""
        w = max(victim.weapons, key=lambda x: WEAPON_TIER[x.key])
        ammo = max(w.ammo, w.spec["mag"] // 2)
        self.drops.append(DroppedWeapon(w.key, ammo, victim.rect.centerx, victim.rect.centery - 6,
                                        vx=random.uniform(-140, 140), vy=-260))
        del self.drops[:-MAX_DROPS]

    def near_drop(self, me):
        if me is None or not me.alive:
            return None
        cand = [d for d in self.drops if not d.dead and d.reachable_by(me)]
        return min(cand, key=lambda d: (d.rect.centerx - me.rect.centerx) ** 2 + (d.rect.centery - me.rect.centery) ** 2,
                   default=None)

    def handle_weapon_pickups(self):
        for p in self.players:
            if not (p.alive and p.want_pickup):
                continue
            p.want_pickup = False
            d = self.near_drop(p)
            if d is None:
                continue
            old = p.take_weapon(d)
            d.dead = True
            if old is not None:                              # échange : l'ancienne arme tombe au sol
                self.drops.append(DroppedWeapon(old.key, old.ammo, p.rect.centerx, p.rect.centery - 4,
                                                vx=random.uniform(-90, 90), vy=-200, owner=p, delay=1.5))
                del self.drops[:-MAX_DROPS]
            self.sound("weapon", *p.rect.center)
            self.burst("pickup", *p.rect.center)
            if p in self.controllers:
                self.add_feed("Arme ramassée : " + WEAPON_SPECS[d.key]["name"], (255, 240, 140), to_clients=False)
        self.drops = [d for d in self.drops if not d.dead]

    def tick_effects(self, dt):
        for pt in self.particles:
            pt.update(dt)
        self.particles = [pt for pt in self.particles if not pt.dead]
        for f in self.feed:
            f[1] -= dt
        self.feed = [f for f in self.feed if f[1] > 0]

    def finish(self, rows):
        self.rank_rows = rows
        me = self.views[0][0].name if self.views else None
        self.audio.play("win" if rows and rows[0][0] == me else "lose")
        self.state = "gameover"
        pygame.mouse.set_visible(True)
        if self.net_role == "host":
            self.host_send_snapshot()
            for c in self.clients.values():
                c["conn"].send({"t": "end", "rank": [[n, k, d, list(col)] for n, k, d, col in rows]})

    def update_gameover(self, dt):
        if self.net_role == "host":
            for cid, c in list(self.clients.items()):
                c["conn"].poll()
                if c["conn"].closed:
                    del self.clients[cid]
        elif self.net_role == "client":
            for m in self.conn.poll():
                if m.get("t") == "start":
                    self.client_start(m)
                    return
                if m.get("t") == "bye":
                    self.to_menu(m.get("why", "L'hôte a quitté."))
                    return
            if self.conn.closed:
                self.to_menu("Connexion perdue.")

    # ======================================================================
    #  Client en ligne
    # ======================================================================
    def update_client(self, dt):
        me, cam, _ = self.views[0]
        for m in self.conn.poll():
            t = m.get("t")
            if t == "snap":
                self.apply_snapshot(m)
            elif t == "end":
                self.finish([(n, k, d, tuple(col)) for n, k, d, col in m["rank"]])
                return
            elif t == "bye":
                self.to_menu(m.get("why", "L'hôte a quitté."))
                return
        if self.conn.closed:
            self.to_menu("Connexion perdue.")
            return

        self.sync_controller()
        for p in self.players:
            p.net_step(dt)
            if p.alive and p.thrusting:
                p.emit_flame()
                p.jet_timer -= dt
                if p.jet_timer <= 0:
                    p.jet_timer = 0.11
                    self.sound("jet", *p.rect.center, vol=0.7, net=False)
            self.particles.extend(p.fx)
            p.fx.clear()
        for pr in self.projectiles:
            pr.x += pr.vx * dt
            pr.y += pr.vy * dt
        for pk in self.pickups:
            pk.update(dt)
        self.tick_effects(dt)
        cam.follow(me.rect, dt)

        sh = me.shoulder()
        it = self.controllers[me].intent(me, (sh[0] - cam.x, sh[1] - cam.y), dt)
        self.out_reload |= it.reload
        self.out_switch |= it.switch
        self.out_pickup |= it.pickup
        self.out_timer += dt
        if self.out_timer >= NET_RATE:
            self.out_timer = 0.0
            self.conn.send({"t": "in", "m": it.move, "j": int(it.jet), "f": int(it.fire),
                            "a": round(it.aim, 3), "r": int(self.out_reload), "s": int(self.out_switch),
                            "g": int(self.out_pickup)})
            self.out_reload = self.out_switch = self.out_pickup = False

    def apply_snapshot(self, m):
        self.time_left = m["tl"]
        for p, arr in zip(self.players, m["p"]):
            p.net_apply(arr)
        self.projectiles = [Projectile(x, y, vx, vy, 0, None, 1, (r, g, b), width=w, trail=tr / 1000.0)
                            for x, y, vx, vy, r, g, b, w, tr in m["pr"]]
        have = {(pk.kind, pk.rect.centerx, pk.rect.centery): pk for pk in self.pickups}
        new = []
        for kind, x, y in m["pk"]:
            new.append(have.get((kind, x, y)) or Pickup(kind, (x, y)))
        self.pickups = new
        self.drops = []
        for key, x, y, ammo in m.get("dr", []):
            d = DroppedWeapon(key, ammo, x, y, ttl=99.0)
            d.on_ground = True
            self.drops.append(d)
        for ev in m["ev"]:
            if ev[0] == "sfx":
                self.sound(ev[1], ev[2], ev[3], net=False)
            elif ev[0] == "feed":
                self.add_feed(ev[1], ev[2], to_clients=False)
            elif ev[0] == "burst":
                self.make_burst(ev[1], ev[2], ev[3], ev[4])

    # ======================================================================
    #  Rendu : monde et HUD
    # ======================================================================
    def draw_world(self, surf, cam, me=None):
        ox, oy = int(cam.x), int(cam.y)
        self.map.draw_background(surf, ox, oy)
        self.map.draw_foreground(surf, ox, oy)
        for pk in self.pickups:
            pk.draw(surf, ox, oy)
        for d in self.drops:
            d.draw(surf, ox, oy, self.t)
        for pr in self.projectiles:
            pr.draw(surf, ox, oy)
        for p in self.players:
            p.draw(surf, ox, oy)
        for pt in self.particles:
            pt.draw(surf, ox, oy)
        for p in self.players:
            p.draw_label(surf, ox, oy, self.f_s, p.pal["tee"] if p is not me else WHITE, bars=(p is not me))
        d = self.near_drop(me)                             # invite « Ramasser » au-dessus de l'arme à portée
        if d is not None:
            ctrl = self.controllers.get(me)
            key = getattr(ctrl, "pickup_label", "G")
            txt = f"[{key}] {d.name} ({d.ammo})" if len(key) == 1 else f"{key} : {d.name} ({d.ammo})"
            img = self.f_s.render(txt, True, (255, 240, 140))
            r = img.get_rect(midbottom=(d.rect.centerx - ox, d.rect.top - oy - 30))
            pygame.draw.rect(surf, (0, 0, 0), r.inflate(14, 8), border_radius=6)
            surf.blit(img, r)

    def draw_hud(self, surf, p, controller):
        w, h = surf.get_size()
        if p.alive:
            if controller.use_mouse:
                off = surf.get_abs_offset()
                mx, my = pygame.mouse.get_pos()
                mx, my = mx - off[0], my - off[1]
            else:
                cam = next(c for pl, c, _ in self.views if pl is p)
                sx, sy = p.shoulder()
                mx = sx - cam.x + math.cos(p.aim) * 110
                my = sy - cam.y + math.sin(p.aim) * 110
            pygame.draw.circle(surf, WHITE, (int(mx), int(my)), 10, 2)
            for dx, dy, ex, ey in ((-15, 0, -5, 0), (5, 0, 15, 0), (0, -15, 0, -5), (0, 5, 0, 15)):
                pygame.draw.line(surf, WHITE, (mx + dx, my + dy), (mx + ex, my + ey), 2)

        panel = pygame.Surface((250, 76), pygame.SRCALPHA)
        pygame.draw.rect(panel, (0, 0, 0, 150), panel.get_rect(), border_radius=8)
        surf.blit(panel, (12, h - 88))
        draw_text(surf, "SANTÉ", self.f_s, WHITE, (22, h - 80), shadow=False)
        pygame.draw.rect(surf, (50, 50, 55), (22, h - 62, 200, 14))
        pygame.draw.rect(surf, (230, 60, 60) if p.health < 35 else (90, 220, 110),
                         (22, h - 62, int(200 * p.health / MAX_HEALTH), 14))
        draw_text(surf, "JET-PACK", self.f_s, WHITE, (22, h - 42), shadow=False)
        pygame.draw.rect(surf, (50, 50, 55), (22, h - 24, 200, 10))
        pygame.draw.rect(surf, (80, 200, 255) if p.fuel > 20 else ORANGE, (22, h - 24, int(200 * p.fuel / 100), 10))
        if p.boost > 0:
            draw_text(surf, f"BOOST {p.boost:0.1f}s", self.f_s, (255, 160, 80), (270, h - 40))

        wp, other = p.weapon, p.weapons[1 - p.cur]
        panel = pygame.Surface((270, 60), pygame.SRCALPHA)
        pygame.draw.rect(panel, (0, 0, 0, 150), panel.get_rect(), border_radius=8)
        surf.blit(panel, (w - 282, h - 72))
        draw_text(surf, wp.name, self.f_s, WHITE, (w - 272, h - 66), shadow=False)
        ammo = "RECHARGE..." if wp.reloading else f"{wp.ammo} / {wp.spec['mag']}"
        draw_text(surf, ammo, self.f_m, ORANGE if not wp.reloading else (255, 90, 90), (w - 272, h - 46), shadow=False)
        draw_text(surf, f"[{other.name.split()[0]}]", self.f_s, (170, 170, 180), (w - 272 + 170, h - 44), shadow=False)
        if not p.alive:
            draw_text(surf, f"Réapparition dans {max(0, p.respawn_timer):.0f}", self.f_l, WHITE,
                      (w // 2, h // 2 - 40), "center")

    def draw_top_bar(self):
        t = max(0, int(self.time_left))
        draw_text(self.screen, f"{t // 60}:{t % 60:02d}", self.f_l, WHITE, (SCREEN_W // 2, 12), "midtop")
        for i, p in enumerate(sorted(self.players, key=lambda q: -q.kills)):
            draw_text(self.screen, f"{p.name}: {p.kills}", self.f_s, p.pal["tee"],
                      (SCREEN_W // 2 - 140 + (i % 2) * 150, 62 + (i // 2) * 20), "midtop")
        draw_text(self.screen, f"Objectif : {KILL_LIMIT} kills", self.f_s, (230, 230, 230), (SCREEN_W - 14, 12), "topright")
        for i, (txt, ttl, col) in enumerate(self.feed):
            draw_text(self.screen, txt, self.f_s, col, (SCREEN_W - 14, 34 + i * 20), "topright")

    def draw_play(self):
        for p, cam, surf in self.views:
            self.draw_world(surf, cam, me=p)
            self.draw_hud(surf, p, self.controllers[p])
        if len(self.views) == 2:
            pygame.draw.line(self.screen, BLACK, (SCREEN_W // 2, 0), (SCREEN_W // 2, SCREEN_H), 4)
        self.draw_top_bar()
        if self.touch_mode and self.views:
            self.touch.draw(self.screen, near_drop=self.near_drop(self.views[0][0]) is not None)
        if self.paused:
            veil = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            veil.fill((0, 0, 0, 140))
            self.screen.blit(veil, (0, 0))
            draw_text(self.screen, "PAUSE", self.f_xl, WHITE, (SCREEN_W // 2, SCREEN_H // 2 - 70), "center")
            self.pause_rects = []
            for i, (name, label) in enumerate((("resume", "REPRENDRE"), ("menu", "MENU"))):
                r = pygame.Rect(0, 0, 300, 60)
                r.center = (SCREEN_W // 2, SCREEN_H // 2 + 20 + i * 76)
                self.pause_rects.append((name, r))
                pygame.draw.rect(self.screen, GREEN if name == "resume" else (60, 60, 90), r, border_radius=12)
                pygame.draw.rect(self.screen, ORANGE, r, 3, border_radius=12)
                draw_text(self.screen, label, self.f_m, WHITE, r.center, "center")
            draw_text(self.screen, "T ou Pause : reprendre   |   Échap : menu", self.f_s, (220, 220, 230),
                      (SCREEN_W // 2, SCREEN_H // 2 + 190), "center")

    # ======================================================================
    #  Rendu : écrans de menus
    # ======================================================================
    def draw_backdrop(self, gmap=None):
        gmap = gmap or self.get_map("yop")
        cam_x = (1 + math.sin(self.t * 0.15)) / 2 * (WORLD_W - SCREEN_W)
        cam_y = (WORLD_H - SCREEN_H) * (0.6 + 0.4 * math.sin(self.t * 0.1))
        gmap.draw_background(self.screen, int(cam_x), int(cam_y))
        gmap.draw_foreground(self.screen, int(cam_x), int(cam_y))
        veil = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        veil.fill((10, 8, 25, 150))
        self.screen.blit(veil, (0, 0))

    def draw_title(self, title, sub=None, y=48):
        cx = SCREEN_W // 2
        for i, col in enumerate((ORANGE, WHITE, GREEN)):
            pygame.draw.rect(self.screen, col, (cx - 150 + i * 100, y - 36, 100, 6))
        draw_text(self.screen, title, self.f_l, ORANGE, (cx, y + 10), "center")
        if sub:
            draw_text(self.screen, sub, self.f_s, (225, 225, 235), (cx, y + 48), "center")

    def draw_wait(self, txt):
        veil = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        veil.fill((0, 0, 0, 160))
        self.screen.blit(veil, (0, 0))
        draw_text(self.screen, txt, self.f_l, WHITE, (SCREEN_W // 2, SCREEN_H // 2), "center")
        pygame.display.flip()

    def draw_msg(self):
        txt, ttl = self.msg
        if ttl > 0 and txt:
            draw_text(self.screen, txt, self.f_m, (255, 130, 110), (SCREEN_W // 2, SCREEN_H - 36), "center")

    def draw_menu(self):
        self.draw_backdrop()
        cx = SCREEN_W // 2
        for i, col in enumerate((ORANGE, WHITE, GREEN)):
            pygame.draw.rect(self.screen, col, (cx - 260 + i * 174, 70, 174, 8))
        draw_text(self.screen, "BABIZONE", self.f_xl, ORANGE, (cx, 150), "center")
        draw_text(self.screen, "ABIDJAN MILITIA", self.f_l, WHITE, (cx, 225), "center")
        self.menu_form.draw(self.screen, 310, self.t)
        draw_text(self.screen, f"Pseudo : {self.profile['name']}", self.f_s, (255, 240, 140), (cx, SCREEN_H - 60), "center")
        draw_text(self.screen, "v" + VERSION, self.f_s, (200, 200, 215), (SCREEN_W - 14, SCREEN_H - 12), "bottomright")
        draw_text(self.screen, "Flèches / souris : naviguer   |   Entrée : valider   |   Échap : retour",
                  self.f_s, (210, 210, 225), (cx, SCREEN_H - 34), "center")
        self.draw_msg()

    def draw_setup(self):
        key = ARENA_ORDER[self.setup_form.idx("arena")]
        mode = self.setup_form.idx("mode")
        joining = mode == 2 and self.setup_form.idx("role") == 1
        self.draw_backdrop(self.get_map(key) if not joining else None)
        self.draw_title("JOUER")
        end = self.setup_form.draw(self.screen, 110, self.t)
        lvl = LEVELS[self.setup_form.idx("level")]
        if joining:
            lines = ["Demande à ton ami son code d'invitation (ex : GAXAA-UXTLK) ou son adresse IP.",
                     "Il doit avoir créé un salon (Multi en ligne > Héberger une partie)."]
        elif mode == 0:
            lines = [ARENAS[key]["desc"], f"Niveau {lvl['name']} : {lvl['bots']} bots. Souris pour viser, ZQSD/WASD pour bouger."]
        elif mode == 1:
            lines = [ARENAS[key]["desc"], "Écran partagé : J1 souris + ZQSD, J2 flèches + O/P. Les bots complètent la partie."]
        else:
            lines = [ARENAS[key]["desc"], "Tu crées un salon : tes amis te rejoignent avec ton code d'invitation."]
        for i, ln in enumerate(lines):
            draw_text(self.screen, ln, self.f_s, (235, 235, 245), (SCREEN_W // 2, end + 8 + i * 22), "center")
        self.draw_msg()

    def draw_preview(self, feet, scale=3):
        """Aperçu net du personnage (dessiné directement en grand)."""
        f = self.perso_form
        prof = dict(self.profile, outfit=f.idx("outfit"), skin=f.idx("skin"), hair=f.idx("hair"), hcol=f.idx("hcol"),
                    acc=f.idx("acc"), beard=f.idx("beard"),
                    w1=WEAPON_CHOICES[f.idx("w1")], w2=WEAPON_CHOICES[f.idx("w2")])
        p = Player("", palette_of(prof), loadout=(prof["w1"], prof["w2"]))
        p.alive, p.on_ground = True, True
        p.rect.midbottom = feet
        p.aim = 0.2 * math.sin(self.t * 1.6)
        p.facing = 1
        halo = pygame.Surface((300, 50), pygame.SRCALPHA)
        pygame.draw.ellipse(halo, (0, 0, 0, 90), halo.get_rect())
        self.screen.blit(halo, halo.get_rect(center=(feet[0], feet[1] + 4)))
        draw_character(self.screen, p, 0, 0, supersample=4, out_scale=scale)

    def draw_perso(self):
        self.draw_backdrop()
        self.draw_title("MON PERSONNAGE", "Choisis ta tenue, ton teint, ta coiffure et tes armes")
        self.draw_preview((300, 500))
        draw_text(self.screen, self.profile["name"], self.f_m, (255, 240, 140), (300, 560), "center")
        self.perso_form.draw(self.screen, 118, self.t)

    def draw_params(self):
        self.draw_backdrop()
        self.draw_title("PARAMÈTRES")
        self.params_form.draw(self.screen, 200, self.t)
        draw_text(self.screen, "Ton pseudo est affiché au-dessus de ton personnage et dans les parties en ligne.",
                  self.f_s, (225, 225, 235), (SCREEN_W // 2, 400), "center")

    def draw_lobby_host(self):
        self.draw_backdrop(self.get_map(ARENA_ORDER[self.setup_form.idx("arena")]))
        self.draw_title("SALON EN LIGNE", "Arène : " + ARENAS[ARENA_ORDER[self.setup_form.idx("arena")]]["name"])
        cx = SCREEN_W // 2
        box = pygame.Rect(0, 0, 900, 150)
        box.midtop = (cx, 120)
        pygame.draw.rect(self.screen, (24, 24, 44), box, border_radius=14)
        pygame.draw.rect(self.screen, ORANGE, box, 3, border_radius=14)
        draw_text(self.screen, "Code pour les amis sur le même Wi-Fi :", self.f_s, (230, 230, 240), (box.x + 24, box.y + 14))
        draw_text(self.screen, f"{net.encode_code(self.lan_ip)}   ({self.lan_ip})", self.f_l, (255, 240, 140), (box.x + 24, box.y + 36))
        draw_text(self.screen, "Code pour les amis via Internet :", self.f_s, (230, 230, 240), (box.x + 24, box.y + 92))
        if self.pub.ip:
            pub = f"{net.encode_code(self.pub.ip)}   ({self.pub.ip})"
        else:
            pub = "recherche de ton IP publique..." if not self.pub.done else "IP publique introuvable (pas d'Internet ?)"
        draw_text(self.screen, pub, self.f_m, (140, 230, 255), (box.x + 24, box.y + 112))
        if self.local_ips:
            tip2 = "Avec un VPN (Radmin / Tailscale) : tes amis tapent l'une de ces IP :  " + "   ".join(self.local_ips)
        else:
            tip2 = "Windows peut demander d'autoriser le jeu dans le pare-feu : clique sur « Autoriser »."
        tips = ["Internet : redirige le port TCP %d de ta box vers ce PC (ou utilise Radmin VPN / Tailscale)." % net.PORT, tip2]
        for i, ln in enumerate(tips):
            draw_text(self.screen, ln, self.f_s, (225, 225, 235), (cx, 290 + i * 20), "center")
        names = [self.profile["name"] + " (hôte)"] + [c["name"] for c in self.clients.values()]
        draw_text(self.screen, f"Joueurs connectés ({len(names)}/{net.MAX_FRIENDS + 1}) :", self.f_m, WHITE, (cx, 340), "center")
        for i, n in enumerate(names):
            draw_text(self.screen, f"{i + 1}. {n}", self.f_m, ORANGE if i == 0 else (180, 255, 200), (cx, 378 + i * 30), "center")
        draw_text(self.screen, "Les bots choisis dans « Jouer » complètent la partie.", self.f_s, (200, 200, 215), (cx, 505), "center")
        self.lobby_host_form.draw(self.screen, 540, self.t)

    def draw_lobby_client(self):
        self.draw_backdrop(self.get_map(self.lobby_arena))
        self.draw_title("SALON DE L'HÔTE", "Arène : " + ARENAS[self.lobby_arena]["name"])
        cx = SCREEN_W // 2
        draw_text(self.screen, "Connecté ! En attente du lancement par l'hôte...", self.f_m, (255, 240, 140), (cx, 150), "center")
        for i, n in enumerate(self.lobby_names):
            draw_text(self.screen, f"{i + 1}. {n}", self.f_m, WHITE, (cx, 220 + i * 34), "center")
        self.lobby_client_form.draw(self.screen, 540, self.t)

    def draw_gameover(self):
        self.draw_backdrop(self.map)
        cx = SCREEN_W // 2
        draw_text(self.screen, "FIN DE PARTIE", self.f_xl, ORANGE, (cx, 110), "center")
        if self.rank_rows:
            draw_text(self.screen, f"{self.rank_rows[0][0]} a enjaillé Babi !", self.f_l, WHITE, (cx, 190), "center")
        for i, (name, kills, deaths, col) in enumerate(self.rank_rows):
            r = pygame.Rect(0, 0, 520, 50)
            r.center = (cx, 280 + i * 58)
            pygame.draw.rect(self.screen, (30, 30, 50), r, border_radius=10)
            pygame.draw.rect(self.screen, col, r, 3, border_radius=10)
            draw_text(self.screen, f"{i + 1}.  {name}", self.f_m, col, (r.x + 18, r.centery), "midleft")
            draw_text(self.screen, f"{kills} kills   {deaths} morts", self.f_m, WHITE, (r.right - 18, r.centery), "midright")
        names = (("menu", "MENU"),) if self.net_role == "client" else (("again", "REJOUER"), ("menu", "MENU"))
        self.over_rects = []
        for i, (name, label) in enumerate(names):
            r = pygame.Rect(0, 0, 260, 56)
            r.center = (cx + (i - (len(names) - 1) / 2) * 290, SCREEN_H - 60)
            self.over_rects.append((name, r))
            pygame.draw.rect(self.screen, GREEN if name == "again" else (60, 60, 90), r, border_radius=12)
            pygame.draw.rect(self.screen, ORANGE, r, 3, border_radius=12)
            draw_text(self.screen, label, self.f_m, WHITE, r.center, "center")
        if self.net_role == "client":
            draw_text(self.screen, "En attente de l'hôte pour rejouer...", self.f_s, WHITE, (cx, SCREEN_H - 112), "center")

    # ======================================================================
    #  Boucle principale (60 FPS)
    # ======================================================================
    def frame(self):
        """Une image de jeu : événements, mise à jour, dessin."""
        dt = min(self.clock.tick(FPS) / 1000.0, 1 / 30)
        self.t += dt
        if self.msg[1] > 0:
            self.msg = (self.msg[0], self.msg[1] - dt)
        self.handle_events()
        st = self.state
        if st == "play":
            self.update_play(dt)
        elif st == "lobby_host":
            self.update_lobby_host(dt)
        elif st == "lobby_client":
            self.update_lobby_client(dt)
        elif st == "gameover":
            self.update_gameover(dt)
        self.update_music()
        getattr(self, "draw_" + self.state)()
        if self.vkb:
            self.vkb.draw(self.screen)
        pygame.display.flip()

    def run(self):
        while True:
            self.frame()

    async def run_async(self):
        """Boucle compatible navigateur (pygbag) : rend la main au navigateur à chaque image."""
        while True:
            self.frame()
            await asyncio.sleep(0)


async def main():
    await Game().run_async()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except SystemExit:
        raise
    except BaseException:
        # En cas de plantage chez un testeur : un fichier babizone_erreur.txt est créé, à t'envoyer
        try:
            with open(CRASH_FILE, "w", encoding="utf-8") as f:
                f.write("Babizone " + VERSION + "\n" + traceback.format_exc())
        except OSError:
            pass
        raise
