"""
companion_npc.py
----------------
CompanionNPC sprite that follows the player, renders a speech bubble,
and triggers interaction with CompanionAI on keypress.
"""

import pygame
import os


BUBBLE_WIDTH      = 260
BUBBLE_PADDING    = 10
BUBBLE_LINE_H     = 20
BUBBLE_DURATION   = 360        # frames (~6s at 60fps)
FOLLOW_OFFSET_X   = -55        # NPC appears left of player
FOLLOW_OFFSET_Y   = 0
FOLLOW_SPEED      = 0.12       # 0.0–1.0, lower = smoother/slower
INTERACT_RADIUS   = 90         # pixels — how close player must be
INTERACT_KEY      = pygame.K_t

# Colours (Egypt-themed)
BUBBLE_BG         = (28, 18,  8)
BUBBLE_BORDER     = (255, 215, 0)   # gold
BUBBLE_TEXT       = (255, 245, 220) # warm white
THINKING_TEXT     = (180, 160, 100)
HINT_TEXT         = (255, 215, 0)
CHAT_PANEL_BG     = (18, 12, 6, 232)
CHAT_PANEL_BORDER = (255, 215, 0)
CHAT_LABEL_TEXT   = (255, 232, 180)
ANGEL_FOLLOW_Y    = -86


def _wrap_text(text: str, font: pygame.font.Font, max_width: int) -> list[str]:
    """Word-wraps text to fit inside max_width pixels."""
    words = text.split()
    lines, current = [], ""
    for word in words:
        test = (current + " " + word).strip()
        if font.size(test)[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [""]


class CompanionNPC(pygame.sprite.Sprite):
    """
    A companion sprite that:
      - follows the player smoothly
      - shows a [T] hint when the player is nearby
      - opens a text input box on T press
      - displays Gemini AI responses as a speech bubble
    """

    def __init__(self, player: pygame.sprite.Sprite, companion_ai, font: pygame.font.Font):
        super().__init__()

        self.player       = player
        self.ai           = companion_ai
        self.font         = font

        # --- Sprite image -------------------------------------------------
        # Try to load a custom sprite; fall back to a coloured placeholder
        asset_path = os.path.join("assets", "kha_npc.png")
        if os.path.exists(asset_path):
            self.image = pygame.image.load(asset_path).convert_alpha()
        else:
            self.image = self._make_placeholder_sprite()

        self.rect = self.image.get_rect()
        # Start next to the player
        self.rect.x = player.rect.x + FOLLOW_OFFSET_X
        self.rect.y = player.rect.y + FOLLOW_OFFSET_Y

        # Smooth-follow uses floats internally
        self._float_x = float(self.rect.x)
        self._float_y = float(self.rect.y)

        # --- Dialogue state -----------------------------------------------
        self.dialogue_text  = ""
        self.show_bubble    = False
        self.bubble_timer   = 0
        self.is_near_player = False
        self.angel_portrait = self._load_angel_portrait()

    # ------------------------------------------------------------------
    # Placeholder sprite (golden ankh-like shape, 40×48 px)
    # Replace this with your actual kha_npc.png asset
    # ------------------------------------------------------------------
    def _make_placeholder_sprite(self) -> pygame.Surface:
        surf = pygame.Surface((40, 48), pygame.SRCALPHA)
        gold  = (255, 215,   0, 255)
        dark  = ( 80,  50,  10, 255)
        # body
        pygame.draw.rect(surf, dark, (14, 20, 12, 24), border_radius=4)
        # head circle
        pygame.draw.circle(surf, gold, (20, 14), 10)
        pygame.draw.circle(surf, dark, (20, 14),  7)
        # eye
        pygame.draw.circle(surf, gold, (20, 14),  3)
        # arms
        pygame.draw.rect(surf, dark, (4, 26, 32, 6), border_radius=3)
        # legs
        pygame.draw.rect(surf, dark, (12, 42, 6, 6), border_radius=2)
        pygame.draw.rect(surf, dark, (22, 42, 6, 6), border_radius=2)
        # border glow
        pygame.draw.circle(surf, gold, (20, 14), 10, 2)
        return surf

    def _load_angel_portrait(self) -> pygame.Surface:
        """Load Anglepngg.png from project root; fallback to generated portrait."""
        angel_path = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "Anglepngg.png"))
        if os.path.exists(angel_path):
            try:
                image = pygame.image.load(angel_path).convert_alpha()
                return pygame.transform.smoothscale(image, (96, 96))
            except Exception:
                pass

        # Fallback stylized portrait if asset loading fails.
        surf = pygame.Surface((96, 96), pygame.SRCALPHA)
        gold = (255, 215, 0, 255)
        ivory = (255, 245, 220, 255)
        dark = (46, 30, 10, 255)
        pygame.draw.ellipse(surf, gold, (18, 4, 60, 18), 3)
        pygame.draw.polygon(surf, ivory, [(48, 44), (10, 34), (6, 62), (34, 56)])
        pygame.draw.polygon(surf, ivory, [(48, 44), (86, 34), (90, 62), (62, 56)])
        pygame.draw.circle(surf, gold, (48, 34), 13)
        pygame.draw.polygon(surf, dark, [(48, 50), (30, 84), (66, 84)])
        pygame.draw.polygon(surf, gold, [(48, 54), (39, 80), (57, 80)], 2)
        return surf

    # ------------------------------------------------------------------
    # Update — called every frame from the game loop
    # ------------------------------------------------------------------
    def update(self):
        # Smooth-follow player
        target_x = self.player.rect.x + FOLLOW_OFFSET_X
        target_y = self.player.rect.y + FOLLOW_OFFSET_Y
        self._float_x += (target_x - self._float_x) * FOLLOW_SPEED
        self._float_y += (target_y - self._float_y) * FOLLOW_SPEED
        self.rect.x = int(self._float_x)
        self.rect.y = int(self._float_y)

        # Proximity check
        dist = pygame.Vector2(self.player.rect.center).distance_to(self.rect.center)
        self.is_near_player = dist < INTERACT_RADIUS

        # Bubble countdown
        if self.show_bubble and not self.ai.is_thinking:
            self.bubble_timer -= 1
            if self.bubble_timer <= 0:
                self.show_bubble = False

    # ------------------------------------------------------------------
    # Handle pygame events — call this from your event loop
    # Returns True if the input box was opened this frame
    # ------------------------------------------------------------------
    def handle_event(self, event: pygame.event.Event, screen: pygame.Surface) -> bool:
        if (event.type == pygame.KEYDOWN
                and event.key == INTERACT_KEY
                and self.is_near_player
                and not self.ai.is_thinking):
            question = self._get_text_input(screen)
            if question.strip():
                self.say("...")   # "thinking" placeholder
                self.ai.ask(question, callback=self.say)
            return True
        return False

    # ------------------------------------------------------------------
    # Say — sets dialogue bubble text
    # ------------------------------------------------------------------
    def say(self, text: str):
        self.dialogue_text = text
        self.show_bubble   = True
        self.bubble_timer  = BUBBLE_DURATION

    # ------------------------------------------------------------------
    # Draw — call AFTER drawing the map/player so bubble is on top
    # ------------------------------------------------------------------
    def draw(self, screen: pygame.Surface):
        # Draw sprite
        screen.blit(self.image, self.rect)

        # Angel follows the main character and stays above them.
        angel_x = self.player.rect.centerx - (self.angel_portrait.get_width() // 2)
        angel_y = self.player.rect.y + ANGEL_FOLLOW_Y
        screen.blit(self.angel_portrait, (angel_x, angel_y))

        # Proximity hint
        if self.is_near_player and not self.show_bubble and not self.ai.is_thinking:
            hint = self.font.render("[T] Talk to Kha", True, HINT_TEXT)
            screen.blit(hint, (self.rect.x - 20, self.rect.y - 22))

        # Thinking indicator
        if self.ai.is_thinking:
            thinking = self.font.render("Kha is thinking...", True, THINKING_TEXT)
            screen.blit(thinking, (self.rect.x - 30, self.rect.y - 22))

        # Speech bubble
        if self.show_bubble and self.dialogue_text:
            self._draw_bubble(screen)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _draw_bubble(self, screen: pygame.Surface):
        lines      = _wrap_text(self.dialogue_text, self.font, BUBBLE_WIDTH - BUBBLE_PADDING * 2)
        bh         = len(lines) * BUBBLE_LINE_H + BUBBLE_PADDING * 2
        bx         = self.rect.x - 80
        by         = self.rect.y - bh - 14

        # Keep bubble inside screen horizontally
        bx = max(4, min(bx, screen.get_width() - BUBBLE_WIDTH - 4))

        # Box
        pygame.draw.rect(screen, BUBBLE_BG,
                         (bx, by, BUBBLE_WIDTH, bh), border_radius=8)
        pygame.draw.rect(screen, BUBBLE_BORDER,
                         (bx, by, BUBBLE_WIDTH, bh), 2, border_radius=8)

        # Tail triangle
        tail_x = self.rect.centerx
        pygame.draw.polygon(screen, BUBBLE_BG, [
            (tail_x - 6, by + bh),
            (tail_x + 6, by + bh),
            (tail_x,     by + bh + 10)
        ])
        pygame.draw.lines(screen, BUBBLE_BORDER, False, [
            (tail_x - 6, by + bh),
            (tail_x,     by + bh + 10),
            (tail_x + 6, by + bh)
        ], 2)

        # Text lines
        for i, line in enumerate(lines):
            surf = self.font.render(line, True, BUBBLE_TEXT)
            screen.blit(surf, (bx + BUBBLE_PADDING,
                               by + BUBBLE_PADDING + i * BUBBLE_LINE_H))

    def _get_text_input(self, screen: pygame.Surface):
        """Blocking inline text input box.

        Returns user text on submit, or None when cancelled with Esc.
        """
        clock      = pygame.time.Clock()
        input_text = ""
        panel_w    = min(860, screen.get_width() - 36)
        panel_h    = 130
        panel_x    = (screen.get_width() - panel_w) // 2
        panel_y    = screen.get_height() - panel_h - 18
        panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)

        avatar_size = 88
        avatar_rect = pygame.Rect(panel_x + 18, panel_y - (avatar_size // 2), avatar_size, avatar_size)

        # Keep the input area clear of the portrait so text never overlaps it.
        box_x = avatar_rect.right + 18
        box_w = panel_x + panel_w - box_x - 14
        box = pygame.Rect(box_x, panel_y + 62, box_w, 42)
        active     = True
        title_font = pygame.font.SysFont("freesansbold", 17)
        prompt_surf = self.font.render("Type your message and press Enter", True, CHAT_LABEL_TEXT)

        while active:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    raise SystemExit
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        # Enter submits only when there is meaningful text.
                        if input_text.strip():
                            active = False
                    elif event.key == pygame.K_ESCAPE:
                        return None
                    elif event.key == pygame.K_BACKSPACE:
                        input_text = input_text[:-1]
                    else:
                        if len(input_text) < 120:
                            input_text += event.unicode

            # Compact chat panel overlay (no full-screen blackout)
            panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
            panel.fill(CHAT_PANEL_BG)
            screen.blit(panel, (panel_x, panel_y))
            pygame.draw.rect(screen, CHAT_PANEL_BORDER, panel_rect, 2, border_radius=10)

            # Kha angel portrait at left corner, half-embedded into the chat panel.
            # Draw portrait directly (no surrounding box/frame).
            top_portrait = pygame.transform.smoothscale(self.angel_portrait, (avatar_size, avatar_size))
            screen.blit(top_portrait, avatar_rect)

            title = title_font.render("KHA ANGEL", True, CHAT_PANEL_BORDER)
            screen.blit(title, (avatar_rect.right + 12, panel_y + 12))
            screen.blit(prompt_surf, (box.x, panel_y + 34))

            # Input box
            pygame.draw.rect(screen, BUBBLE_BG, box, border_radius=6)
            pygame.draw.rect(screen, BUBBLE_BORDER, box, 2, border_radius=6)

            # If text is wider than the input box, render the right-most visible tail.
            display_text = input_text + "|"
            max_text_w = box.width - 16
            while self.font.size(display_text)[0] > max_text_w and len(display_text) > 1:
                display_text = display_text[1:]
            text_surf = self.font.render(display_text, True, BUBBLE_TEXT)
            screen.blit(text_surf, (box.x + 8, box.y + 11))

            pygame.display.flip()
            clock.tick(60)

        return input_text.strip()
