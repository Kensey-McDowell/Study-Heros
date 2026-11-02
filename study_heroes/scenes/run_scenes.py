"""Between-battle scenes: path choice, rewards, campfire, treasure, game over."""
from functools import partial

import pygame

from .. import settings as S
from ..run import NODE_INFO, TREASURE_POOL, UPGRADES, RunState, draw_status_bar
from ..sprites import draw_campfire, draw_chest, draw_hero
from ..ui import Button, draw_background, draw_panel, draw_text, ellipsize, font
from .base import Scene


def _row_of_buttons(count, width, height, y, gap=40):
    total = count * width + (count - 1) * gap
    x0 = (S.WIDTH - total) // 2
    return [pygame.Rect(x0 + i * (width + gap), y, width, height) for i in range(count)]


def _advance(game, run):
    """Finish the current floor and move on to the next path choice."""
    run.floor += 1
    game.change(PathChoice(game, run))


def _draw_trickiest(surf, run, rect):
    tricky = run.quiz.trickiest(5)
    draw_panel(surf, rect, color=(30, 26, 46))
    draw_text(surf, "Cards to review", 24, S.ACCENT, (rect.left + 16, rect.top + 10), bold=True)
    if not tricky:
        draw_text(surf, "No misses yet. Nice work!", 20, S.MUTED, (rect.left + 16, rect.top + 50))
        return
    y = rect.top + 48
    width = rect.width - 32
    for card, misses in tricky:
        draw_text(surf, ellipsize(f"{card['term']}  (missed {misses}x)", font(20, True), width), 20, S.TEXT,
                  (rect.left + 16, y), bold=True)
        draw_text(surf, ellipsize(card["definition"], font(18), width), 18, S.MUTED, (rect.left + 16, y + 26))
        y += 56


class PathChoice(Scene):
    def __init__(self, game, run):
        super().__init__(game)
        self.run = run
        self.choices = run.next_choices()
        self.confirm_quit = False
        self.t = 0.0
        rects = _row_of_buttons(len(self.choices), 320, 240, 270)
        self.buttons = []
        for kind, rect in zip(self.choices, rects):
            title, desc, color = NODE_INFO[kind]
            self.buttons.append(Button(rect, title, partial(self.choose, kind), size=34, color=color, desc=desc))

    def choose(self, kind):
        if kind == "rest":
            self.game.change(Rest(self.game, self.run))
        elif kind == "treasure":
            self.game.change(Treasure(self.game, self.run))
        else:
            from .battle import Battle
            self.game.change(Battle(self.game, self.run, kind))

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if self.confirm_quit:
                from .menu import MainMenu
                self.game.change(MainMenu(self.game))
            self.confirm_quit = True
            return
        for b in self.buttons:
            if b.handle_event(event):
                return

    def update(self, dt):
        self.t += dt

    def draw(self, surf):
        draw_background(surf)
        draw_status_bar(surf, self.run)
        draw_text(surf, f"Floor {self.run.current_floor}", 52, S.ACCENT, (S.WIDTH // 2, 110), "center", bold=True)
        draw_text(surf, "Choose your path" if len(self.choices) > 1 else "The only way is forward", 26, S.MUTED,
                  (S.WIDTH // 2, 160), "center")
        # Progress track
        total = self.run.TOTAL_FLOORS
        spacing = 60
        x0 = S.WIDTH // 2 - (total - 1) * spacing // 2
        pygame.draw.line(surf, S.BORDER, (x0, 215), (x0 + (total - 1) * spacing, 215), 3)
        for i in range(total):
            floor = i + 1
            boss = floor in (self.run.MIDBOSS_FLOOR, total)
            if floor <= self.run.floor:
                color = S.GOOD
            elif floor == self.run.current_floor:
                color = S.ACCENT
            else:
                color = S.PANEL_LIGHT
            r = 14 if boss else 10
            pygame.draw.circle(surf, color, (x0 + i * spacing, 215), r)
            if boss:
                pygame.draw.circle(surf, S.BAD, (x0 + i * spacing, 215), r, 3)
        for b in self.buttons:
            b.draw(surf)
        draw_hero(surf, (S.WIDTH // 2, 620), self.t)
        msg = "Press ESC again to abandon this run" if self.confirm_quit else "ESC: abandon run"
        draw_text(surf, msg, 18, S.BAD if self.confirm_quit else S.MUTED, (16, S.HEIGHT - 30))


class Reward(Scene):
    def __init__(self, game, run, node_kind):
        super().__init__(game)
        self.run = run
        p = run.player
        self.bonus = ""
        if node_kind == "elite":
            p.hints += 1
            self.bonus = "Elite bonus: +1 hint"
        elif node_kind == "boss":
            p.heal(p.max_hp // 2)
            self.bonus = "Boss bonus: healed 50% HP"
        options = run.rng.sample(UPGRADES, 3)
        rects = _row_of_buttons(3, 340, 220, 260)
        self.buttons = [Button(r, u.name, partial(self.pick, u), size=30, desc=u.desc) for u, r in zip(options, rects)]

    def pick(self, upgrade):
        upgrade.apply(self.run.player)
        _advance(self.game, self.run)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and pygame.K_1 <= event.key <= pygame.K_3:
            self.buttons[event.key - pygame.K_1].on_click()
            return
        for b in self.buttons:
            if b.handle_event(event):
                return

    def draw(self, surf):
        draw_background(surf)
        draw_status_bar(surf, self.run)
        draw_text(surf, "Victory!", 60, S.ACCENT, (S.WIDTH // 2, 120), "center", bold=True)
        draw_text(surf, "Choose an upgrade (or press 1-3)", 26, S.MUTED, (S.WIDTH // 2, 185), "center")
        if self.bonus:
            draw_text(surf, self.bonus, 24, S.GOOD, (S.WIDTH // 2, 225), "center")
        for b in self.buttons:
            b.draw(surf)
        acc = round(self.run.quiz.accuracy * 100)
        draw_text(surf, f"Run accuracy so far: {acc}%", 22, S.MUTED, (S.WIDTH // 2, 540), "center")


class Rest(Scene):
    def __init__(self, game, run):
        super().__init__(game)
        self.run = run
        self.t = 0.0
        p = run.player
        self.heal_amount = max(1, round(p.max_hp * 0.4))
        self.buttons = [
            Button((80, 300, 340, 120), "Rest", self.rest, size=30, desc=f"Heal {self.heal_amount} HP."),
            Button((80, 440, 340, 120), "Train", self.train, size=30, desc="+1 attack damage."),
        ]

    def rest(self):
        self.run.player.heal(self.heal_amount)
        _advance(self.game, self.run)

    def train(self):
        self.run.player.attack += 1
        _advance(self.game, self.run)

    def handle_event(self, event):
        for b in self.buttons:
            if b.handle_event(event):
                return

    def update(self, dt):
        self.t += dt

    def draw(self, surf):
        draw_background(surf)
        draw_status_bar(surf, self.run)
        draw_text(surf, "Campfire", 56, S.ACCENT, (250, 120), "center", bold=True)
        draw_text(surf, "Take a breather before the next fight.", 22, S.MUTED, (250, 175), "center")
        draw_campfire(surf, 650, 540, self.t)
        draw_hero(surf, (510, 470), self.t)
        for b in self.buttons:
            b.draw(surf)
        _draw_trickiest(surf, self.run, pygame.Rect(820, 120, 420, 340))


class Treasure(Scene):
    def __init__(self, game, run):
        super().__init__(game)
        self.run = run
        self.t = 0.0
        self.item = run.rng.choice(TREASURE_POOL)
        self.item.apply(run.player)
        self.button = Button((S.WIDTH // 2 - 150, 600, 300, 60), "Continue", lambda: _advance(game, run))

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_RETURN):
            self.button.on_click()
            return
        self.button.handle_event(event)

    def update(self, dt):
        self.t += dt

    def draw(self, surf):
        draw_background(surf)
        draw_status_bar(surf, self.run)
        draw_text(surf, "Treasure!", 56, S.ACCENT, (S.WIDTH // 2, 120), "center", bold=True)
        draw_chest(surf, S.WIDTH // 2, 380, self.t)
        draw_text(surf, f"You found: {self.item.name}", 32, S.TEXT, (S.WIDTH // 2, 470), "center", bold=True)
        draw_text(surf, self.item.desc, 22, S.MUTED, (S.WIDTH // 2, 515), "center")
        self.button.draw(surf)


class GameOver(Scene):
    def __init__(self, game, run, won):
        super().__init__(game)
        self.run = run
        self.won = won
        self.t = 0.0
        self.buttons = [
            Button((S.WIDTH // 2 - 330, 620, 300, 60), "Try Again", self.retry, color=(50, 100, 70)),
            Button((S.WIDTH // 2 + 30, 620, 300, 60), "Main Menu", self.menu),
        ]

    def retry(self):
        self.game.change(PathChoice(self.game, RunState(self.run.deck, self.run.ask_mode)))

    def menu(self):
        from .menu import MainMenu
        self.game.change(MainMenu(self.game))

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.menu()
            return
        for b in self.buttons:
            if b.handle_event(event):
                return

    def update(self, dt):
        self.t += dt

    def draw(self, surf):
        draw_background(surf)
        title = "You Passed the Final Exam!" if self.won else "Run Over"
        draw_text(surf, title, 60, S.ACCENT if self.won else S.BAD, (S.WIDTH // 2, 80), "center", bold=True)
        quiz = self.run.quiz
        stats = [
            ("Floors cleared", f"{self.run.floor}/{self.run.TOTAL_FLOORS}"),
            ("Monsters defeated", str(self.run.kills)),
            ("Questions answered", str(quiz.total_answered)),
            ("Accuracy", f"{round(quiz.accuracy * 100)}%"),
            ("Best combo", str(self.run.best_combo)),
        ]
        panel = pygame.Rect(60, 150, 480, 340)
        draw_panel(surf, panel, color=(30, 26, 46))
        draw_text(surf, "Run summary", 24, S.ACCENT, (panel.left + 16, panel.top + 10), bold=True)
        for i, (label, value) in enumerate(stats):
            y = panel.top + 60 + i * 52
            draw_text(surf, label, 24, S.MUTED, (panel.left + 20, y))
            draw_text(surf, value, 26, S.TEXT, (panel.right - 20, y), "topright", bold=True)
        _draw_trickiest(surf, self.run, pygame.Rect(580, 150, 640, 340))
        for b in self.buttons:
            b.draw(surf)
