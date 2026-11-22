"""Babizone - constantes globales du jeu."""
import sys

# --- Fenêtre ---------------------------------------------------------------
SCREEN_W, SCREEN_H = 1280, 720
FPS = 60

# --- Monde -----------------------------------------------------------------
WORLD_W, WORLD_H = 2400, 1000
GROUND_Y = 940

# --- Physique du joueur (pixels / secondes) --------------------------------
GRAVITY = 1500.0
RUN_SPEED = 300.0
GROUND_ACCEL = 14.0
AIR_ACCEL = 5.0
JUMP_V = -430.0
MAX_RISE = 520.0
MAX_FALL = 850.0

# --- Jet-pack --------------------------------------------------------------
JET_THRUST = 2700.0          # accélération vers le haut (gravité déjà déduite ensuite)
JET_BURN = 32.0              # carburant consommé / s
JET_RECHARGE_GROUND = 55.0   # recharge / s au sol
JET_RECHARGE_AIR = 14.0      # recharge / s en l'air
JET_DELAY = 0.7              # délai avant recharge après une poussée

# --- Joueur ----------------------------------------------------------------
PLAYER_W, PLAYER_H = 32, 60
MAX_HEALTH = 100
RESPAWN_TIME = 3.0
SPAWN_INVULN = 2.0
AIM_ROT_SPEED = 3.4          # rad/s pour la visée au clavier

# --- Partie ----------------------------------------------------------------
MATCH_TIME = 180             # secondes
KILL_LIMIT = 15
MAX_PICKUPS = 5
PICKUP_INTERVAL = 6.0

# --- Couleurs (drapeau ivoirien) -------------------------------------------
ORANGE = (247, 127, 0)
WHITE = (255, 255, 255)
GREEN = (0, 158, 96)
BLACK = (15, 15, 20)

# --- Qualité graphique -------------------------------------------------------
# Les personnages sont dessinés en haute résolution puis réduits (traits lisses).
# 2 = joli (par défaut), 1 = plus rapide si le jeu ralentit sur un PC modeste.
SUPERSAMPLE = 1 if sys.platform in ("emscripten", "android", "ios") else 2     # mobile / navigateur : plus léger

# --- Tests avec des amis -----------------------------------------------------
VERSION = "0.6-test"
# Colle ici le lien de ton formulaire d'avis (Google Forms...). Vide = bouton masqué.
FEEDBACK_URL = ""
