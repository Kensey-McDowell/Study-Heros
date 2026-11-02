from pathlib import Path

WIDTH, HEIGHT = 1280, 720
FPS = 60
TITLE = "Study Heroes"

ROOT = Path(__file__).resolve().parent.parent
DECK_DIR = ROOT / "data" / "decks"
IMPORT_DIR = ROOT / "imports"

# Colors
BG = (22, 18, 34)
BG2 = (44, 32, 70)
PANEL = (44, 38, 66)
PANEL_LIGHT = (64, 56, 96)
BORDER = (92, 82, 132)
TEXT = (236, 232, 246)
MUTED = (156, 146, 182)
ACCENT = (255, 196, 72)
GOOD = (88, 204, 112)
GOOD_DARK = (46, 120, 66)
BAD = (226, 78, 78)
BAD_DARK = (130, 44, 50)
BLUE = (86, 156, 255)
PURPLE = (170, 110, 255)
DISABLED = (50, 46, 62)
