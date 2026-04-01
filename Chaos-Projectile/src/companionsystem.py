"""
Optional companion integration system.

Bridges the event-driven core game with the optional companion modules in
../files without hard-failing when AI dependencies are unavailable.
"""

import os
import sys

import pygame

import events


def _wrap_text(text, font, max_width):
    words = (text or "").split()
    lines = []
    current = ""
    for word in words:
        candidate = (current + " " + word).strip()
        if font.size(candidate)[0] <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [""]


class _FallbackCompanionAI(object):
    """Simple fallback when Gemini dependencies or API key are unavailable."""

    def __init__(self):
        self.is_thinking = False

    def ask(self, question, callback=None):
        del question
        if callback:
            callback("The sands are quiet... install AI deps to awaken me.")

    def reset_chat(self):
        return None


def _load_companion_modules():
    """Try importing companion modules from ../files."""
    files_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "files"))
    if files_dir not in sys.path:
        sys.path.append(files_dir)

    npc_cls = None
    ai_cls = None

    try:
        from companion_npc import CompanionNPC
        npc_cls = CompanionNPC
    except Exception as exc:
        print("[CompanionSystem] companion_npc unavailable: %s" % exc)

    try:
        from companion_ai import CompanionAI
        ai_cls = CompanionAI
    except Exception as exc:
        print("[CompanionSystem] companion_ai unavailable: %s" % exc)

    return npc_cls, ai_cls


class CompanionSystem(object):
    """Event listener that updates and draws a companion NPC above main render."""

    def __init__(self, event_manager, world):
        self.event_manager = event_manager
        self.world = world
        self.screen = world.screen
        self.event_manager.register_listener(self)

        self._npc_cls, self._ai_cls = _load_companion_modules()
        self._font = None
        self._ai = None
        self._npc = None
        self._reply_text = ""
        self._reply_until_ms = 0

    def _set_reply_overlay(self, text, duration_ms=7000):
        self._reply_text = (text or "").strip()
        if self._reply_text:
            self._reply_until_ms = pygame.time.get_ticks() + duration_ms
        else:
            self._reply_until_ms = 0

    def _draw_reply_overlay(self):
        if not self._reply_text:
            return
        if pygame.time.get_ticks() > self._reply_until_ms:
            self._reply_text = ""
            self._reply_until_ms = 0
            return

        width = self.screen.get_width() - 80
        x = 40
        lines = _wrap_text(self._reply_text, self._font, width - 24)
        height = 16 + len(lines) * 18 + 10
        y = self.screen.get_height() - height - 24

        panel = pygame.Rect(x, y, width, height)
        pygame.draw.rect(self.screen, (20, 15, 8), panel, border_radius=8)
        pygame.draw.rect(self.screen, (255, 215, 0), panel, 2, border_radius=8)

        line_y = y + 12
        for line in lines:
            surf = self._font.render(line, True, (255, 245, 220))
            self.screen.blit(surf, (x + 12, line_y))
            line_y += 18

    def _draw_talk_hint(self):
        hint = "Press T to talk with Kha"
        text = self._font.render(hint, True, (255, 245, 220))
        pad_x = 14
        pad_y = 10
        panel = pygame.Rect(14, self.screen.get_height() - 42, text.get_width() + pad_x * 2, 30)
        pygame.draw.rect(self.screen, (20, 15, 8), panel, border_radius=8)
        pygame.draw.rect(self.screen, (255, 215, 0), panel, 1, border_radius=8)
        self.screen.blit(text, (panel.x + pad_x, panel.y + pad_y - 1))

    def _ensure_ready(self):
        if self._npc is not None:
            return True

        if self._npc_cls is None or self.world.player is None:
            return False

        player_sprite = self.world.appearance.get(self.world.player)
        if player_sprite is None or not hasattr(player_sprite, "rect"):
            return False

        if self._font is None:
            self._font = pygame.font.SysFont("freesansbold", 14)

        if self._ai is None:
            if self._ai_cls is None:
                self._ai = _FallbackCompanionAI()
            else:
                try:
                    self._ai = self._ai_cls()
                except Exception as exc:
                    print("[CompanionSystem] AI init failed, using fallback: %s" % exc)
                    self._ai = _FallbackCompanionAI()

        try:
            self._npc = self._npc_cls(player_sprite, self._ai, self._font)
        except Exception as exc:
            print("[CompanionSystem] NPC init failed: %s" % exc)
            self._npc = None
            return False

        return True

    def notify(self, event):
        if isinstance(event, events.TickEvent):
            if self.world.game_paused:
                return
            if self._ensure_ready():
                self._npc.update()
                self._npc.draw(self.screen)
                self._draw_talk_hint()
                self._draw_reply_overlay()
                pygame.display.flip()

        elif isinstance(event, events.TalkToCompanionEvent):
            if self._ensure_ready():
                if self._ai is not None and self._ai.is_thinking:
                    return

                # Open chat input directly so T always triggers the chat box,
                # even when proximity state is stale.
                question = self._npc._get_text_input(self.screen)
                if question and question.strip():
                    self._npc.say("...")
                    self._set_reply_overlay("Kha is listening...")

                    def _on_reply(text):
                        self._npc.say(text)
                        self._set_reply_overlay(text)

                    self._ai.ask(question, callback=_on_reply)

        elif isinstance(event, events.ResetWorld):
            if self._ai is not None:
                self._ai.reset_chat()
