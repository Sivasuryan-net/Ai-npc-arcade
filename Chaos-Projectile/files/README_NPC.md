# Kha — AI Companion NPC for Chaos Projectile

## Files
```
src/
  companion_ai.py       ← Gemini API wrapper (restricted to game topics)
  companion_npc.py      ← Pygame sprite, follow logic, speech bubble, input UI
  game_integration.py   ← Copy-paste guide: exactly where to edit game.py
.env.example            ← Rename to .env and add your API key
requirements_npc.txt    ← Two new pip dependencies
assets/
  kha_npc.png           ← (optional) Your custom NPC sprite (40×48px recommended)
```

---

## Setup

### 1. Install dependencies
```bash
pip install -r requirements_npc.txt
```

### 2. Get a Gemini API key
- Visit https://aistudio.google.com/app/apikey
- Create a free key

### 3. Set up your .env file
```bash
cp .env.example .env
# Edit .env and paste your key
```

### 4. Patch game.py
Open `src/game_integration.py` and follow the 5 labelled patches
in order — each one tells you exactly where in game.py to add the code.

### 5. (Optional) Add a custom NPC sprite
Place a `kha_npc.png` file inside the `assets/` folder.
- Recommended size: **40×48 px**, transparent background (.png)
- If the file is missing, a built-in gold placeholder sprite is used automatically

---

## Controls
| Key | Action |
|-----|--------|
| Walk near Kha | `[T] Talk to Kha` hint appears |
| **T** | Opens text input box |
| **Enter** | Sends question to Gemini |
| **Esc** | Cancels input |

---

## Behaviour
- Kha follows the player with a smooth lag
- Responses appear as a gold speech bubble above Kha
- Bubble auto-hides after ~6 seconds
- Gemini calls run in a background thread — game never freezes
- Kha only answers game-related questions; everything else gets deflected in character
- Chat history resets on game reset (BACKSPACE)

---

## Troubleshooting
| Problem | Fix |
|---------|-----|
| `GEMINI_API_KEY not set` | Check your `.env` file is in project root |
| NPC doesn't appear | Make sure `all_sprites.add(companion_npc)` uses your actual group name |
| Bubble goes off screen | Already handled — bubble is clamped to screen width |
| Game freezes on question | You may have called `ai.ask()` on the main thread — use the provided `handle_event` method |
