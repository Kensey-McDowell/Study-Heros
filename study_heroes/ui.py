"""Small UI toolkit: fonts, text helpers, buttons and text inputs."""
import random

import pygame

from . import settings as S

_fonts = {}
_bg_cache = None


def font(size, bold=False):
    key = (size, bold)
    if key not in _fonts:
        _fonts[key] = pygame.font.SysFont("segoeui,arial,helvetica,sans", size, bold=bold)
    return _fonts[key]


def lighten(color, amount):
    return tuple(max(0, min(255, c + amount)) for c in color[:3])


def draw_text(surf, text, size, color, pos, anchor="topleft", bold=False):
    img = font(size, bold).render(str(text), True, color)
    rect = img.get_rect(**{anchor: pos})
    surf.blit(img, rect)
    return rect


def ellipsize(text, fnt, width):
    text = " ".join(str(text).split())
    if fnt.size(text)[0] <= width:
        return text
    while text and fnt.size(text + "...")[0] > width:
        text = text[:-1]
    return text + "..."


def wrap_text(text, fnt, max_width):
    lines = []
    for para in str(text).split("\n"):
        line = ""
        for word in para.split(" "):
            test = word if not line else f"{line} {word}"
            if fnt.size(test)[0] <= max_width:
                line = test
                continue
            if line:
                lines.append(line)
            # Break words that are wider than the whole line.
            while fnt.size(word)[0] > max_width and len(word) > 1:
                i = len(word)
                while i > 1 and fnt.size(word[:i])[0] > max_width:
                    i -= 1
                lines.append(word[:i])
                word = word[i:]
            line = word
        lines.append(line)
    return lines


def draw_wrapped(surf, text, size, color, rect, align="center", valign="center", bold=False, min_size=14):
    """Draw word-wrapped text inside rect, shrinking the font until it fits."""
    rect = pygame.Rect(rect)
    while True:
        fnt = font(size, bold)
        lines = wrap_text(text, fnt, rect.width)
        line_h = fnt.get_linesize()
        total = line_h * len(lines)
        if total <= rect.height or size <= min_size:
            break
        size -= 2
    y = rect.top if valign == "top" else rect.centery - total // 2
    for line in lines:
        img = fnt.render(line, True, color)
        if align == "left":
            r = img.get_rect(topleft=(rect.left, y))
        else:
            r = img.get_rect(midtop=(rect.centerx, y))
        surf.blit(img, r)
        y += line_h


def draw_panel(surf, rect, color=S.PANEL, border=S.BORDER, radius=12):
    pygame.draw.rect(surf, color, rect, border_radius=radius)
    pygame.draw.rect(surf, border, rect, 2, border_radius=radius)


def draw_bar(surf, rect, frac, color, bg=(30, 26, 40), label=None):
    rect = pygame.Rect(rect)
    pygame.draw.rect(surf, bg, rect, border_radius=6)
    frac = max(0.0, min(1.0, frac))
    if frac > 0:
        fill = rect.copy()
        fill.width = max(4, int(rect.width * frac))
        pygame.draw.rect(surf, color, fill, border_radius=6)
    pygame.draw.rect(surf, S.BORDER, rect, 2, border_radius=6)
    if label:
        draw_text(surf, label, max(14, rect.height - 6), S.TEXT, rect.center, "center", bold=True)


def draw_background(surf):
    global _bg_cache
    if _bg_cache is None:
        w, h = surf.get_size()
        _bg_cache = pygame.Surface((w, h))
        for y in range(h):
            k = y / h
            color = [int(S.BG2[i] * (1 - k) + S.BG[i] * k) for i in range(3)]
            pygame.draw.line(_bg_cache, color, (0, y), (w, y))
        rng = random.Random(7)
        for _ in range(90):
            pos = (rng.randrange(w), rng.randrange(int(h * 0.6)))
            pygame.draw.circle(_bg_cache, (96, 86, 140), pos, rng.choice((1, 1, 2)))
    surf.blit(_bg_cache, (0, 0))


def get_clipboard():
    try:
        text = pygame.scrap.get_text()
        if text:
            return text
    except Exception:
        pass
    try:
        import tkinter

        root = tkinter.Tk()
        root.withdraw()
        text = root.clipboard_get()
        root.destroy()
        return text
    except Exception:
        return ""


class Button:
    def __init__(self, rect, label, on_click=None, size=26, color=S.PANEL_LIGHT,
                 enabled=True, desc=None, bold=True):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.on_click = on_click
        self.size = size
        self.color = color
        self.enabled = enabled
        self.desc = desc
        self.bold = bold
        self.fill = None  # Optional color override (e.g. right/wrong answers).

    def hovered(self):
        return self.enabled and self.rect.collidepoint(pygame.mouse.get_pos())

    def handle_event(self, event):
        if (self.enabled and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
                and self.rect.collidepoint(event.pos)):
            if self.on_click:
                self.on_click()
            return True
        return False

    def draw(self, surf):
        hov = self.hovered()
        base = self.fill or (self.color if self.enabled else S.DISABLED)
        if hov and self.fill is None:
            base = lighten(base, 22)
        pygame.draw.rect(surf, base, self.rect, border_radius=10)
        pygame.draw.rect(surf, S.ACCENT if hov else S.BORDER, self.rect, 2, border_radius=10)
        color = S.TEXT if self.enabled else S.MUTED
        inner = self.rect.inflate(-24, -12)
        if self.desc:
            title_h = font(self.size, True).get_linesize()
            draw_text(surf, self.label, self.size, color, (inner.centerx, inner.top + 8), "midtop", bold=True)
            desc_rect = pygame.Rect(inner.left, inner.top + title_h + 20, inner.width, inner.height - title_h - 20)
            draw_wrapped(surf, self.desc, self.size - 8, lighten(S.MUTED, 50), desc_rect, valign="top")
        else:
            draw_wrapped(surf, self.label, self.size, color, inner, bold=self.bold)


class TextInput:
    def __init__(self, rect, text="", placeholder="", max_len=300, size=24):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.placeholder = placeholder
        self.max_len = max_len
        self.size = size
        self.active = False

    def insert(self, text):
        text = text.replace("\r", "").replace("\n", " ").replace("\t", " ")
        self.text = (self.text + text)[: self.max_len]

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.active = self.rect.collidepoint(event.pos)
            return self.active
        if not self.active:
            return False
        if event.type == pygame.TEXTINPUT:
            self.insert(event.text)
            return True
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                if event.mod & pygame.KMOD_CTRL:
                    self.text = self.text.rstrip().rpartition(" ")[0]
                    if self.text:
                        self.text += " "
                else:
                    self.text = self.text[:-1]
                return True
            if event.key == pygame.K_v and event.mod & pygame.KMOD_CTRL:
                self.insert(get_clipboard())
                return True
        return False

    def draw(self, surf):
        pygame.draw.rect(surf, (28, 24, 40), self.rect, border_radius=8)
        pygame.draw.rect(surf, S.ACCENT if self.active else S.BORDER, self.rect, 2, border_radius=8)
        fnt = font(self.size)
        inner = self.rect.inflate(-20, 0)
        img = fnt.render(self.text or self.placeholder, True, S.TEXT if self.text else S.MUTED)
        x = inner.left
        if self.text and img.get_width() > inner.width - 4:
            x = inner.right - 4 - img.get_width()  # Keep the end of long text visible.
        prev_clip = surf.get_clip()
        surf.set_clip(inner)
        surf.blit(img, (x, inner.centery - img.get_height() // 2))
        if self.active and (pygame.time.get_ticks() // 500) % 2 == 0:
            cx = x + (img.get_width() if self.text else 0) + 1
            pygame.draw.line(surf, S.TEXT, (cx, inner.centery - 12), (cx, inner.centery + 12), 2)
        surf.set_clip(prev_clip)
