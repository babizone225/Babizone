"""Babizone - petit système de menus : lignes de choix, champs de texte, boutons."""
import pygame
from settings import *


def draw_text(surf, txt, font, color, pos, anchor="topleft", shadow=True):
    if shadow:
        sh = font.render(txt, True, (0, 0, 0))
        surf.blit(sh, sh.get_rect(**{anchor: (pos[0] + 2, pos[1] + 2)}))
    img = font.render(txt, True, color)
    r = img.get_rect(**{anchor: pos})
    surf.blit(img, r)
    return r


class Row:
    """kind : 'choice' (gauche/droite), 'text' (saisie) ou 'button'."""

    def __init__(self, key, label, kind="choice", options=None, index=0, text="",
                 maxlen=14, visible=None):
        self.key = key
        self.label = label
        self.kind = kind
        self.options = options if options is not None else []
        self.index = index
        self.text = text
        self.maxlen = maxlen
        self.visible = visible
        self.fresh = False
        self.rect = None

    def is_visible(self):
        return True if self.visible is None else bool(self.visible())

    def get_label(self):
        return self.label() if callable(self.label) else self.label

    def get_options(self):
        return self.options() if callable(self.options) else self.options

    def value(self):
        opts = self.get_options()
        return opts[self.index % len(opts)] if opts else None

    def step(self, d):
        opts = self.get_options()
        if opts:
            self.index = (self.index + d) % len(opts)


class Form:
    def __init__(self, rows, fonts, row_w=740, row_h=50, gap=10, cx=SCREEN_W // 2):
        self.cx = cx
        self.changed = False          # un choix vient d'être modifié (pour le son)
        self.kb_request = None        # ligne texte touchée : le jeu peut ouvrir le clavier à l'écran
        self.rows = rows
        self.f_s, self.f_m, self.f_l = fonts
        self.row_w, self.row_h, self.gap = row_w, row_h, gap
        self.sel = 0

    def row(self, key):
        return next(r for r in self.rows if r.key == key)

    def idx(self, key):
        return self.row(key).index

    def val(self, key):
        r = self.row(key)
        return r.text if r.kind == "text" else r.value()

    def visible_rows(self):
        return [r for r in self.rows if r.is_visible()]

    def _selected(self):
        vis = self.visible_rows()
        if not vis:
            return None
        self.sel = max(0, min(self.sel, len(vis) - 1))
        return vis[self.sel]

    def handle(self, e):
        """Retourne la clé d'un bouton activé, '__back__' pour Échap, sinon None."""
        vis = self.visible_rows()
        row = self._selected()
        if row is None:
            return None

        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                return "__back__"
            if e.key == pygame.K_UP:
                self.sel = (self.sel - 1) % len(vis)
            elif e.key in (pygame.K_DOWN, pygame.K_TAB):
                self.sel = (self.sel + 1) % len(vis)
            elif e.key == pygame.K_LEFT and row.kind == "choice":
                row.step(-1)
                self.changed = True
            elif e.key == pygame.K_RIGHT and row.kind == "choice":
                row.step(+1)
                self.changed = True
            elif e.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                if row.kind == "button":
                    return row.key
                if row.kind == "choice":
                    row.step(+1)
                    self.changed = True
                else:
                    self.sel = (self.sel + 1) % len(vis)
            elif row.kind == "text":
                if e.key == pygame.K_BACKSPACE:
                    row.text = "" if row.fresh else row.text[:-1]
                    row.fresh = False
                elif e.unicode and e.unicode.isprintable():
                    if row.fresh:              # 1re frappe : remplace le texte prérempli
                        row.text, row.fresh = "", False
                    if len(row.text) < row.maxlen:
                        row.text += e.unicode
            return None

        if e.type == pygame.MOUSEMOTION:
            for i, r in enumerate(vis):
                if r.rect and r.rect.collidepoint(e.pos):
                    self.sel = i
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for i, r in enumerate(vis):
                if r.rect and r.rect.collidepoint(e.pos):
                    self.sel = i
                    if r.kind == "button":
                        return r.key
                    if r.kind == "choice":
                        r.step(-1 if e.pos[0] < r.rect.right - 190 else +1)
                        self.changed = True
                    elif r.kind == "text":
                        self.kb_request = r
        return None

    def draw(self, surf, top, t=0.0):
        vis = self.visible_rows()
        self._selected()
        cx = self.cx
        y = top
        for i, r in enumerate(vis):
            rect = pygame.Rect(0, 0, self.row_w, self.row_h)
            rect.midtop = (cx, y)
            r.rect = rect
            y += self.row_h + self.gap
            sel = (i == self.sel)

            if r.kind == "button":
                pygame.draw.rect(surf, GREEN if sel else (30, 90, 65), rect, border_radius=12)
                pygame.draw.rect(surf, ORANGE if sel else (150, 150, 165), rect, 3, border_radius=12)
                draw_text(surf, r.get_label(), self.f_m, WHITE, rect.center, "center")
                continue

            pygame.draw.rect(surf, (48, 48, 78) if sel else (28, 28, 48), rect, border_radius=12)
            pygame.draw.rect(surf, ORANGE if sel else (95, 95, 125), rect, 3 if sel else 2, border_radius=12)
            draw_text(surf, r.get_label(), self.f_m, (235, 235, 245), (rect.x + 20, rect.centery), "midleft")

            if r.kind == "choice":
                vx = rect.right - 190
                val = str(r.value())
                col = (255, 240, 140) if sel else WHITE
                draw_text(surf, val, self.f_m, col, (vx, rect.centery), "center")
                if sel:
                    off = max(60, self.f_m.size(val)[0] // 2 + 18)
                    pygame.draw.polygon(surf, ORANGE, [(vx - off, rect.centery), (vx - off + 12, rect.centery - 9), (vx - off + 12, rect.centery + 9)])
                    pygame.draw.polygon(surf, ORANGE, [(vx + off, rect.centery), (vx + off - 12, rect.centery - 9), (vx + off - 12, rect.centery + 9)])
            else:  # text
                box = pygame.Rect(0, 0, 290, rect.h - 14)
                box.midright = (rect.right - 12, rect.centery)
                pygame.draw.rect(surf, (12, 12, 24), box, border_radius=8)
                pygame.draw.rect(surf, ORANGE if sel else (120, 120, 140), box, 2, border_radius=8)
                shown = r.text + ("|" if sel and int(t * 2) % 2 == 0 else "")
                draw_text(surf, shown, self.f_m, WHITE, (box.x + 12, box.centery), "midleft", shadow=False)
        return y


class VKeyboard:
    """Clavier à l'écran (écrans tactiles) pour saisir un pseudo ou un code."""
    ROWS = ["1234567890", "AZERTYUIOP", "QSDFGHJKLM", "WXCVBN.-:"]

    def __init__(self, row, fonts):
        self.row = row
        self.f_s, self.f_m, self.f_l = fonts
        self.lower = False
        self.keys = []            # (rect, valeur, texte affiché)
        kw, kh, gap = 108, 66, 8
        top = 330
        for ri, chars in enumerate(self.ROWS):
            total = len(chars) * (kw + gap) - gap
            x0 = (SCREEN_W - total) // 2
            for ci, ch in enumerate(chars):
                self.keys.append((pygame.Rect(x0 + ci * (kw + gap), top + ri * (kh + gap), kw, kh), ch, ch))
        y = top + 4 * (kh + gap)
        self.keys.append((pygame.Rect(180, y, 220, kh), "<lower>", "Aa"))
        self.keys.append((pygame.Rect(408, y, 464, kh), " ", "ESPACE"))
        self.keys.append((pygame.Rect(880, y, 220, kh), "<back>", "EFFACER"))
        self.keys.append((pygame.Rect(1108, y, 160, kh), "<ok>", "OK"))

    def handle(self, e):
        """Retourne True quand la saisie est terminée."""
        if e.type == pygame.KEYDOWN and e.key in (pygame.K_RETURN, pygame.K_ESCAPE):
            return True
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for rect, val, _ in self.keys:
                if rect.collidepoint(e.pos):
                    if val == "<ok>":
                        return True
                    if val == "<back>":
                        self.row.text = self.row.text[:-1]
                    elif val == "<lower>":
                        self.lower = not self.lower
                    elif len(self.row.text) < self.row.maxlen:
                        self.row.text += val.lower() if self.lower and val.isalpha() else val
        return False

    def draw(self, surf):
        veil = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        veil.fill((0, 0, 0, 190))
        surf.blit(veil, (0, 0))
        box = pygame.Rect(0, 0, 760, 70)
        box.center = (SCREEN_W // 2, 250)
        pygame.draw.rect(surf, (12, 12, 24), box, border_radius=10)
        pygame.draw.rect(surf, ORANGE, box, 3, border_radius=10)
        draw_text(surf, self.row.get_label() + " :  " + self.row.text + "|", self.f_m, WHITE, (box.x + 16, box.centery), "midleft")
        for rect, val, txt in self.keys:
            special = val.startswith("<") or val == " "
            pygame.draw.rect(surf, (40, 90, 70) if special else (40, 40, 66), rect, border_radius=10)
            pygame.draw.rect(surf, ORANGE if val == "<ok>" else (130, 130, 160), rect, 2, border_radius=10)
            show = txt.lower() if self.lower and txt.isalpha() else txt
            draw_text(surf, show, self.f_m, WHITE, rect.center, "center")
