"""Babizone - générateur de sons et de musiques (synthèse, aucun fichier externe).

Les fichiers générés sont déjà fournis dans le dossier « sounds/ ».
Relancer ce script (nécessite numpy : pip install numpy) permet de les régénérer
ou de modifier les sons. Si ffmpeg est installé, des .ogg sont aussi créés
(utiles pour la version navigateur / mobile).

    python make_sounds.py
"""
import os
import shutil
import subprocess
import wave

import numpy as np

SR = 22050
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sounds")
RNG = np.random.default_rng(225)          # 225 = indicatif de la Côte d'Ivoire


# ---------------------------------------------------------------------------
#  Briques de synthèse
# ---------------------------------------------------------------------------
def T(sec):
    return np.arange(int(sec * SR)) / SR


def noise(sec):
    return RNG.standard_normal(int(sec * SR))


def lowpass(x, cutoff):
    a = 1 - np.exp(-2 * np.pi * cutoff / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i, v in enumerate(x):
        acc += a * (v - acc)
        y[i] = acc
    return y


def highpass(x, cutoff):
    return x - lowpass(x, cutoff)


def bandpass(x, lo, hi):
    return lowpass(highpass(x, lo), hi)


def decay(x, rate):
    return x * np.exp(-T(len(x) / SR) * rate)


def fade(x, ms=4):
    n = int(ms / 1000 * SR)
    if n * 2 < len(x):
        x[:n] *= np.linspace(0, 1, n)
        x[-n:] *= np.linspace(1, 0, n)
    return x


def sweep(sec, f0, f1, curve=4.0):
    t = T(sec)
    f = f1 + (f0 - f1) * np.exp(-t * curve / max(sec, 1e-3))
    return np.sin(2 * np.pi * np.cumsum(f) / SR)


def tone(freq, sec, harmonics=((1, 1.0),), dec=6.0):
    t = T(sec)
    x = sum(a * np.sin(2 * np.pi * freq * h * t) for h, a in harmonics)
    return x * np.exp(-t * dec)


def pluck(freq, sec, dec=7.0):
    return lowpass(tone(freq, sec, ((1, 1), (2, .5), (3, .3), (4, .15), (5, .08)), dec), 4200)


def pad(freq, sec):
    t = T(sec)
    x = np.sin(2 * np.pi * freq * t) + .5 * np.sin(2 * np.pi * freq * 2.005 * t) + .3 * np.sin(2 * np.pi * freq * .4975 * t)
    env = np.minimum(1, t / 0.25) * np.minimum(1, (sec - t) / 0.3)
    return x * env


def stack(*sigs):
    """Additionne des sons de longueurs différentes."""
    n = max(len(x) for x in sigs)
    out = np.zeros(n)
    for x in sigs:
        out[:len(x)] += x
    return out


def mix_into(buf, start, sig, gain=1.0):
    """Ajoute `sig` dans `buf` à partir de `start` (en s), avec bouclage circulaire."""
    n = len(buf)
    i = int(start * SR) % n
    sig = sig * gain
    first = min(len(sig), n - i)
    buf[i:i + first] += sig[:first]
    if first < len(sig):                      # la queue du son revient au début : boucle sans coupure
        rest = sig[first:]
        buf[:len(rest)] += rest[:n]


def norm(x, peak=0.85):
    m = np.max(np.abs(x)) or 1.0
    return x / m * peak


def save(name, x, peak=0.85):
    os.makedirs(OUT, exist_ok=True)
    pcm = (np.clip(norm(x, peak), -1, 1) * 32767).astype(np.int16)
    path = os.path.join(OUT, name + ".wav")
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    return path


# ---------------------------------------------------------------------------
#  Effets sonores
# ---------------------------------------------------------------------------
def sfx_all():
    s = {}
    # --- tirs (un caractère par arme)
    s["shot_nouchi"] = fade(decay(noise(.16), 38) * .9 + decay(sweep(.16, 520, 150), 30) * .9)
    s["shot_coupe"] = fade(decay(highpass(noise(.12), 1200), 45) + decay(sweep(.12, 330, 95), 38) * .8)
    boom = decay(lowpass(noise(.55), 700), 9) + decay(sweep(.55, 140, 38, 6), 8) * 1.2
    s["shot_dozo"] = fade(boom + decay(highpass(noise(.55), 1800), 40) * .6)
    crack = decay(highpass(noise(.9), 900), 30) + decay(sweep(.9, 260, 55, 5), 11) * 1.1
    echo = np.zeros_like(crack)
    echo[int(.16 * SR):] = crack[:len(crack) - int(.16 * SR)] * .28
    s["shot_sniper"] = fade(crack + echo)
    # --- armes
    click = lambda f: decay(bandpass(noise(.05), f, f * 2.2), 120)
    reload = np.zeros(int(.5 * SR))
    mix_into(reload, 0.00, click(1800) * 1.0)
    mix_into(reload, 0.07, decay(sweep(.08, 260, 130), 50) * .6)
    mix_into(reload, 0.30, click(2600) * 1.2)
    mix_into(reload, 0.36, decay(sweep(.08, 330, 160), 50) * .7)
    s["reload"] = fade(reload)
    s["empty"] = fade(click(1500) * 1.2)
    # --- combat
    s["hit"] = fade(stack(decay(sweep(.14, 170, 60, 5), 24) * 1.1, decay(bandpass(noise(.14), 600, 2400), 40) * .6))
    die = decay(sweep(.55, 420, 70, 3), 5) * .9 + decay(lowpass(noise(.55), 1200), 7) * .5
    s["die"] = fade(die * np.sign(np.sin(2 * np.pi * 8 * T(.55))) * .2 + die)
    s["wall"] = fade(stack(decay(bandpass(noise(.1), 2200, 6500), 55), decay(sweep(.1, 3400, 1800), 40) * .25))
    s["jet"] = fade(decay(lowpass(noise(.18), 900), 9) * 1.0 + decay(lowpass(noise(.18), 220), 7) * .8, 12)
    # --- bonus et jeu
    s["pickup"] = fade(np.concatenate([tone(660, .09, ((1, 1), (2, .3)), 9), tone(990, .22, ((1, 1), (2, .3)), 6)]))
    wp = np.concatenate([click(1300) * 1.1, np.zeros(int(.03 * SR)), click(2100) * 1.1])
    wchime = np.concatenate([np.zeros(len(wp)), tone(784, .18, ((1, 1), (3, .2)), 8)])
    s["weapon"] = fade(np.pad(wp, (0, len(wchime) - len(wp))) + wchime * .7)
    s["spawn"] = fade(decay(sweep(.35, 180, 880, 2.5)[::-1][::-1], 4) * .8)
    s["click"] = fade(tone(1100, .05, ((1, 1),), 40))
    s["move"] = fade(tone(740, .035, ((1, 1),), 60) * .7)
    notes = [523.25, 659.25, 783.99, 1046.5]
    win = np.zeros(int(1.1 * SR))
    for i, f in enumerate(notes):
        mix_into(win, i * .13, tone(f, .5, ((1, 1), (2, .35), (3, .15)), 5))
    s["win"] = fade(win)
    lose = np.zeros(int(1.2 * SR))
    for i, f in enumerate([392.0, 349.23, 293.66, 220.0]):
        mix_into(lose, i * .2, tone(f, .55, ((1, 1), (2, .25)), 4))
    s["lose"] = fade(lose)
    return s


# ---------------------------------------------------------------------------
#  Musiques (boucles parfaites de 8 mesures)
# ---------------------------------------------------------------------------
def hz(semitones_from_a4):
    return 440.0 * 2 ** (semitones_from_a4 / 12)


# Progression La mineur : Am - F - C - G (x2).  Notes en demi-tons depuis le La 440
ROOTS = [-24, -28, -21, -26]                      # basses : A1 F1 C2 G1
CHORDS = [[-12, -9, -5], [-16, -12, -9], [-9, -5, -2], [-14, -10, -7]]
SCALE_MELODY = [
    [(0, 12, 2), (3, 15, 1), (4, 12, 2), (7, 10, 1), (8, 12, 2), (11, 7, 1), (12, 10, 4)],
    [(0, 10, 2), (3, 12, 1), (4, 8, 2), (7, 5, 1), (8, 8, 2), (11, 10, 1), (12, 12, 4)],
    [(0, 15, 2), (3, 12, 1), (4, 10, 2), (7, 12, 1), (8, 15, 2), (11, 17, 1), (12, 15, 4)],
    [(0, 10, 2), (3, 7, 1), (4, 10, 2), (7, 12, 1), (8, 10, 2), (11, 7, 1), (12, 5, 4)],
]


def music(bpm, bars, style):
    step = 60.0 / bpm / 4
    n = int(bars * 16 * step * SR)
    buf = np.zeros(n)
    kick = stack(decay(sweep(.28, 135, 46, 5), 14) * 1.3, decay(highpass(noise(.02), 1500), 200) * .3)
    clap = sum(np.pad(decay(bandpass(noise(.16), 1100, 3600), 24), (int(k * .011 * SR), 0))[:int(.16 * SR)] for k in range(3))
    hat_c = decay(highpass(noise(.06), 6000), 90)
    hat_o = decay(highpass(noise(.2), 5000), 18)
    shaker = decay(highpass(noise(.05), 4500), 110)
    conga_hi = stack(decay(sweep(.16, 330, 250, 8), 22), decay(bandpass(noise(.05), 700, 2400), 90) * .3)
    conga_lo = decay(sweep(.2, 220, 150, 8), 18)
    battle = style == "battle"

    for bar in range(bars):
        b0 = bar * 16 * step
        p = bar % 4
        # percussions
        for st in range(16):
            tt = b0 + st * step
            if battle:
                if st % 4 == 0:
                    mix_into(buf, tt, kick, 1.0)
                if st in (4, 12):
                    mix_into(buf, tt, clap, .55)
                if st in (2, 6, 10, 14):
                    mix_into(buf, tt, hat_o, .28)
                if st in (3, 7, 10, 14) and bar % 2 == 0 or st in (3, 11, 15) and bar % 2:
                    mix_into(buf, tt, conga_hi, .5)
            else:
                if st in (0, 10) or (st == 6 and bar % 2):
                    mix_into(buf, tt, kick, .85)
                if st == 8:
                    mix_into(buf, tt, clap, .35)
                if st in (4, 12):
                    mix_into(buf, tt, hat_c, .35)
                if st in (3, 7, 11, 15):
                    mix_into(buf, tt, conga_lo if st in (7, 15) else conga_hi, .42)
            mix_into(buf, tt, shaker, .14 if st % 2 else .08)
        # basse
        root = hz(ROOTS[p])
        pat = [0, 3, 6, 8, 11, 14] if battle else [0, 6, 10]
        for k, st in enumerate(pat):
            f = root * (2 if (battle and k in (2, 5)) else 1)
            mix_into(buf, b0 + st * step, tone(f, step * (3 if battle else 5), ((1, 1), (2, .45), (3, .12)), 7), .55)
        # accords
        for semi in CHORDS[p]:
            if battle:
                for st in (0, 6, 10):
                    mix_into(buf, b0 + st * step, pluck(hz(semi + 12), step * 3, 9), .16)
            else:
                mix_into(buf, b0, pad(hz(semi + 12), 16 * step), .17)
        # mélodie
        for st, semi, ln in SCALE_MELODY[p if bar < 4 else (p + 1) % 4]:
            if battle or st % 4 in (0, 3) or bar >= 4:
                mix_into(buf, b0 + st * step, pluck(hz(semi), step * ln * 1.4 + .2, 6.5), .5 if battle else .42)

    if not battle:                                    # petit écho : ambiance plus aérée
        d = int(step * 3 * SR)
        echo = np.roll(buf, d) * .32 + np.roll(buf, 2 * d) * .15
        buf = buf + echo
    return buf


def build():
    paths = []
    for name, sig in sfx_all().items():
        paths.append(save(name, sig, .9 if name.startswith("shot") or name in ("die",) else .8))
    paths.append(save("music_menu", music(98, 8, "menu"), .7))
    paths.append(save("music_battle", music(132, 8, "battle"), .75))
    return paths


def to_ogg(paths):
    if not shutil.which("ffmpeg"):
        print("ffmpeg introuvable : seuls les .wav ont été créés.")
        return
    for p in paths:
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", p, "-c:a", "libvorbis", "-q:a", "4",
                        p[:-4] + ".ogg"], check=True)


if __name__ == "__main__":
    files = build()
    to_ogg(files)
    print(f"{len(files)} sons générés dans {OUT}")
