# Study Heroes

A roguelike RPG where your flashcards are your weapon. Build decks of terms and definitions,
then battle through 10 floors of monsters. Every attack is a quiz question.

## Running

```
pip install -r requirements.txt
python main.py
```

## How to play

1. **Manage Decks** → **+ New Deck**. Type a term, press Enter, type the definition, press Enter.
   - **Bulk add:** copy lines like `term<TAB>definition` (a Quizlet export works) and click
     *Paste cards from clipboard*.
   - **Import files:** drop `.txt` files in `imports/` and click *Import .txt*.
2. **Start Adventure** → choose a deck and a question direction (term → definition, the
   reverse, or mixed).
3. On each floor, pick a path: **Battle**, **Elite**, **Campfire** or **Treasure**. Floor 5 is
   the Deadline Golem, and floor 10 is The Final Exam.

### In battle

| Action | Key |
| --- | --- |
| Answer | Click, or `1`–`4` |
| Hint (removes two wrong answers) | `H` |
| Potion (heal 40%) | `P` |
| Continue after a miss | `Space` / click |

- **Correct answer:** you attack. Answering in the first third of the timer is **QUICK!**
  (+50% damage). Streaks build a **combo**, and crits deal double damage.
- **Wrong answer or time out:** the monster hits you, and the correct answer is shown so you
  can learn it.
- Cards you miss come back more often during the run. Campfires and the end screen list your
  trickiest cards.

## Project layout

```
main.py                    entry point
study_heroes/
  game.py                  main loop and scene switching
  settings.py              screen size, colors, paths
  ui.py                    buttons, text inputs, text helpers
  storage.py               deck save/load/import (data/decks/*.json)
  quiz.py                  question generation + miss-weighted card picking
  entities.py              player, enemies, enemy scaling
  run.py                   run state, map choices, upgrades, status bar
  sprites.py               procedurally drawn characters (no image assets)
  scenes/                  menu, deck editor, battle, path/reward/rest/treasure/game over
data/decks/                your decks (JSON)
```
