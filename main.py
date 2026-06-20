"""
Bible Quest - The Portal
========================
This is the main entry point for the game. It shows a "portal" hub — 
a grand hall with doors, each leading to a different Bible story game.

Currently implemented:
  Door 1 & 2 → The Lost Sheep Maze (Luke 15:3-7)

Architecture:
  main.py         - Portal hub (this file)
  sheep_maze.py   - The Lost Sheep maze game
  assets/         - Images, sounds (generated procedurally for now)
"""

import pygame
import sys
import math
import os

# ─── Bootstrap ──────────────────────────────────────────────────────────────
pygame.init()
pygame.font.init()

SCREEN_W, SCREEN_H = 900, 600
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("Bible Quest — The Portal")
clock = pygame.time.Clock()

# ─── Colour Palette (ancient parchment & stone) ──────────────────────────────
C_PARCHMENT  = (235, 215, 175)
C_DARK_STONE = ( 60,  45,  30)
C_STONE      = (120,  95,  70)
C_GOLD       = (200, 160,  50)
C_GOLD_LIT   = (255, 215,  80)
C_DOOR_WOOD  = (100,  60,  20)
C_DOOR_DARK  = ( 55,  30,  10)
C_SKY        = ( 30,  20,  10)       # dark background — inside a temple
C_TEXT_DARK  = ( 40,  25,  10)
C_WHITE      = (255, 255, 255)
C_HOVER      = (255, 230, 100)

# ─── Fonts ───────────────────────────────────────────────────────────────────
# We use system fonts that evoke antiquity
def load_font(size, bold=False):
    for name in ["Georgia", "Times New Roman", "serif", None]:
        try:
            return pygame.font.SysFont(name, size, bold=bold)
        except Exception:
            pass
    return pygame.font.Font(None, size)

font_title  = load_font(52, bold=True)
font_sub    = load_font(22)
font_door   = load_font(18, bold=True)
font_verse  = load_font(15)
font_hint   = load_font(14)

# ─── Door definitions ─────────────────────────────────────────────────────────
# Each door is a dict describing position, label, verse, and which module to load.
DOORS = [
    {
        "id": 1,
        "x": 170, "y": 230,
        "w": 140, "h": 210,
        "label": "The Lost\nSheep",
        "verse": "Luke 15:4",
        "desc": "Search the maze\nfor the lost sheep",
        "module": "sheep_maze",
        "color": (130, 75, 25),
    },
    {
        "id": 2,
        "x": 590, "y": 230,
        "w": 140, "h": 210,
        "label": "The Lost\nSheep",
        "verse": "Luke 15:4",
        "desc": "Search the maze\nfor the lost sheep",
        "module": "sheep_maze",
        "color": (100, 60, 20),
    },
]

# ─── Draw helpers ─────────────────────────────────────────────────────────────

def draw_arch(surface, x, y, w, h, color, border_color, hovered=False):
    """Draw a gothic-arch door shape."""
    body_rect = pygame.Rect(x, y + w // 2, w, h - w // 2)
    pygame.draw.rect(surface, color, body_rect, border_radius=4)

    # Arch top (semicircle)
    cx = x + w // 2
    cy = y + w // 2
    radius = w // 2
    pygame.draw.circle(surface, color, (cx, cy), radius)

    # Border
    border_col = C_GOLD_LIT if hovered else border_color
    pygame.draw.rect(surface, border_col, body_rect, width=3, border_radius=4)
    pygame.draw.circle(surface, border_col, (cx, cy), radius, width=3)

    # Door planks (decorative horizontal lines)
    plank_color = (color[0] - 20, color[1] - 10, max(0, color[2] - 5))
    for i in range(3):
        py = y + w // 2 + 20 + i * 55
        if py < y + h - 10:
            pygame.draw.line(surface, plank_color, (x + 8, py), (x + w - 8, py), 2)

    # Door knob
    knob_x = x + w - 22
    knob_y = y + w // 2 + (h - w // 2) // 2
    pygame.draw.circle(surface, C_GOLD if not hovered else C_GOLD_LIT, (knob_x, knob_y), 6)
    pygame.draw.circle(surface, C_DARK_STONE, (knob_x, knob_y), 6, width=1)


def draw_door_label(surface, door, hovered):
    """Render multi-line label and verse above/below door."""
    cx = door["x"] + door["w"] // 2
    col = C_GOLD_LIT if hovered else C_GOLD

    # Label lines (centred above the door)
    for i, line in enumerate(door["label"].split("\n")):
        surf = font_door.render(line, True, col)
        rect = surf.get_rect(center=(cx, door["y"] - 28 + i * 22))
        surface.blit(surf, rect)

    # Verse reference
    v_surf = font_verse.render(door["verse"], True, C_STONE)
    surface.blit(v_surf, v_surf.get_rect(center=(cx, door["y"] + door["h"] + 16)))

    # Description (shown on hover)
    if hovered:
        for i, line in enumerate(door["desc"].split("\n")):
            d_surf = font_hint.render(line, True, C_PARCHMENT)
            surface.blit(d_surf, d_surf.get_rect(center=(cx, door["y"] + door["h"] + 36 + i * 18)))


def draw_stars(surface, t):
    """Subtle twinkle in the dark temple ceiling."""
    star_positions = [
        (80, 40), (200, 70), (350, 30), (500, 55), (650, 35),
        (780, 60), (130, 90), (440, 85), (700, 80), (860, 45),
    ]
    for i, (sx, sy) in enumerate(star_positions):
        brightness = int(120 + 80 * math.sin(t * 2 + i * 1.1))
        pygame.draw.circle(surface, (brightness, brightness, brightness // 2), (sx, sy), 1)


def draw_floor(surface):
    """Tiled stone floor at the bottom."""
    floor_rect = pygame.Rect(0, SCREEN_H - 80, SCREEN_W, 80)
    pygame.draw.rect(surface, C_DARK_STONE, floor_rect)
    # Tile grid
    for col in range(0, SCREEN_W, 60):
        pygame.draw.line(surface, C_STONE, (col, SCREEN_H - 80), (col, SCREEN_H), 1)
    for row in range(SCREEN_H - 80, SCREEN_H, 40):
        pygame.draw.line(surface, C_STONE, (0, row), (SCREEN_W, row), 1)


def draw_pillars(surface):
    """Two stone pillars framing the scene."""
    for px in [30, SCREEN_W - 70]:
        pygame.draw.rect(surface, C_STONE, pygame.Rect(px, 100, 40, SCREEN_H - 180))
        # Capital (top decoration)
        pygame.draw.rect(surface, C_DARK_STONE, pygame.Rect(px - 5, 95, 50, 15), border_radius=3)
        # Base
        pygame.draw.rect(surface, C_DARK_STONE, pygame.Rect(px - 5, SCREEN_H - 185, 50, 15), border_radius=3)


def draw_portal_bg(surface, t):
    """Full background: dark temple interior."""
    surface.fill(C_SKY)
    draw_stars(surface, t)
    # Glow behind doors
    for door in DOORS:
        cx = door["x"] + door["w"] // 2
        cy = door["y"] + door["h"] // 2
        glow = pygame.Surface((300, 300), pygame.SRCALPHA)
        intensity = int(25 + 10 * math.sin(t * 1.5))
        pygame.draw.circle(glow, (200, 160, 50, intensity), (150, 150), 120)
        surface.blit(glow, (cx - 150, cy - 150), special_flags=pygame.BLEND_RGBA_ADD)
    draw_pillars(surface)
    draw_floor(surface)


def draw_title(surface, t):
    """Animated title banner."""
    glow_val = int(200 + 55 * math.sin(t * 1.2))
    title_color = (glow_val, int(glow_val * 0.78), 50)
    t_surf = font_title.render("Bible Quest", True, title_color)
    surface.blit(t_surf, t_surf.get_rect(center=(SCREEN_W // 2, 70)))

    sub_surf = font_sub.render("Choose a door to begin your journey", True, C_STONE)
    surface.blit(sub_surf, sub_surf.get_rect(center=(SCREEN_W // 2, 120)))


# ─── Main Portal Loop ─────────────────────────────────────────────────────────

def run_portal():
    t = 0.0
    running = True

    while running:
        dt = clock.tick(60) / 1000.0
        t += dt

        mx, my = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return "quit"
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for door in DOORS:
                    rect = pygame.Rect(door["x"], door["y"], door["w"], door["h"])
                    if rect.collidepoint(mx, my):
                        return door["module"]   # signal which game to launch

        # ── Draw ─────────────────────────────────────────────────────────────
        draw_portal_bg(screen, t)
        draw_title(screen, t)

        for door in DOORS:
            rect = pygame.Rect(door["x"], door["y"], door["w"], door["h"])
            hovered = rect.collidepoint(mx, my)
            draw_arch(screen, door["x"], door["y"], door["w"], door["h"],
                      door["color"], C_GOLD, hovered)
            draw_door_label(screen, door, hovered)

        # Hint at bottom
        hint = font_hint.render("Click a door · ESC to quit", True, C_STONE)
        screen.blit(hint, hint.get_rect(center=(SCREEN_W // 2, SCREEN_H - 20)))

        pygame.display.flip()

    return "quit"


# ─── Entry point ──────────────────────────────────────────────────────────────

def main():
    """
    Game loop orchestrator.
    The portal returns a string saying which game to launch.
    After a game ends, we return to the portal.
    """
    while True:
        result = run_portal()

        if result == "quit":
            break
        elif result == "sheep_maze":
            # Lazy-import so each game is self-contained
            import sheep_maze
            sheep_maze.run()   # runs until player exits or wins
        # Add more elif branches here as new games are added

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
