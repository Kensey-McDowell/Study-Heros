"""Loading and saving flashcard decks as JSON files."""
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from .settings import DECK_DIR, IMPORT_DIR


@dataclass
class Deck:
    name: str
    cards: list = field(default_factory=list)  # [{"term": str, "definition": str}]
    path: Path | None = None


def list_decks():
    DECK_DIR.mkdir(parents=True, exist_ok=True)
    decks = []
    for p in DECK_DIR.glob("*.json"):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        cards = [
            {"term": str(c.get("term", "")), "definition": str(c.get("definition", ""))}
            for c in data.get("cards", [])
            if isinstance(c, dict)
        ]
        decks.append(Deck(str(data.get("name", p.stem)), cards, p))
    decks.sort(key=lambda d: d.name.lower())
    return decks


def _unique_path(name):
    base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "deck"
    path = DECK_DIR / f"{base}.json"
    i = 2
    while path.exists():
        path = DECK_DIR / f"{base}-{i}.json"
        i += 1
    return path


def save_deck(deck):
    DECK_DIR.mkdir(parents=True, exist_ok=True)
    if deck.path is None:
        deck.path = _unique_path(deck.name)
    data = {"name": deck.name, "cards": deck.cards}
    deck.path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def delete_deck(deck):
    if deck.path and deck.path.exists():
        deck.path.unlink()


def parse_card_lines(text):
    """Parse 'term<TAB>definition' lines (Quizlet export format).

    Also accepts ' - ' or ':' as the separator. Only the first separator splits.
    """
    cards = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        for sep in ("\t", " - ", " – ", ":", ","):
            if sep in line:
                term, definition = line.split(sep, 1)
                term, definition = term.strip(), definition.strip()
                if term and definition:
                    cards.append({"term": term, "definition": definition})
                break
    return cards


def import_text_files():
    """Turn every .txt file in imports/ into a deck. Returns the number of decks made."""
    IMPORT_DIR.mkdir(parents=True, exist_ok=True)
    count = 0
    for p in IMPORT_DIR.glob("*.txt"):
        cards = parse_card_lines(p.read_text(encoding="utf-8", errors="ignore"))
        if not cards:
            continue
        save_deck(Deck(p.stem.replace("_", " "), cards))
        p.rename(p.with_suffix(".imported"))
        count += 1
    return count
