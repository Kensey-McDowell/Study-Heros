import pygame

from .. import settings as S
from .. import storage
from ..ui import (Button, TextInput, draw_background, draw_panel, draw_text, draw_wrapped,
                  ellipsize, font, get_clipboard)
from .base import Scene


class DeckEditor(Scene):
    LIST_RECT = pygame.Rect(690, 130, 550, 490)
    ROW_H = 64

    def __init__(self, game, deck):
        super().__init__(game)
        self.deck = deck
        self.name_input = TextInput((40, 70, 600, 50), deck.name, "Deck name", max_len=60, size=28)
        self.term_input = TextInput((40, 180, 600, 52), "", "Term  (e.g. Mitochondria)")
        self.def_input = TextInput((40, 275, 600, 52), "", "Definition  (e.g. Powerhouse of the cell)")
        self.inputs = [self.name_input, self.term_input, self.def_input]
        self.term_input.active = True
        self.editing = None  # Index of the card being edited, if any.
        self.add_btn = Button((40, 345, 290, 56), "Add Card", self.submit_card, color=(50, 100, 70))
        self.clear_btn = Button((350, 345, 290, 56), "Clear", self.clear_form)
        self.paste_btn = Button((40, 520, 600, 52), "Paste cards from clipboard", self.paste_cards)
        self.back_btn = Button((40, 640, 240, 52), "Save & Back", self.back)
        self.buttons = [self.add_btn, self.clear_btn, self.paste_btn, self.back_btn]
        self.scroll = 0
        self.message = ""

    # --- Actions ---

    def save(self):
        self.deck.name = self.name_input.text.strip() or "Untitled Deck"
        storage.save_deck(self.deck)

    def back(self):
        self.save()
        from .menu import DeckSelect
        self.game.change(DeckSelect(self.game, "edit"))

    def focus(self, target):
        for inp in self.inputs:
            inp.active = inp is target

    def clear_form(self):
        self.term_input.text = ""
        self.def_input.text = ""
        self.editing = None
        self.focus(self.term_input)

    def submit_card(self):
        term, definition = self.term_input.text.strip(), self.def_input.text.strip()
        if not term or not definition:
            self.message = "A card needs both a term and a definition."
            return
        card = {"term": term, "definition": definition}
        if self.editing is not None:
            self.deck.cards[self.editing] = card
            self.message = "Card updated."
        else:
            self.deck.cards.append(card)
            self.message = f"Added '{term}'."
            self.scroll = self.max_scroll()
        self.save()
        self.clear_form()

    def paste_cards(self):
        cards = storage.parse_card_lines(get_clipboard())
        if not cards:
            self.message = "Clipboard has no 'term [Tab] definition' lines."
            return
        self.deck.cards.extend(cards)
        self.save()
        self.scroll = self.max_scroll()
        self.message = f"Pasted {len(cards)} card(s)."

    def edit_card(self, index):
        card = self.deck.cards[index]
        self.editing = index
        self.term_input.text = card["term"]
        self.def_input.text = card["definition"]
        self.focus(self.term_input)

    def delete_card(self, index):
        removed = self.deck.cards.pop(index)
        if self.editing == index:
            self.clear_form()
        elif self.editing is not None and self.editing > index:
            self.editing -= 1
        self.save()
        self.scroll = min(self.scroll, self.max_scroll())
        self.message = f"Deleted '{removed['term']}'."

    def max_scroll(self):
        return max(0, len(self.deck.cards) * self.ROW_H - (self.LIST_RECT.height - 50))

    # --- Events ---

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.back()
                return
            if event.key == pygame.K_TAB:
                active = next((i for i, inp in enumerate(self.inputs) if inp.active), 0)
                step = -1 if event.mod & pygame.KMOD_SHIFT else 1
                self.focus(self.inputs[(active + step) % len(self.inputs)])
                return
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                if self.term_input.active:
                    self.focus(self.def_input)
                elif self.def_input.active:
                    self.submit_card()
                elif self.name_input.active:
                    self.save()
                    self.focus(self.term_input)
                return
        if event.type == pygame.MOUSEWHEEL:
            if self.LIST_RECT.collidepoint(pygame.mouse.get_pos()):
                self.scroll = max(0, min(self.max_scroll(), self.scroll - event.y * 40))
            return
        for b in self.buttons:
            if b.handle_event(event):
                return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.click_list(event.pos):
            return
        for inp in self.inputs:
            inp.handle_event(event)

    def row_rect(self, i):
        top = self.LIST_RECT.top + 50 + i * self.ROW_H - self.scroll
        return pygame.Rect(self.LIST_RECT.left + 10, top, self.LIST_RECT.width - 20, self.ROW_H - 8)

    def delete_rect(self, row):
        return pygame.Rect(row.right - 46, row.centery - 18, 36, 36)

    def click_list(self, pos):
        body = pygame.Rect(self.LIST_RECT.left, self.LIST_RECT.top + 50, self.LIST_RECT.width,
                           self.LIST_RECT.height - 50)
        if not body.collidepoint(pos):
            return False
        for i in range(len(self.deck.cards)):
            row = self.row_rect(i)
            if row.collidepoint(pos):
                if self.delete_rect(row).collidepoint(pos):
                    self.delete_card(i)
                else:
                    self.edit_card(i)
                return True
        return False

    def update(self, dt):
        # Auto-save deck renames.
        name = self.name_input.text.strip()
        if name and name != self.deck.name:
            self.save()

    # --- Drawing ---

    def draw(self, surf):
        draw_background(surf)
        draw_text(surf, "Deck name", 22, S.MUTED, (40, 40))
        draw_text(surf, "Term", 22, S.MUTED, (40, 150))
        draw_text(surf, "Definition", 22, S.MUTED, (40, 245))
        for inp in self.inputs:
            inp.draw(surf)
        self.add_btn.label = "Update Card" if self.editing is not None else "Add Card"
        for b in self.buttons:
            b.draw(surf)
        draw_wrapped(surf, "Enter moves to the next box and saves the card. Tab switches boxes. Ctrl+V pastes.",
                     18, S.MUTED, pygame.Rect(40, 410, 600, 30), align="left")
        draw_text(surf, "Bulk add (works with a Quizlet export)", 22, S.ACCENT, (40, 460), bold=True)
        draw_wrapped(surf, "Copy lines like 'term [Tab] definition' (or 'term - definition'), one card per line, "
                     "then click below.", 18, S.MUTED, pygame.Rect(40, 488, 600, 30), align="left")
        if self.message:
            draw_text(surf, self.message, 22, S.ACCENT, (40, 592))

        draw_panel(surf, self.LIST_RECT, color=(30, 26, 46))
        draw_text(surf, f"Cards ({len(self.deck.cards)})", 26, S.TEXT,
                  (self.LIST_RECT.left + 16, self.LIST_RECT.top + 10), bold=True)
        draw_text(surf, "Click a card to edit it", 18, S.MUTED,
                  (self.LIST_RECT.right - 16, self.LIST_RECT.top + 16), "topright")
        prev_clip = surf.get_clip()
        surf.set_clip(pygame.Rect(self.LIST_RECT.left, self.LIST_RECT.top + 48,
                                  self.LIST_RECT.width, self.LIST_RECT.height - 52))
        mouse = pygame.mouse.get_pos()
        for i, card in enumerate(self.deck.cards):
            row = self.row_rect(i)
            if row.bottom < self.LIST_RECT.top or row.top > self.LIST_RECT.bottom:
                continue
            color = (80, 70, 120) if i == self.editing else (54, 48, 80)
            if row.collidepoint(mouse):
                color = tuple(c + 14 for c in color)
            pygame.draw.rect(surf, color, row, border_radius=8)
            text_w = row.width - 70
            draw_text(surf, ellipsize(card["term"], font(22, True), text_w), 22, S.TEXT,
                      (row.left + 12, row.top + 4), bold=True)
            draw_text(surf, ellipsize(card["definition"], font(18), text_w), 18, S.MUTED,
                      (row.left + 12, row.top + 32))
            d = self.delete_rect(row)
            pygame.draw.rect(surf, S.BAD_DARK if not d.collidepoint(mouse) else S.BAD, d, border_radius=6)
            draw_text(surf, "X", 20, S.TEXT, d.center, "center", bold=True)
        surf.set_clip(prev_clip)
