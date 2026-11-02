"""State for a single roguelike run, plus upgrades and the shared status bar."""
import random
from dataclasses import dataclass
from typing import Callable

import pygame

from . import settings as S
from .entities import Player
from .quiz import QuizEngine
from .ui import draw_bar, draw_text, ellipsize, font

NODE_INFO = {
    "battle": ("Battle", "Fight a monster. Win to choose an upgrade.", (150, 60, 70)),
    "elite": ("Elite", "Tougher foe and less time per question. Bonus hint on victory.", (110, 70, 170)),
    "rest": ("Campfire", "Heal up or train your attack.", (170, 100, 40)),
    "treasure": ("Treasure", "A free item, no fighting required.", (160, 130, 40)),
    "boss": ("BOSS", "The Deadline Golem blocks the way.", (170, 40, 50)),
    "final": ("FINAL BOSS", "The Final Exam. Good luck.", (170, 40, 50)),
}


@dataclass
class Upgrade:
    name: str
    desc: str
    apply: Callable[[Player], None]


def _attack(p): p.attack += 2
def _max_hp(p): p.max_hp += 8; p.heal(8)
def _potion(p): p.potions += 1
def _hints(p): p.hints += 2
def _crit(p): p.crit_chance = min(0.6, p.crit_chance + 0.10)
def _time(p): p.time_limit += 4
def _armor(p): p.armor += 1
def _full_heal(p): p.hp = p.max_hp


UPGRADES = [
    Upgrade("Sharpened Pencil", "+2 attack damage.", _attack),
    Upgrade("Study Snack", "+8 max HP and heal 8.", _max_hp),
    Upgrade("Healing Potion", "+1 potion. Press P in battle to heal 40% HP.", _potion),
    Upgrade("Cheat Sheet", "+2 hints. Press H in battle to remove two wrong answers.", _hints),
    Upgrade("Lucky Eraser", "+10% chance to land a critical hit for double damage.", _crit),
    Upgrade("Extra Time", "+4 seconds to answer each question.", _time),
    Upgrade("Binder Armor", "Take 1 less damage from every hit.", _armor),
    Upgrade("Power Nap", "Restore all of your HP.", _full_heal),
]
TREASURE_POOL = [u for u in UPGRADES if u.name in
                 ("Sharpened Pencil", "Study Snack", "Healing Potion", "Cheat Sheet", "Lucky Eraser")]


class RunState:
    TOTAL_FLOORS = 10
    MIDBOSS_FLOOR = 5

    def __init__(self, deck, ask_mode, seed=None):
        self.rng = random.Random(seed)
        self.deck = deck
        self.ask_mode = ask_mode
        self.player = Player()
        self.quiz = QuizEngine(deck.cards, ask_mode, self.rng)
        self.floor = 0  # Floors completed so far.
        self.kills = 0
        self.best_combo = 0

    @property
    def current_floor(self):
        return min(self.floor + 1, self.TOTAL_FLOORS)

    def next_choices(self):
        f = self.floor + 1
        if f == self.TOTAL_FLOORS:
            return ["final"]
        if f == self.MIDBOSS_FLOOR:
            return ["boss"]
        if f == 1:
            return ["battle"]
        extras = ["rest", "treasure"] + (["elite"] if f > 2 else [])
        count = self.rng.choice((1, 2))
        picks = self.rng.sample(extras, count)
        if f + 1 in (self.MIDBOSS_FLOOR, self.TOTAL_FLOORS) and "rest" not in picks:
            picks[0] = "rest"  # Always offer a campfire before a boss.
        options = ["battle"] + picks
        self.rng.shuffle(options)
        return options


def draw_status_bar(surf, run):
    p = run.player
    pygame.draw.rect(surf, (16, 13, 26), (0, 0, S.WIDTH, 52))
    pygame.draw.line(surf, S.BORDER, (0, 52), (S.WIDTH, 52), 2)
    draw_text(surf, "HP", 22, S.BAD, (16, 13), bold=True)
    draw_bar(surf, (52, 14, 200, 24), p.hp / p.max_hp, S.BAD, label=f"{p.hp}/{p.max_hp}")
    stats = [f"ATK {p.attack}", f"ARMOR {p.armor}", f"CRIT {round(p.crit_chance * 100)}%",
             f"TIME {p.time_limit:.0f}s", f"POTIONS {p.potions}", f"HINTS {p.hints}"]
    x = 272
    for stat in stats:
        x = draw_text(surf, stat, 20, S.TEXT, (x, 15)).right + 20
    floor_rect = draw_text(surf, f"Floor {run.current_floor}/{run.TOTAL_FLOORS}", 20, S.ACCENT,
                           (S.WIDTH - 16, 15), "topright", bold=True)
    name = ellipsize(run.deck.name, font(20), max(40, floor_rect.left - x - 20))
    draw_text(surf, name, 20, S.MUTED, (floor_rect.left - 16, 15), "topright")
