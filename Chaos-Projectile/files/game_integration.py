"""
game_integration.py
-------------------
This file is NOT a standalone script.
It shows you exactly WHERE and WHAT to add inside your existing src/game.py.

Search for the commented landmarks (e.g. "# >>> PATCH 1") in your game.py
and insert the corresponding code blocks.
"""


# =============================================================================
# >>> PATCH 1 — Top of game.py, with the other imports
# =============================================================================
from companion_ai  import CompanionAI
from companion_npc import CompanionNPC


# =============================================================================
# >>> PATCH 2 — After pygame.init() and font/screen setup, before the game loop
#               (where you create your player sprite)
# =============================================================================

# --- Companion setup ---------------------------------------------------------
companion_ai  = CompanionAI()
companion_font = pygame.font.SysFont("freesansbold", 14)   # or your existing font

# Pass your actual player sprite object here
companion_npc = CompanionNPC(
    player       = player,          # <-- your existing player sprite variable
    companion_ai = companion_ai,
    font         = companion_font,
)

# Add NPC to your sprite groups so it gets updated with everything else
# (use whichever group makes sense in your project — all_sprites is common)
all_sprites.add(companion_npc)      # <-- adjust group name if needed


# =============================================================================
# >>> PATCH 3 — Inside your event loop  (for event in pygame.event.get(): ...)
# =============================================================================
companion_npc.handle_event(event, screen)


# =============================================================================
# >>> PATCH 4 — Inside your main draw section, AFTER drawing map + player
#               so the NPC and bubble render on top
# =============================================================================
companion_npc.draw(screen)


# =============================================================================
# >>> PATCH 5 — On game reset (BACKSPACE handler you already have)
#               Resets Gemini chat history for the new run
# =============================================================================
companion_ai.reset_chat()
