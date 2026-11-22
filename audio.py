"""Babizone - gestion du son : effets positionnels (volume + panoramique) et musiques."""
import os
import time
import pygame

SOUND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sounds")

SFX = ["shot_nouchi", "shot_coupe", "shot_dozo", "shot_sniper", "reload", "empty", "hit", "die",
       "wall", "jet", "pickup", "weapon", "spawn", "click", "move", "win", "lose"]
MUSIC = {"menu": "music_menu", "battle": "music_battle"}

SFX_LEVELS = [0.0, 0.25, 0.5, 0.75, 1.0]
MUSIC_VOLUME = 0.32
HEARING = 1500.0                     # distance (px) au-delà de laquelle un son n'est plus audible

# réglages par son : (gain, écart minimal en secondes entre deux lectures)
TUNING = {"jet": (0.40, 0.09), "wall": (0.40, 0.05), "hit": (0.85, 0.03), "shot_coupe": (0.70, 0.04),
          "move": (0.60, 0.03), "empty": (0.7, 0.2)}


def _find(name):
    for ext in (".ogg", ".wav"):
        path = os.path.join(SOUND_DIR, name + ext)
        if os.path.exists(path):
            return path
    return None


class Audio:
    def __init__(self):
        self.ok = False
        self.sounds = {}
        self.sfx_level = 3
        self.music_on = True
        self.music_name = None
        self._last = {}
        try:
            pygame.mixer.init(22050, -16, 2, 512)
            pygame.mixer.set_num_channels(28)
        except Exception:          # pas de carte son, serveur distant... : le jeu reste jouable en silence
            return
        self.ok = True
        for name in SFX:
            path = _find(name)
            if path:
                try:
                    self.sounds[name] = pygame.mixer.Sound(path)
                except Exception:
                    pass

    # ----- réglages ------------------------------------------------------------------
    def configure(self, sfx_level, music_on):
        self.sfx_level = max(0, min(len(SFX_LEVELS) - 1, int(sfx_level)))
        self.music_on = bool(music_on)
        if not self.ok:
            return
        if not self.music_on:
            pygame.mixer.music.stop()
            self.music_name = None

    @property
    def volume(self):
        return SFX_LEVELS[self.sfx_level]

    # ----- effets ----------------------------------------------------------------------
    def play(self, name, vol=1.0, pan=0.0):
        """pan : -1 (gauche) .. +1 (droite)."""
        snd = self.sounds.get(name)
        if not self.ok or snd is None or self.volume <= 0:
            return
        gain, gap = TUNING.get(name, (1.0, 0.0))
        now = time.monotonic()
        if gap and now - self._last.get(name, 0.0) < gap:
            return
        self._last[name] = now
        v = max(0.0, min(1.0, vol * gain * self.volume))
        left = v * (1.0 - max(0.0, pan) * 0.85)
        right = v * (1.0 + min(0.0, pan) * 0.85)
        try:
            ch = snd.play()
            if ch is not None:
                ch.set_volume(left, right)
        except Exception:
            pass

    def play_at(self, name, x, y, listeners, vol=1.0):
        """Son localisé dans le monde : on l'entend depuis l'écouteur le plus proche."""
        if not listeners:
            return self.play(name, vol)
        lx, ly = min(listeners, key=lambda p: (p[0] - x) ** 2 + (p[1] - y) ** 2)
        d = ((lx - x) ** 2 + (ly - y) ** 2) ** 0.5
        att = max(0.0, 1.0 - d / HEARING) ** 1.4
        if att <= 0.02:
            return
        pan = max(-1.0, min(1.0, (x - lx) / 650.0))
        self.play(name, vol * att, pan)

    # ----- musique ----------------------------------------------------------------------
    def music(self, key):
        """key : 'menu', 'battle' ou None."""
        if not self.ok:
            return
        if key is None or not self.music_on or self.volume < 0:
            if self.music_name is not None:
                pygame.mixer.music.stop()
                self.music_name = None
            return
        if key == self.music_name:
            return
        path = _find(MUSIC[key])
        if not path:
            return
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(MUSIC_VOLUME)
            pygame.mixer.music.play(-1)
            self.music_name = key
        except Exception:
            self.music_name = None
