"""Procedurally drawn characters, so the game needs no image assets."""
import math

import pygame

from .ui import font, lighten

WHITE = (255, 255, 255)
DARK = (30, 28, 44)


def _flasher(flash):
    blink = flash > 0 and int(flash * 20) % 2 == 0
    return lambda color: WHITE if blink else color


def draw_shadow(surf, x, y, w):
    shadow = pygame.Surface((w, max(4, w // 4)), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow, (0, 0, 0, 90), shadow.get_rect())
    surf.blit(shadow, shadow.get_rect(center=(int(x), int(y))))


def _eyes(surf, x, y, spacing, r, angry=True, pupil=DARK):
    for d in (-1, 1):
        ex = x + d * spacing
        pygame.draw.circle(surf, WHITE, (ex, y), r)
        pygame.draw.circle(surf, pupil, (ex + r * 0.25, y + r * 0.1), r * 0.5)
        if angry:
            pygame.draw.line(surf, DARK, (ex - d * r * 1.2, y - r * 1.6), (ex + d * r * 1.0, y - r * 0.9), max(2, int(r * 0.4)))


def draw_hero(surf, pos, t, flash=0.0, lunge=0.0):
    c = _flasher(flash)
    draw_shadow(surf, pos[0], pos[1] + 78, 120)
    x, y = int(pos[0] + lunge), int(pos[1] + math.sin(t * 3) * 3)
    skin = (250, 218, 186)
    # Legs and cape
    pygame.draw.rect(surf, c((60, 60, 100)), (x - 22, y + 32, 16, 40), border_radius=5)
    pygame.draw.rect(surf, c((60, 60, 100)), (x + 6, y + 32, 16, 40), border_radius=5)
    pygame.draw.polygon(surf, c((190, 50, 70)), [(x - 24, y - 22), (x - 50, y + 54), (x - 4, y + 42)])
    # Body
    pygame.draw.rect(surf, c((84, 126, 220)), (x - 30, y - 26, 60, 64), border_radius=14)
    pygame.draw.rect(surf, c((240, 196, 80)), (x - 30, y + 16, 60, 8))
    # Head and helmet
    pygame.draw.circle(surf, c(skin), (x, y - 48), 24)
    pygame.draw.rect(surf, c((176, 188, 210)), (x - 26, y - 78, 52, 28),
                     border_top_left_radius=22, border_top_right_radius=22)
    pygame.draw.rect(surf, c((230, 80, 90)), (x - 4, y - 92, 8, 16), border_radius=3)
    pygame.draw.circle(surf, DARK, (x + 12, y - 46), 4)
    pygame.draw.circle(surf, DARK, (x - 2, y - 46), 4)
    # Textbook shield
    pygame.draw.rect(surf, c((160, 56, 60)), (x - 62, y - 14, 30, 42), border_radius=4)
    pygame.draw.rect(surf, c((245, 240, 225)), (x - 36, y - 11, 4, 36))
    pygame.draw.line(surf, c((240, 196, 80)), (x - 56, y), (x - 40, y), 2)
    # Giant pencil sword
    px, py = x + 42, y - 4
    pygame.draw.rect(surf, c((250, 160, 170)), (px - 6, py + 6, 12, 12), border_radius=3)
    pygame.draw.rect(surf, c((190, 190, 200)), (px - 6, py, 12, 6))
    pygame.draw.rect(surf, c((250, 200, 60)), (px - 6, py - 60, 12, 60))
    pygame.draw.polygon(surf, c((240, 214, 170)), [(px - 6, py - 60), (px + 6, py - 60), (px, py - 78)])
    pygame.draw.polygon(surf, DARK, [(px - 2, py - 72), (px + 2, py - 72), (px, py - 78)])
    pygame.draw.circle(surf, c(skin), (px, py + 3), 7)


# --- Enemy shapes. Each draws around center (x, y) at scale s. ---

def _blob(surf, x, y, s, col, t, c):
    squish = math.sin(t * 4) * 0.08
    w, h = int(150 * s * (1 + squish)), int(110 * s * (1 - squish))
    body = pygame.Rect(0, 0, w, h)
    body.midbottom = (x, y + int(60 * s))
    pygame.draw.ellipse(surf, c(col), body)
    pygame.draw.ellipse(surf, c(lighten(col, 50)), (body.left + w * 0.2, body.top + h * 0.12, w * 0.25, h * 0.18))
    ey = body.top + h * 0.45
    _eyes(surf, x, ey, 24 * s, 12 * s)
    pygame.draw.arc(surf, DARK, (x - 20 * s, ey + 8 * s, 40 * s, 22 * s), math.pi * 1.1, math.pi * 1.9, max(2, int(3 * s)))


def _bat(surf, x, y, s, col, t, c):
    flap = math.sin(t * 10) * 25 * s
    by = y - 10 * s + math.sin(t * 3) * 10 * s
    for d in (-1, 1):
        wing = [(x + d * 30 * s, by - 10 * s), (x + d * 130 * s, by - 40 * s - flap),
                (x + d * 112 * s, by + 10 * s - flap * 0.3), (x + d * 80 * s, by),
                (x + d * 55 * s, by + 25 * s)]
        pygame.draw.polygon(surf, c(lighten(col, -30)), wing)
        ear = [(x + d * 18 * s, by - 35 * s), (x + d * 36 * s, by - 70 * s), (x + d * 40 * s, by - 25 * s)]
        pygame.draw.polygon(surf, c(col), ear)
    pygame.draw.circle(surf, c(col), (x, by), int(45 * s))
    _eyes(surf, x, by - 6 * s, 16 * s, 10 * s, pupil=(200, 30, 40))
    for d in (-1, 1):
        fx = x + d * 9 * s
        pygame.draw.polygon(surf, WHITE, [(fx - 5 * s, by + 18 * s), (fx + 5 * s, by + 18 * s), (fx, by + 30 * s)])


def _ghost(surf, x, y, s, col, t, c):
    gy = y - 20 * s + math.sin(t * 2) * 12 * s
    r = 60 * s
    pts = [(x + math.cos(math.radians(a)) * r, gy + math.sin(math.radians(a)) * r) for a in range(180, 361, 10)]
    bottom = gy + 80 * s
    pts.append((x + r, bottom))
    for i in range(11):
        pts.append((x + r - i * (2 * r / 10), bottom + math.sin(i * 1.3 + t * 6) * 8 * s))
    pygame.draw.polygon(surf, c(col), pts)
    for d in (-1, 1):
        pygame.draw.ellipse(surf, DARK, (x + d * 22 * s - 9 * s, gy - 12 * s, 18 * s, 26 * s))
    pygame.draw.ellipse(surf, DARK, (x - 10 * s, gy + 22 * s, 20 * s, 24 * s))


def _goblin(surf, x, y, s, col, t, c):
    by = y + abs(math.sin(t * 5)) * -6 * s
    body = pygame.Rect(0, 0, 90 * s, 80 * s)
    body.midbottom = (x, by + 70 * s)
    pygame.draw.rect(surf, c((120, 80, 50)), body, border_radius=int(20 * s))
    hy = by - 25 * s
    for d in (-1, 1):
        ear = [(x + d * 35 * s, hy - 10 * s), (x + d * 85 * s, hy - 35 * s), (x + d * 40 * s, hy + 15 * s)]
        pygame.draw.polygon(surf, c(col), ear)
    pygame.draw.circle(surf, c(col), (x, hy), int(48 * s))
    _eyes(surf, x, hy - 8 * s, 18 * s, 11 * s, pupil=(220, 180, 30))
    mouth = pygame.Rect(0, 0, 50 * s, 16 * s)
    mouth.center = (x, hy + 22 * s)
    pygame.draw.rect(surf, DARK, mouth, border_radius=int(6 * s))
    for i in range(4):
        tx = mouth.left + (i + 0.5) * mouth.width / 4
        pygame.draw.polygon(surf, WHITE, [(tx - 4 * s, mouth.top), (tx + 4 * s, mouth.top), (tx, mouth.top + 8 * s)])
    # A crammed stack of books.
    for i, bc in enumerate(((200, 70, 70), (70, 120, 200), (230, 190, 70))):
        pygame.draw.rect(surf, c(bc), (x - 75 * s, by + 20 * s - i * 14 * s, 44 * s, 13 * s), border_radius=3)


def _eye(surf, x, y, s, col, t, c):
    ey = y - 15 * s + math.sin(t * 2) * 8 * s
    for i in range(5):
        tx = x + (i - 2) * 22 * s
        end = (tx + math.sin(t * 3 + i) * 15 * s, ey + 100 * s)
        pygame.draw.line(surf, c(lighten(col, -30)), (tx, ey + 40 * s), end, max(3, int(9 * s)))
    pygame.draw.circle(surf, c(col), (x, ey), int(65 * s))
    pygame.draw.circle(surf, WHITE, (x, ey), int(45 * s))
    lx, ly = x + math.sin(t * 1.3) * 15 * s, ey + math.cos(t * 1.7) * 8 * s
    pygame.draw.circle(surf, (200, 50, 60), (lx, ly), int(22 * s))
    pygame.draw.circle(surf, DARK, (lx, ly), int(10 * s))
    pygame.draw.circle(surf, WHITE, (lx - 6 * s, ly - 6 * s), int(4 * s))


def _golem(surf, x, y, s, col, t, c):
    swing = math.sin(t * 2) * 10 * s
    body = pygame.Rect(0, 0, 150 * s, 120 * s)
    body.midbottom = (x, y + 70 * s)
    for d in (-1, 1):
        arm = pygame.Rect(0, 0, 40 * s, 100 * s)
        arm.midtop = (x + d * 95 * s, body.top + 10 * s + d * swing)
        pygame.draw.rect(surf, c(lighten(col, -25)), arm, border_radius=int(12 * s))
    pygame.draw.rect(surf, c(col), body, border_radius=int(16 * s))
    head = pygame.Rect(0, 0, 90 * s, 64 * s)
    head.midbottom = (x, body.top + 6 * s)
    pygame.draw.rect(surf, c(lighten(col, 15)), head, border_radius=int(12 * s))
    for d in (-1, 1):
        pygame.draw.rect(surf, (255, 120, 40), (x + d * 22 * s - 8 * s, head.centery - 6 * s, 16 * s, 10 * s))
    # Clock face on the chest, spinning toward the deadline.
    cx, cy, r = x, body.centery + 6 * s, 34 * s
    pygame.draw.circle(surf, (245, 240, 225), (cx, cy), r)
    pygame.draw.circle(surf, DARK, (cx, cy), r, max(2, int(4 * s)))
    for ang, length in ((t * 4, 0.8), (t * 0.4, 0.55)):
        pygame.draw.line(surf, DARK, (cx, cy), (cx + math.sin(ang) * r * length, cy - math.cos(ang) * r * length), max(2, int(4 * s)))


def _exam(surf, x, y, s, col, t, c):
    sway = math.sin(t * 1.5) * 6 * s
    paper = pygame.Rect(0, 0, 160 * s, 190 * s)
    paper.midbottom = (x + sway, y + 66 * s)
    for d in (-1, 1):
        start = (paper.centerx + d * paper.width / 2, paper.centery + 10 * s)
        end = (start[0] + d * 50 * s, start[1] - 30 * s + math.sin(t * 4 + d) * 15 * s)
        pygame.draw.line(surf, DARK, start, end, max(3, int(6 * s)))
    pygame.draw.rect(surf, c(col), paper, border_radius=int(6 * s))
    for i in range(6):
        ly = paper.top + 70 * s + i * 20 * s
        pygame.draw.line(surf, (150, 180, 230), (paper.left + 14 * s, ly), (paper.right - 14 * s, ly), 2)
    grade = font(int(56 * s), bold=True).render("F", True, (220, 40, 50))
    surf.blit(grade, grade.get_rect(topright=(paper.right - 12 * s, paper.top + 4 * s)))
    _eyes(surf, paper.centerx - 18 * s, paper.top + 44 * s, 22 * s, 13 * s, pupil=(200, 30, 40))
    pts = [(paper.left + 30 * s + i * 14 * s, paper.top + 92 * s + (8 * s if i % 2 else 0)) for i in range(9)]
    pygame.draw.lines(surf, DARK, False, pts, max(2, int(4 * s)))


SHAPES = {"blob": _blob, "bat": _bat, "ghost": _ghost, "goblin": _goblin,
          "eye": _eye, "golem": _golem, "exam": _exam}


def _crown(surf, x, y, s):
    w = 60 * s
    pts = [(x - w / 2, y), (x - w / 2, y - 30 * s), (x - w / 4, y - 15 * s), (x, y - 36 * s),
           (x + w / 4, y - 15 * s), (x + w / 2, y - 30 * s), (x + w / 2, y)]
    pygame.draw.polygon(surf, (250, 200, 60), pts)
    pygame.draw.polygon(surf, (180, 120, 20), pts, 2)


def draw_enemy(surf, enemy, pos, t, flash=0.0, offset=(0, 0), shrink=1.0):
    if shrink <= 0:
        return
    s = enemy.scale * shrink
    x, y = pos[0] + offset[0], pos[1] + offset[1]
    draw_shadow(surf, pos[0], pos[1] + 72 * enemy.scale, int(150 * s))
    if enemy.kind == "elite":
        r = int((95 + math.sin(t * 4) * 6) * s)
        aura = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(aura, (170, 110, 255, 60), (r, r), r)
        surf.blit(aura, (x - r, y - r))
    SHAPES[enemy.shape](surf, x, y, s, enemy.color, t, _flasher(flash))
    if enemy.kind == "boss" and enemy.shape != "exam":
        _crown(surf, x, y - 106 * s, s)


def _radial_glow(glow, color, radius, max_alpha):
    """Soft circle that fades out toward the edge (draws outside-in so inner rings win)."""
    center = (glow.get_width() // 2, glow.get_height() // 2)
    for r in range(radius, 0, -4):
        alpha = int(max_alpha * (1 - r / radius) ** 1.5)
        pygame.draw.circle(glow, (*color, alpha), center, r)


def draw_campfire(surf, x, y, t):
    glow = pygame.Surface((320, 320), pygame.SRCALPHA)
    flicker = int(4 * math.sin(t * 6))
    _radial_glow(glow, (255, 150, 50), 150 + flicker, 70)
    surf.blit(glow, (x - 160, y - 200))
    pygame.draw.line(surf, (110, 70, 40), (x - 60, y + 12), (x + 60, y - 6), 16)
    pygame.draw.line(surf, (95, 60, 35), (x - 60, y - 6), (x + 60, y + 12), 16)
    for i, (col, k) in enumerate((((230, 80, 40), 1.0), ((250, 160, 50), 0.7), ((255, 230, 120), 0.4))):
        h = 110 * k * (1 + 0.12 * math.sin(t * 12 + i * 2))
        w = 55 * k
        tip = x + math.sin(t * 8 + i) * 10 * k
        pygame.draw.polygon(surf, col, [(x - w, y), (x - w * 0.6, y - h * 0.5), (tip, y - h),
                                        (x + w * 0.6, y - h * 0.5), (x + w, y)])


def draw_chest(surf, x, y, t):
    glow = pygame.Surface((300, 300), pygame.SRCALPHA)
    _radial_glow(glow, (255, 220, 100), 140 + int(6 * math.sin(t * 4)), 60)
    surf.blit(glow, (x - 150, y - 170))
    pygame.draw.polygon(surf, (120, 72, 36), [(x - 80, y - 50), (x - 60, y - 120), (x + 60, y - 120), (x + 80, y - 50)])
    pygame.draw.rect(surf, (150, 92, 46), (x - 80, y - 50, 160, 90), border_radius=8)
    pygame.draw.rect(surf, (240, 196, 80), (x - 80, y - 20, 160, 10))
    pygame.draw.rect(surf, (240, 196, 80), (x - 12, y - 34, 24, 34), border_radius=4)
    for i in range(3):
        sx = x + math.sin(t * 2 + i * 2.1) * 50
        sy = y - 90 - ((t * 40 + i * 30) % 80)
        pygame.draw.circle(surf, (255, 240, 160), (sx, sy), 4)
