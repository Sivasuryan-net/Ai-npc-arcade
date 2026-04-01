"""
companion_ai.py
---------------
Handles all Gemini AI communication for the companion NPC (Kha).
Restricted to game-related topics only via system instruction.
"""

import threading
import google.generativeai as genai
from dotenv import load_dotenv
import os

# Load .env from project root (../.env relative to this file) so it works
# even when the game is launched from the src directory.
PROJECT_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
ENV_PATH = os.path.join(PROJECT_ROOT, ".env")
load_dotenv(dotenv_path=ENV_PATH)

API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
if API_KEY:
    genai.configure(api_key=API_KEY)

SYSTEM_INSTRUCTION = """
You are Kha, a helpful companion in Chaos Projectile, an ancient
Egypt-themed 2D run-and-gun arcade game with RPG elements.

You ONLY answer questions about:
- Game controls and keybindings (mouse aim, WASD movement, gamepad setup)
- Level exits and how each exit affects character attributes
- Unlockable actions and character progression/RPG elements
- Game lore (ancient Egypt setting, Art Nouveau visuals, Cthulhu/Lovecraft influences)
- How to install, run, or compile the game
- Enemies, enemy power/strength, levels, and general gameplay tips
- Navigation advice like which route/path to take in a level

Rules:
- Keep responses SHORT (2-3 sentences max) since they appear as in-game speech bubbles
- Use clear, normal English that is easy to understand
- If asked ANYTHING outside game topics, respond exactly with:
    "I think you have to explore to have more fun."
- Never break character or mention Gemini, AI, or APIs
"""

model = None
if API_KEY:
    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        system_instruction=SYSTEM_INSTRUCTION
    )


def _local_fallback_reply(question: str) -> str:
    """Offline fallback so companion always answers even without API access."""
    q = (question or "").lower()

    if any(k in q for k in ["control", "key", "move", "aim", "shoot", "attack"]):
        return "Press WASD to move, aim with the mouse, and strike while moving with purpose."
    if any(k in q for k in ["exit", "portal", "door", "level"]):
        return "Seek each level's exit with care, for every path may shape your attributes."
    if any(k in q for k in ["companion", "kha", "talk", "chat"]):
        return "Press T to commune with me, and Enter to send your words through the sands."
    if any(k in q for k in ["install", "run", "start", "launch", "compile"]):
        return "From src, run the game with Python 3.11 and ensure pygame is installed."
    if any(k in q for k in ["enemy", "boss", "power", "strength", "damage", "health"]):
        return "Enemy power rises deeper in each level. Keep moving, dodge first, then attack when you have a safe opening."
    if any(k in q for k in ["which way", "where", "go", "path", "route", "direction"]):
        return "Follow the path toward the level exit and avoid getting surrounded. If two routes appear, choose the one with more space to move."

    return "I think you have to explore to have more fun."


class CompanionAI:
    def __init__(self):
        self.chat = model.start_chat(history=[]) if model is not None else None
        self.response = ""
        self.is_thinking = False
        self._thread = None

    def ask(self, question: str, callback=None):
        """
        Sends a question to Gemini in a background thread.
        Calls callback(response_text) when done — so the game loop never freezes.
        """
        if self.is_thinking:
            return  # ignore if already waiting for a response

        self.is_thinking = True
        self.response = ""

        def _fetch():
            try:
                if self.chat is None:
                    self.response = _local_fallback_reply(question)
                    return
                result = self.chat.send_message(question)
                self.response = result.text.strip()
            except Exception as e:
                self.response = _local_fallback_reply(question)
                print(f"[CompanionAI] Error: {e}")
            finally:
                self.is_thinking = False
                if callback:
                    callback(self.response)

        self._thread = threading.Thread(target=_fetch, daemon=True)
        self._thread.start()

    def reset_chat(self):
        """Resets conversation history (call on new level/game reset)."""
        self.chat = model.start_chat(history=[]) if model is not None else None
        self.response = ""
        self.is_thinking = False
