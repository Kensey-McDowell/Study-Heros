from dataclasses import dataclass


@dataclass
class Player:
    max_hp: int = 30
    hp: int = 30
    attack: int = 5
    armor: int = 0
    crit_chance: float = 0.10
    time_limit: float = 20.0
    potions: int = 1
    hints: int = 1

    @property
    def alive(self):
        return self.hp > 0

    def heal(self, amount):
        self.hp = min(self.max_hp, self.hp + amount)

    def take_damage(self, amount):
        dmg = max(1, amount - self.armor)
        self.hp = max(0, self.hp - dmg)
        return dmg


@dataclass
class Enemy:
    name: str
    shape: str
    color: tuple
    max_hp: int
    attack: int
    kind: str = "normal"  # "normal", "elite" or "boss"

    def __post_init__(self):
        self.hp = self.max_hp

    @property
    def alive(self):
        return self.hp > 0

    @property
    def scale(self):
        return {"normal": 1.0, "elite": 1.2, "boss": 1.3}[self.kind]

    def take_damage(self, amount):
        self.hp = max(0, self.hp - amount)


NORMAL_ENEMIES = [
    ("Slime of Forgetting", "blob", (110, 200, 120)),
    ("Distraction Slime", "blob", (230, 140, 80)),
    ("Procrastination Bat", "bat", (120, 90, 160)),
    ("Pop Quiz Phantom", "ghost", (200, 210, 240)),
    ("Cramming Goblin", "goblin", (120, 180, 90)),
    ("All-Seeing Grader", "eye", (170, 70, 120)),
]

BOSSES = {
    "boss": ("Deadline Golem", "golem", (130, 120, 140)),
    "final": ("The Final Exam", "exam", (240, 236, 220)),
}


def make_enemy(floor, kind, rng):
    """kind is "normal", "elite", "boss" (mid-boss) or "final"."""
    hp = 12 + floor * 4
    atk = 3 + floor // 2
    if kind in BOSSES:
        name, shape, color = BOSSES[kind]
        hp = int(hp * (2.2 if kind == "boss" else 2.4))
        atk += 3
        return Enemy(name, shape, color, hp, atk, "boss")
    name, shape, color = rng.choice(NORMAL_ENEMIES)
    if kind == "elite":
        return Enemy("Elite " + name, shape, color, int(hp * 1.6), atk + 2, "elite")
    return Enemy(name, shape, color, hp, atk, "normal")
