[README.md](https://github.com/user-attachments/files/24919519/README.md)
# Galactic Traveler 🚀 (Pygame Space Invaders++ / Galaga-like)

A wave-based arcade shooter with:
- **Enemy waves & formation patterns** (line, V, sine drift, ring)
- **Structured enemy behavior** via a lightweight **state machine**
- **Power-ups** (spread shot, rapid fire, shield, score multiplier)
- **Score multipliers** + a clean **HUD layer**
- Keyboard controls + pause/menu/game-over screens

## Quick start

### 1) Create a virtual environment (recommended)
```bash
python -m venv .venv
source .venv/bin/activate   # macOS/Linux
# .venv\Scripts\activate  # Windows PowerShell
```

### 2) Install dependencies
```bash
pip install -r requirements.txt
```

### 3) Run
```bash
python main.py
```

## Controls
- **Move:** Arrow keys or WASD
- **Shoot:** Space
- **Pause:** P or Esc
- **Confirm/Start:** Enter
- **Quit:** Q (from menus)

## Design notes (developer-focused)
- `src/states.py` implements a simple **game state machine**:
  - `MenuState` → `PlayState` → `GameOverState` (+ `PauseState`)
- `src/patterns.py` defines **wave patterns**. A `WaveManager` schedules spawns and ramps difficulty.
- `src/entities.py` defines all game entities and collision shapes.
- No external art assets required: everything is drawn with simple shapes for portability.

## Extending the game
Ideas:
- Add boss fights every N waves
- New weapons (laser beam, homing missiles)
- Enemy bullet patterns (fan, burst)
- Audio (SFX/music) and sprite art
- Difficulty modifiers and leaderboard persistence

---

**Project name:** Galactic Traveler 
