import math
import random
from functools import partial

import pygame

from .. import settings as S
from ..entities import make_enemy
from ..run import draw_status_bar
from ..sprites import draw_enemy, draw_hero
from ..ui import Button, draw_background, draw_bar, draw_panel, draw_text, draw_wrapped, font
from .base import Scene

ENEMY_KIND = {"battle": "normal", "elite": "elite", "boss": "boss", "final": "final"}
LUNGE_TIME = 0.35


class Battle(Scene):
    HERO_POS = (250, 245)
    GROUND_Y = 330

    def __init__(self, game, run, node_kind):
        super().__init__(game)
        self.run = run
        self.player = run.player
        self.node_kind = node_kind
        self.enemy = make_enemy(run.current_floor, ENEMY_KIND[node_kind], run.rng)
        self.time_limit = self.player.time_limit * (0.75 if node_kind == "elite" else 1.0)
        self.time_left = self.time_limit
        self.combo = 0
        self.t = 0.0
        self.phase = "intro"  # intro -> question -> feedback -> ... -> victory / defeat
        self.phase_t = 0.0
        self.banner = (f"{self.enemy.name} appears!", S.ACCENT)
        self.question = None
        self.last_correct = False
        self.hidden = set()
        self.answer_buttons = []
        self.floaters = []  # [text, color, x, y, age]
        self.hero_flash = self.enemy_flash = 0.0
        self.hero_lunge = self.enemy_lunge = 0.0
        self.shake = 0.0
        self.hint_btn = Button((16, 64, 180, 40), "", self.use_hint, size=20)
        self.potion_btn = Button((206, 64, 180, 40), "", self.use_potion, size=20)

    @property
    def enemy_pos(self):
        return (970, self.GROUND_Y - 70 * self.enemy.scale)

    # --- Turn flow ---

    def next_question(self):
        self.question = self.run.quiz.next_question()
        self.time_left = self.time_limit
        self.hidden = set()
        self.phase, self.phase_t = "question", 0.0
        self.banner = None
        self.answer_buttons = []
        for i, text in enumerate(self.question.options):
            rect = (20 + (i % 2) * 630, 496 + (i // 2) * 106, 610, 96)
            self.answer_buttons.append(Button(rect, f"{i + 1}.  {text}", partial(self.answer, i), size=24, bold=False))

    def answer(self, index):
        if self.phase != "question" or index in self.hidden:
            return
        q = self.question
        correct = index == q.correct_index
        self.last_correct = correct
        self.run.quiz.record(q.card_index, correct)
        ex, ey = self.enemy_pos
        hx, hy = self.HERO_POS
        if correct:
            self.combo += 1
            self.run.best_combo = max(self.run.best_combo, self.combo)
            dmg = self.player.attack + min(5, self.combo - 1)
            tags = []
            if self.time_left >= self.time_limit * 0.65:
                dmg = round(dmg * 1.5)
                tags.append("QUICK!")
            if self.run.rng.random() < self.player.crit_chance:
                dmg *= 2
                tags.append("CRIT!")
            self.enemy.take_damage(dmg)
            self.hero_lunge, self.enemy_flash, self.shake = LUNGE_TIME, 0.45, 0.12
            self.add_floater(f"-{dmg}", S.ACCENT, ex, ey - 60)
            for i, tag in enumerate(tags):
                self.add_floater(tag, S.BLUE if tag == "QUICK!" else S.PURPLE, ex + 90, ey - 20 + i * 34)
            combo = f"   Combo x{self.combo}" if self.combo > 1 else ""
            self.banner = ("Correct!" + combo, S.GOOD)
        else:
            self.combo = 0
            dmg = self.player.take_damage(self.enemy.attack)
            self.enemy_lunge, self.hero_flash, self.shake = LUNGE_TIME, 0.5, 0.25
            self.add_floater(f"-{dmg}", S.BAD, hx, hy - 100)
            self.banner = ("Time's up!" if index is None else "Not quite!", S.BAD)
        for i, b in enumerate(self.answer_buttons):
            if i == q.correct_index:
                b.fill = S.GOOD_DARK
            elif i == index:
                b.fill = S.BAD_DARK
        self.phase, self.phase_t = "feedback", 0.0

    def finish_feedback(self):
        if not self.enemy.alive:
            self.run.kills += 1
            self.phase, self.phase_t = "victory", 0.0
            self.banner = ("Victory!", S.ACCENT)
        elif not self.player.alive:
            self.phase, self.phase_t = "defeat", 0.0
            self.banner = ("You were defeated...", S.BAD)
        else:
            self.next_question()

    def end_battle(self):
        from .run_scenes import GameOver, Reward
        if self.phase == "defeat":
            self.game.change(GameOver(self.game, self.run, won=False))
        elif self.node_kind == "final":
            self.run.floor += 1
            self.game.change(GameOver(self.game, self.run, won=True))
        else:
            self.game.change(Reward(self.game, self.run, self.node_kind))

    # --- Items ---

    def use_hint(self):
        if self.phase != "question" or self.player.hints <= 0:
            return
        wrong = [i for i in range(len(self.question.options))
                 if i != self.question.correct_index and i not in self.hidden]
        count = min(2, len(wrong) - 1)  # Always leave the right answer and one wrong one.
        if count <= 0:
            return
        for i in self.run.rng.sample(wrong, count):
            self.hidden.add(i)
            self.answer_buttons[i].enabled = False
            self.answer_buttons[i].label = ""
        self.player.hints -= 1

    def use_potion(self):
        p = self.player
        if self.phase != "question" or p.potions <= 0 or p.hp >= p.max_hp:
            return
        amount = max(1, round(p.max_hp * 0.4))
        p.heal(amount)
        p.potions -= 1
        self.add_floater(f"+{amount}", S.GOOD, self.HERO_POS[0], self.HERO_POS[1] - 100)

    def add_floater(self, text, color, x, y):
        self.floaters.append([text, color, x, y, 0.0])

    # --- Loop ---

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if self.phase == "question":
                for i in range(len(self.question.options)):
                    if event.key in (pygame.K_1 + i, pygame.K_KP1 + i):
                        self.answer(i)
                        return
                if event.key == pygame.K_h:
                    self.use_hint()
                elif event.key == pygame.K_p:
                    self.use_potion()
            elif self.phase == "feedback" and event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER):
                if self.phase_t > 0.3:
                    self.finish_feedback()
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.phase == "feedback" and self.phase_t > 0.3:
                self.finish_feedback()
            elif self.phase == "question":
                for b in [self.hint_btn, self.potion_btn] + self.answer_buttons:
                    if b.handle_event(event):
                        return

    def update(self, dt):
        self.t += dt
        self.phase_t += dt
        self.hero_flash = max(0.0, self.hero_flash - dt)
        self.enemy_flash = max(0.0, self.enemy_flash - dt)
        self.hero_lunge = max(0.0, self.hero_lunge - dt)
        self.enemy_lunge = max(0.0, self.enemy_lunge - dt)
        self.shake = max(0.0, self.shake - dt)
        for f in self.floaters:
            f[3] -= 50 * dt
            f[4] += dt
        self.floaters = [f for f in self.floaters if f[4] < 1.2]

        if self.phase == "intro" and self.phase_t > 1.2:
            self.next_question()
        elif self.phase == "question":
            self.time_left -= dt
            if self.time_left <= 0:
                self.time_left = 0
                self.answer(None)
        elif self.phase == "feedback" and self.last_correct and self.phase_t > 0.9:
            self.finish_feedback()
        elif self.phase == "victory" and self.phase_t > 1.6:
            self.end_battle()
        elif self.phase == "defeat" and self.phase_t > 2.2:
            self.end_battle()

    def draw(self, surf):
        draw_background(surf)
        pygame.draw.rect(surf, (34, 28, 48), (0, self.GROUND_Y, S.WIDTH, 360 - self.GROUND_Y))
        pygame.draw.line(surf, S.BORDER, (0, self.GROUND_Y), (S.WIDTH, self.GROUND_Y), 2)

        off = (0, 0)
        if self.shake > 0:
            mag = int(self.shake * 40)
            off = (random.randint(-mag, mag), random.randint(-mag, mag))

        hero_lunge = math.sin((1 - self.hero_lunge / LUNGE_TIME) * math.pi) * 90 if self.hero_lunge else 0
        enemy_lunge = -math.sin((1 - self.enemy_lunge / LUNGE_TIME) * math.pi) * 90 if self.enemy_lunge else 0
        hero_flash = self.hero_flash if self.phase != "defeat" else self.phase_t
        draw_hero(surf, (self.HERO_POS[0] + off[0], self.HERO_POS[1] + off[1]), self.t, hero_flash, hero_lunge)
        shrink = 1.0 if self.phase != "victory" else max(0.0, 1 - self.phase_t / 0.8)
        enemy_flash = self.enemy_flash if self.phase != "victory" else self.phase_t
        draw_enemy(surf, self.enemy, self.enemy_pos, self.t, enemy_flash,
                   (enemy_lunge + off[0], off[1]), shrink)

        # Enemy info and player items
        info = pygame.Rect(S.WIDTH // 2 - 200, 64, 400, 62)
        draw_panel(surf, info, color=(30, 26, 46))
        name_color = S.PURPLE if self.enemy.kind == "elite" else S.BAD if self.enemy.kind == "boss" else S.TEXT
        draw_text(surf, self.enemy.name, 22, name_color, (info.left + 12, info.top + 4), bold=True)
        draw_text(surf, f"ATK {self.enemy.attack}", 18, S.MUTED, (info.right - 12, info.top + 8), "topright")
        draw_bar(surf, (info.left + 12, info.top + 34, info.width - 24, 20), self.enemy.hp / self.enemy.max_hp,
                 S.BAD, label=f"{self.enemy.hp}/{self.enemy.max_hp}")
        self.hint_btn.label = f"[H] Hint ({self.player.hints})"
        self.potion_btn.label = f"[P] Potion ({self.player.potions})"
        self.hint_btn.enabled = self.phase == "question" and self.player.hints > 0
        self.potion_btn.enabled = self.phase == "question" and self.player.potions > 0
        self.hint_btn.draw(surf)
        self.potion_btn.draw(surf)

        if self.combo > 1 and self.phase == "question":
            draw_text(surf, f"Combo x{self.combo}", 26, S.ACCENT, (S.WIDTH // 2, 250), "center", bold=True)
        if self.banner:
            text, color = self.banner
            draw_text(surf, text, 44, color, (S.WIDTH // 2, 170), "center", bold=True)
            if self.phase == "feedback" and not self.last_correct:
                draw_text(surf, "Study the correct answer, then press SPACE or click to continue", 20,
                          S.MUTED, (S.WIDTH // 2, 215), "center")

        for text, color, x, y, age in self.floaters:
            img = font(38, True).render(text, True, color)
            img.set_alpha(max(0, 255 - int(age * 210)))
            surf.blit(img, img.get_rect(center=(x, y)))

        # Question panel
        panel = pygame.Rect(20, 368, S.WIDTH - 40, 100)
        draw_panel(surf, panel)
        if self.question and self.phase != "intro":
            draw_text(surf, self.question.label, 18, S.MUTED, (panel.left + 14, panel.top + 6))
            draw_wrapped(surf, self.question.prompt, 34, S.TEXT, panel.inflate(-40, -34).move(0, 8), bold=True)
            frac = self.time_left / self.time_limit
            color = S.GOOD if frac > 0.5 else S.ACCENT if frac > 0.25 else S.BAD
            draw_bar(surf, (20, 476, S.WIDTH - 40, 12), frac, color)
            for b in self.answer_buttons:
                b.draw(surf)
        else:
            draw_text(surf, "Get ready...", 32, S.MUTED, panel.center, "center")

        draw_status_bar(surf, self.run)
