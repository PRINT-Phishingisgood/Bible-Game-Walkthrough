"""
The Lost Sheep — Maze Game
===========================
Based on Luke 15:3–7 — "What man of you, having a hundred sheep, if he has
lost one of them, does not leave the ninety-nine ... and go after the one
that is lost?"

HOW IT WORKS
────────────
1. Maze Generation
   We use a classic Recursive Backtracker (depth-first search) algorithm
   to carve a perfect maze through a grid of cells. Each cell is either
   a WALL or a PATH. Walls are drawn as dense bushes.

2. Fog of War
   A circular "vision radius" follows the player. Everything outside that
   radius is hidden by a dark overlay, giving the feeling of searching
   through an overgrown field at dusk.

3. Player (Shepherd)
   WASD or arrow keys. Collision detection prevents walking into walls.

4. Sheep
   Several sheep are hidden at random PATH cells. Walk over one to collect
   it. Collect all sheep to win.

5. Art Style
   Everything is drawn procedurally with pygame primitives — no external
   image files needed. Bushes = layered green circles; sheep = white ovals
   with legs; shepherd = brown robed figure.
"""

import pygame
import sys
import math
import random

# ─── Constants ───────────────────────────────────────────────────────────────
CELL       = 40          # pixel size of one maze cell
COLS       = 19          # maze width  in cells (must be odd for clean walls)
ROWS       = 15          # maze height in cells (must be odd)
SCREEN_W   = COLS * CELL
SCREEN_H   = ROWS * CELL + 80   # +80 for HUD strip at bottom

VISION_RADIUS = 130      # how far the player can see (pixels)
PLAYER_SPEED  = 3        # pixels per frame
NUM_SHEEP     = 5        # sheep to find

# ─── Colours ─────────────────────────────────────────────────────────────────
C_BG         = ( 20,  40,  10)   # very dark green (hidden grass)
C_PATH       = ( 80, 120,  50)   # lit path grass
C_WALL_BASE  = ( 30,  60,  20)   # dark bush base
C_BUSH_DARK  = ( 20,  70,  15)
C_BUSH_MID   = ( 35,  95,  25)
C_BUSH_LITE  = ( 55, 120,  35)
C_BUSH_HIGH  = ( 75, 140,  45)
C_SHEEP_BODY = (230, 230, 215)
C_SHEEP_LEG  = (100,  80,  60)
C_SHEEP_FACE = (160, 130, 100)
C_PLAYER     = (139,  90,  43)
C_PLAYER_ROBE= (180, 140,  80)
C_STAFF      = (110,  70,  30)
C_GOLD       = (220, 180,  50)
C_HUD_BG     = ( 25,  15,   5)
C_WHITE      = (255, 255, 255)
C_FOG        = (  0,   0,   0)

# ─── Maze Generation (Recursive Backtracker / DFS) ───────────────────────────
# The grid starts as ALL walls.
# We carve paths by visiting cells and knocking down walls between them.
# This guarantees exactly one path between any two cells (a "perfect maze").

WALL = 0
PATH = 1

def generate_maze(cols, rows):
    """
    Returns a 2-D list grid[row][col] where 0=wall, 1=path.
    cols and rows should be ODD so that wall-cells sit between path-cells.
    """
    grid = [[WALL] * cols for _ in range(rows)]

    def carve(r, c):
        grid[r][c] = PATH
        # Directions: up, down, left, right — each step is 2 cells
        directions = [(0, 2), (0, -2), (2, 0), (-2, 0)]
        random.shuffle(directions)
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == WALL:
                # Knock down the wall cell between current and neighbour
                grid[r + dr // 2][c + dc // 2] = PATH
                carve(nr, nc)

    # Start carving from (1,1) — always a PATH cell in an odd-dimension grid
    carve(1, 1)
    return grid


# ─── Procedural Sprite Drawers ────────────────────────────────────────────────

def draw_bush(surface, px, py, seed):
    """Draw a bush made of layered circles at pixel position (px,py)."""
    rng = random.Random(seed)
    cx, cy = px + CELL // 2, py + CELL // 2
    r = CELL // 2 - 2

    # Base blob
    pygame.draw.circle(surface, C_BUSH_DARK, (cx, cy), r)
    # Mid layer
    for _ in range(4):
        ox = rng.randint(-r // 2, r // 2)
        oy = rng.randint(-r // 2, r // 2)
        pygame.draw.circle(surface, C_BUSH_MID, (cx + ox, cy + oy), r - 4)
    # Highlight puffs
    for _ in range(3):
        ox = rng.randint(-r // 3, r // 3)
        oy = rng.randint(-r // 2, -2)
        pygame.draw.circle(surface, C_BUSH_LITE, (cx + ox, cy + oy), r - 8)
    # Top highlight
    pygame.draw.circle(surface, C_BUSH_HIGH,
                       (cx + rng.randint(-4, 4), cy - r // 3), r // 4)


def draw_sheep(surface, px, py, collected=False):
    """Draw a sheep centred at (px, py)."""
    if collected:
        return
    # Body
    pygame.draw.ellipse(surface, C_SHEEP_BODY,
                        pygame.Rect(px - 14, py - 9, 28, 18))
    # Wool bumps
    for bx, by in [(-8, -12), (0, -14), (8, -12)]:
        pygame.draw.circle(surface, C_SHEEP_BODY, (px + bx, py + by), 7)
    # Head
    pygame.draw.circle(surface, C_SHEEP_FACE, (px + 16, py - 4), 7)
    # Eye
    pygame.draw.circle(surface, (30, 20, 10), (px + 18, py - 6), 2)
    # Legs
    for lx in [-8, -2, 6, 12]:
        pygame.draw.line(surface, C_SHEEP_LEG,
                         (px + lx, py + 9), (px + lx, py + 17), 2)


def draw_player(surface, px, py):
    """Draw the shepherd at pixel position (px,py) — centre of sprite."""
    # Staff
    pygame.draw.line(surface, C_STAFF,
                     (px + 10, py - 20), (px + 10, py + 20), 3)
    pygame.draw.arc(surface, C_STAFF,
                    pygame.Rect(px + 4, py - 26, 14, 12),
                    math.pi * 0.8, math.pi * 2.2, 3)
    # Robe
    points = [(px, py - 14), (px - 9, py + 18), (px + 9, py + 18)]
    pygame.draw.polygon(surface, C_PLAYER_ROBE, points)
    # Belt line
    pygame.draw.line(surface, C_PLAYER,
                     (px - 7, py + 2), (px + 7, py + 2), 2)
    # Head
    pygame.draw.circle(surface, (200, 160, 110), (px, py - 18), 8)
    # Head cloth
    pygame.draw.arc(surface, C_PLAYER,
                    pygame.Rect(px - 9, py - 28, 18, 16),
                    0, math.pi, 3)


# ─── Pre-render Maze to a Surface ────────────────────────────────────────────
# We draw the maze once into a big Surface, then blit it each frame.
# This is much faster than redrawing every cell every frame.

def build_maze_surface(grid):
    surf = pygame.Surface((COLS * CELL, ROWS * CELL))
    for r in range(ROWS):
        for c in range(COLS):
            px, py = c * CELL, r * CELL
            if grid[r][c] == PATH:
                pygame.draw.rect(surf, C_PATH, pygame.Rect(px, py, CELL, CELL))
                # Subtle grass texture — tiny random dark dots
                rng = random.Random(r * 1000 + c)
                for _ in range(6):
                    gx = px + rng.randint(2, CELL - 2)
                    gy = py + rng.randint(2, CELL - 2)
                    pygame.draw.circle(surf, (60, 100, 35), (gx, gy), 1)
            else:
                pygame.draw.rect(surf, C_WALL_BASE, pygame.Rect(px, py, CELL, CELL))
                draw_bush(surf, px, py, seed=r * 1000 + c)
    return surf


# ─── Fog of War ───────────────────────────────────────────────────────────────
# We create a full-screen dark surface and punch a soft-edged hole where the
# player is standing. Everything outside that circle is hidden.

def build_fog_surface(width, height, cx, cy, radius):
    """
    Returns a Surface with a transparent circle at (cx,cy).
    We draw concentric circles going from fully transparent at the centre
    to fully opaque black at the edge, creating a soft vignette.
    """
    fog = pygame.Surface((width, height), pygame.SRCALPHA)
    fog.fill((0, 0, 0, 255))  # start fully black

    # Punch gradient hole: draw circles of decreasing alpha from edge inward
    steps = 30
    for i in range(steps):
        frac = i / steps          # 0 = centre, 1 = edge
        r = int(radius * (1 - frac))
        alpha = int(255 * frac * frac)   # quadratic fade: bright centre, dark edge
        pygame.draw.circle(fog, (0, 0, 0, alpha), (cx, cy), r)

    return fog


# ─── HUD (Heads-Up Display) ───────────────────────────────────────────────────

def draw_hud(surface, found, total, verse_surf, font_hud, font_small):
    hud_rect = pygame.Rect(0, ROWS * CELL, SCREEN_W, 80)
    pygame.draw.rect(surface, C_HUD_BG, hud_rect)
    pygame.draw.line(surface, C_GOLD, (0, ROWS * CELL), (SCREEN_W, ROWS * CELL), 2)

    # Sheep counter
    label = font_hud.render(f"Sheep found: {found} / {total}", True, C_GOLD)
    surface.blit(label, (20, ROWS * CELL + 12))

    # Sheep icons in HUD
    for i in range(total):
        ix = 280 + i * 36
        iy = ROWS * CELL + 40
        if i < found:
            # Collected — golden glow
            pygame.draw.circle(surface, C_GOLD, (ix, iy), 12)
            pygame.draw.circle(surface, C_SHEEP_BODY, (ix, iy), 10)
        else:
            # Not yet found — grey silhouette
            pygame.draw.circle(surface, (80, 80, 80), (ix, iy), 12)
            pygame.draw.circle(surface, (50, 50, 50), (ix, iy), 10)

    # Verse reminder
    surface.blit(verse_surf, (SCREEN_W - verse_surf.get_width() - 15, ROWS * CELL + 52))

    # Controls hint
    ctrl = font_small.render("WASD / Arrow keys to move", True, (100, 90, 70))
    surface.blit(ctrl, (20, ROWS * CELL + 52))


# ─── Win Screen ───────────────────────────────────────────────────────────────

def draw_win_screen(surface, font_big, font_med, font_small, t):
    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    surface.blit(overlay, (0, 0))

    glow = int(200 + 55 * math.sin(t * 2))
    gold = (glow, int(glow * 0.8), 40)

    lines = [
        (font_big,   "All Sheep Found!",              gold),
        (font_med,   '"Rejoice with me, for I have',  C_WHITE),
        (font_med,   ' found my sheep that was lost."', C_WHITE),
        (font_small, "— Luke 15:6",                   (180, 160, 100)),
        (font_small, "Press ESC to return to the Portal", (150, 150, 150)),
    ]
    y = SCREEN_H // 2 - 100
    for fnt, text, color in lines:
        surf = fnt.render(text, True, color)
        surface.blit(surf, surf.get_rect(center=(SCREEN_W // 2, y)))
        y += fnt.get_height() + 8


# ─── Main Game Function ───────────────────────────────────────────────────────

def run():
    """
    Called from main.py when the player enters the Lost Sheep door.
    Runs the game loop and returns when the player exits.
    """
    pygame.display.set_caption("Bible Quest — The Lost Sheep")
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    clock  = pygame.time.Clock()

    # ── Fonts
    def sf(size, bold=False):
        for n in ["Georgia", "Times New Roman", None]:
            try:
                return pygame.font.SysFont(n, size, bold=bold)
            except Exception:
                pass
        return pygame.font.Font(None, size)

    font_big   = sf(48, bold=True)
    font_med   = sf(22)
    font_hud   = sf(20, bold=True)
    font_small = sf(15)

    verse_surf = font_small.render(
        '"Go after the lost sheep until he finds it." — Luke 15:4', True, (160, 130, 80))

    # ── Generate maze
    random.seed()            # fresh maze each play
    grid = generate_maze(COLS, ROWS)

    # ── Build static maze image (only done once)
    maze_surf = build_maze_surface(grid)

    # ── Collect all walkable PATH cells (for placing player and sheep)
    path_cells = [(c, r) for r in range(ROWS) for c in range(COLS)
                  if grid[r][c] == PATH]
    random.shuffle(path_cells)

    # ── Player starts at first path cell (top-left area)
    start_cell = path_cells[0]
    # Pixel position = centre of cell
    player_x = float(start_cell[0] * CELL + CELL // 2)
    player_y = float(start_cell[1] * CELL + CELL // 2)

    # ── Place sheep at random path cells far from start
    sheep_cells = path_cells[max(1, len(path_cells) // 4):]
    random.shuffle(sheep_cells)
    sheep_list = []
    for i in range(min(NUM_SHEEP, len(sheep_cells))):
        sc = sheep_cells[i]
        sheep_list.append({
            "x": sc[0] * CELL + CELL // 2,
            "y": sc[1] * CELL + CELL // 2,
            "found": False,
        })

    found_count = 0
    game_won    = False
    t           = 0.0

    # ── Game loop
    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        t += dt

        # ── Events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False   # return to portal

        # ── Movement (only when not won)
        if not game_won:
            keys = pygame.key.get_pressed()
            dx = dy = 0
            if keys[pygame.K_LEFT]  or keys[pygame.K_a]: dx -= PLAYER_SPEED
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx += PLAYER_SPEED
            if keys[pygame.K_UP]    or keys[pygame.K_w]: dy -= PLAYER_SPEED
            if keys[pygame.K_DOWN]  or keys[pygame.K_s]: dy += PLAYER_SPEED

            # ── Collision detection
            # Try to move in X and Y separately so the player can slide along walls.
            def can_stand(x, y):
                """Check that the 4 corners of an 18x18 box around (x,y) are all PATH."""
                half = 9
                corners = [
                    (x - half, y - half), (x + half, y - half),
                    (x - half, y + half), (x + half, y + half),
                ]
                for cx_, cy_ in corners:
                    col_ = int(cx_) // CELL
                    row_ = int(cy_) // CELL
                    if not (0 <= col_ < COLS and 0 <= row_ < ROWS):
                        return False
                    if grid[row_][col_] == WALL:
                        return False
                return True

            new_x = player_x + dx
            new_y = player_y + dy
            if can_stand(new_x, player_y): player_x = new_x
            if can_stand(player_x, new_y): player_y = new_y

            # ── Sheep pickup
            for sheep in sheep_list:
                if not sheep["found"]:
                    dist = math.hypot(sheep["x"] - player_x, sheep["y"] - player_y)
                    if dist < CELL * 0.75:
                        sheep["found"] = True
                        found_count += 1
                        if found_count >= NUM_SHEEP:
                            game_won = True

        # ── Draw ─────────────────────────────────────────────────────────────
        screen.fill(C_BG)

        # 1) Blit static maze
        screen.blit(maze_surf, (0, 0))

        # 2) Draw sheep (only visible when fog allows — the fog handles that visually)
        for sheep in sheep_list:
            if not sheep["found"]:
                draw_sheep(screen, sheep["x"], sheep["y"])

        # 3) Draw player
        draw_player(screen, int(player_x), int(player_y))

        # 4) Fog of war — drawn on top of everything
        fog = build_fog_surface(
            SCREEN_W, ROWS * CELL,
            int(player_x), int(player_y),
            VISION_RADIUS
        )
        screen.blit(fog, (0, 0))

        # 5) HUD (below the maze, unaffected by fog)
        draw_hud(screen, found_count, NUM_SHEEP, verse_surf, font_hud, font_small)

        # 6) Win overlay
        if game_won:
            draw_win_screen(screen, font_big, font_med, font_small, t)

        pygame.display.flip()

    # Restore portal window size when leaving
    pygame.display.set_mode((900, 600))
    pygame.display.set_caption("Bible Quest — The Portal")
