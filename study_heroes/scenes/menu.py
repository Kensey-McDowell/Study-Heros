import math
from functools import partial

import pygame

from .. import settings as S
from .. import storage
from ..entities import Enemy
from ..run import RunState
from ..sprites import draw_enemy, draw_hero
from ..ui import Button, draw_background, draw_panel, draw_text
from .base import Scene

ASK_MODES = [
    ("term", "Show the term, pick the definition"),
    ("definition", "Show the definition, pick the term"),
    ("mixed", "Mixed: both directions"),
]


class MainMenu(Scene):
    def __init__(self, game):
        super().__init__(game)
        cx = S.WIDTH // 2
        self.buttons = [
            Button((cx - 170, 340, 340, 64), "Start Adventure", lambda: game.change(DeckSelect(game, "play"))),
            Button((cx - 170, 420, 340, 64), "Manage Decks", lambda: game.change(DeckSelect(game, "edit"))),
            Button((cx - 170, 500, 340, 64), "Quit", game.quit),
        ]
        self.slime = Enemy("Slime", "blob", (110, 200, 120), 1, 1)
        self.t = 0.0

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.game.quit()
            return
        for b in self.buttons:
            if b.handle_event(event):
                return

    def update(self, dt):
        self.t += dt

    def draw(self, surf):
        draw_background(surf)
        y = 150 + math.sin(self.t * 2) * 6
        draw_text(surf, "Study Heroes", 92, S.ACCENT, (S.WIDTH // 2, y), "center", bold=True)
        draw_text(surf, "Master your flashcards. Slay your monsters.", 28, S.MUTED,
                  (S.WIDTH // 2, 235), "center")
        draw_hero(surf, (220, 460), self.t)
        draw_enemy(surf, self.slime, (1060, 470), self.t)
        for b in self.buttons:
            b.draw(surf)


class DeckSelect(Scene):
    ROW_H = 72
    LIST_RECT = pygame.Rect(240, 140, 800, 440)

    def __init__(self, game, mode):
        super().__init__(game)
        self.mode = mode  # "play" or "edit"
        self.decks = storage.list_decks()
        self.scroll = 0
        self.ask_index = 0
        self.message = ""
        self.confirm_delete = None
        self.static_buttons = [Button((40, 640, 200, 52), "Back", self.back)]
        if mode == "play":
            self.ask_button = Button((S.WIDTH // 2 - 300, 600, 600, 52), "", self.cycle_ask, size=22)
            self.static_buttons.append(self.ask_button)
            self.cycle_ask(advance=False)
        else:
            self.static_buttons += [
                Button((S.WIDTH - 500, 640, 220, 52), "+ New Deck", self.new_deck, color=(50, 100, 70)),
                Button((S.WIDTH - 260, 640, 220, 52), "Import .txt", self.import_files),
            ]
        self.rebuild()

    def cycle_ask(self, advance=True):
        if advance:
            self.ask_index = (self.ask_index + 1) % len(ASK_MODES)
        self.ask_button.label = f"Questions: {ASK_MODES[self.ask_index][1]}  (click to change)"

    def rebuild(self):
        max_scroll = max(0, len(self.decks) * self.ROW_H - self.LIST_RECT.height)
        self.scroll = max(0, min(self.scroll, max_scroll))
        self.rows = []
        edit = self.mode == "edit"
        for i, deck in enumerate(self.decks):
            y = self.LIST_RECT.top + i * self.ROW_H - self.scroll
            width = self.LIST_RECT.width - (130 if edit else 0)
            enabled = edit or len(deck.cards) >= 2
            label = f"{deck.name}   ({len(deck.cards)} cards)"
            row = [Button((self.LIST_RECT.left, y, width, self.ROW_H - 10), label,
                          partial(self.pick, deck), size=26, enabled=enabled)]
            if edit:
                sure = self.confirm_delete is deck
                row.append(Button((self.LIST_RECT.right - 120, y, 120, self.ROW_H - 10),
                                  "Sure?" if sure else "Delete", partial(self.delete, deck),
                                  size=22, color=(150, 50, 56) if sure else (90, 44, 60)))
            self.rows.append(row)

    def reload(self):
        self.decks = storage.list_decks()
        self.confirm_delete = None
        self.rebuild()

    def back(self):
        self.game.change(MainMenu(self.game))

    def pick(self, deck):
        if self.mode == "play":
            from .run_scenes import PathChoice
            self.game.change(PathChoice(self.game, RunState(deck, ASK_MODES[self.ask_index][0])))
        else:
            from .editor import DeckEditor
            self.game.change(DeckEditor(self.game, deck))

    def delete(self, deck):
        if self.confirm_delete is deck:
            storage.delete_deck(deck)
            self.message = f"Deleted '{deck.name}'."
            self.reload()
        else:
            self.confirm_delete = deck
            self.rebuild()

    def new_deck(self):
        names = {d.name for d in self.decks}
        name, i = "New Deck", 2
        while name in names:
            name, i = f"New Deck {i}", i + 1
        deck = storage.Deck(name)
        storage.save_deck(deck)
        from .editor import DeckEditor
        self.game.change(DeckEditor(self.game, deck))

    def import_files(self):
        count = storage.import_text_files()
        if count:
            self.message = f"Imported {count} deck(s) from the imports folder."
        else:
            self.message = "No .txt files with cards found in the imports/ folder."
        self.reload()

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.back()
            return
        if event.type == pygame.MOUSEWHEEL:
            self.scroll -= event.y * 40
            self.rebuild()
            return
        for b in self.static_buttons:
            if b.handle_event(event):
                return
        if event.type == pygame.MOUSEBUTTONDOWN and not self.LIST_RECT.collidepoint(event.pos):
            return
        for row in self.rows:
            for b in row:
                if b.handle_event(event):
                    return

    def draw(self, surf):
        draw_background(surf)
        title = "Choose a Deck to Study" if self.mode == "play" else "Your Decks"
        draw_text(surf, title, 52, S.ACCENT, (S.WIDTH // 2, 70), "center", bold=True)
        draw_panel(surf, self.LIST_RECT.inflate(30, 30), color=(30, 26, 46))
        if not self.decks:
            msg = "No decks yet. Go to Manage Decks to make one!" if self.mode == "play" \
                else "No decks yet. Click '+ New Deck' to make one."
            draw_text(surf, msg, 26, S.MUTED, self.LIST_RECT.center, "center")
        prev_clip = surf.get_clip()
        surf.set_clip(self.LIST_RECT)
        for row in self.rows:
            for b in row:
                b.draw(surf)
        surf.set_clip(prev_clip)
        for b in self.static_buttons:
            b.draw(surf)
        hint = ("Decks need at least 2 cards to play." if self.mode == "play"
                else "Tip: drop tab-separated .txt files (e.g. a Quizlet export) into imports/ and click Import.")
        draw_text(surf, self.message or hint, 20, S.MUTED, (S.WIDTH // 2, 614 if self.mode == "edit" else 676),
                  "center")
