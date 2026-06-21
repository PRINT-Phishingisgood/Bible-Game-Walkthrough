"""
Bible Quest — Arcade World
===========================
A top-down walkable arcade hall with an active Redis Cloud Leaderboard.
Approach a door cabinet and press ENTER to play that Bible story mini-game.
"""

import pygame
import sys
import math
import random
import character_select
import redis  # Restored to standard desktop library

# ──────────────────────────────────────────────────────────────────────────────
# INIT
# ──────────────────────────────────────────────────────────────────────────────
pygame.init()
pygame.font.init()

SCREEN_W = 1100
SCREEN_H = 700
screen   = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("Bible Quest — Arcade World")
clock    = pygame.time.Clock()

global_volume = 70
global_fish_coins = 0  # Globally tracked inventory counter synced via cloud save profile

# ──────────────────────────────────────────────────────────────────────────────
# REDIS CLOUD CONFIGURATION & SETUP (RESTORED)
# ──────────────────────────────────────────────────────────────────────────────
REDIS_HOST = 'expansive-wood-substance-85250.db.redis.io'
REDIS_PORT = 12993
REDIS_PASSWORD = '3Yh0iQlU0oVAiLfyXNrwTHSWhGF6KRty'

try:
    r = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        password=REDIS_PASSWORD,
        decode_responses=True,
        socket_timeout=4
    )
    if r.ping():
        print(" Successfully connected to Redis Cloud! Leaderboards are live.")
except Exception as e:
    print(f"⚠️ Redis initialization skipped/failed: {e}")
    r = None

def save_high_score(game_id, player_name, score):
    """Saves or updates a high score using a Sorted Set (ZSET)."""
    if r:
        try:
            r.zadd(f"leaderboard:{game_id}", {player_name: score})
            print(f" Saved score of {score} for {player_name} to cloud!")
        except Exception as e:
            print(f" Could not post score to Redis: {e}")

def get_top_scores(game_id, limit=5):
    """Retrieves top ranks sorted in descending order from Redis Cloud."""
    if r:
        try:
            return r.zrevrange(f"leaderboard:{game_id}", 0, limit - 1, withscores=True)
        except Exception as e:
            print(f" Could not read cloud scores: {e}")
    return []

# ──────────────────────────────────────────────────────────────────────────────
# NEW CLOUD PROFILE & BALANCING ENGINE CORES (RESTORING MISSING CONFIG CORES)
# ──────────────────────────────────────────────────────────────────────────────
def load_player_profile(player_name):
    """Fetches user currency balance and stats persistently from the cloud."""
    global global_fish_coins
    if r:
        try:
            profile_key = f"player:{player_name}"
            if r.exists(profile_key):
                data = r.hgetall(profile_key)
                global_fish_coins = int(data.get("fish_coins", 0))
                print(f" Loaded {player_name}'s cloud profile. Wallet Balance: {global_fish_coins} Fish Coins.")
            else:
                # Initialize fields
                r.hset(profile_key, mapping={"fish_coins": 0, "chosen_skin": player_name})
                global_fish_coins = 0
                print(f" Created brand new cloud profile for {player_name}.")
        except Exception as e:
            print(f" ⚠️ Profile fetch skipped: {e}")

def save_player_profile(player_name):
    """Saves current wallet variables cleanly into an online hash mapping container."""
    if r:
        try:
            profile_key = f"player:{player_name}"
            r.hset(profile_key, mapping={"fish_coins": global_fish_coins})
            print(f" Safely backed up {player_name}'s balance ({global_fish_coins} coins) to Redis Cloud.")
        except Exception as e:
            print(f" Could not update cloud backup hash: {e}")

def get_live_game_config():
    """Queries configuration hash for active balancing metrics from cloud."""
    defaults = {"goliath_speed": 12.0, "gravity": 1350.0, "player_speed": 5.0}
    if r:
        try:
            config_key = "game:config"
            if r.exists(config_key):
                cloud_data = r.hgetall(config_key)
                return {k: float(cloud_data.get(k, v)) for k, v in defaults.items()}
            else:
                r.hset(config_key, mapping={k: str(v) for k, v in defaults.items()})
        except Exception as e:
            print(f" Custom config query failed, pulling default constants: {e}")
    return defaults

# ──────────────────────────────────────────────────────────────────────────────
# WORLD DIMENSIONS
# ──────────────────────────────────────────────────────────────────────────────
WORLD_W = 2200
WORLD_H = 1100

TILE      = 48
PLAYER_R  = 14
SPEED     = 3

# Transformed floor colors into warm sand shades
C_FLOOR_A    = (235, 205, 145)
C_FLOOR_B    = (225, 195, 135)
C_FLOOR_GRID = (210, 180, 120)
C_WALL       = ( 38,  28,  18)
C_WALL_FACE  = ( 55,  42,  28)
C_TORCH_ORG  = (255, 140,  30)
C_TORCH_YEL  = (255, 220,  80)
C_GOLD       = (210, 170,  50)
C_GOLD_LIT   = (255, 215,  80)
C_PARCHMENT  = (230, 205, 155)
C_TEXT_LIGHT = (240, 220, 170)
C_TEXT_DIM   = (160, 130,  80)
C_DARK       = (  8,   5,   2)
C_WHITE      = (255, 255, 255)

CAB_COLORS = [
    {"wood": ( 90,  50,  15), "glow": ( 80, 200, 120), "trim": (120,  80,  30)},
    {"wood": ( 60,  30,  80), "glow": (150, 100, 255), "trim": ( 90,  55, 120)},
    {"wood": ( 80,  20,  20), "glow": (255,  80,  60), "trim": (120,  45,  40)},
    {"wood": ( 20,  50,  70), "glow": ( 60, 180, 255), "trim": ( 35,  80, 110)},
]

def mf(size, bold=False):
    for n in ["Segoe UI Symbol", "Arial", "Georgia", "Times New Roman", None]:
        try:  return pygame.font.SysFont(n, size, bold=bold)
        except Exception: pass
    return pygame.font.Font(None, size)

def mf2(size, bold=False):
    for n in ["Courier New", "Courier", "monospace", None]:
        try:  return pygame.font.SysFont(n, size, bold=bold)
        except Exception: pass
    return pygame.font.Font(None, size)

fnt_title  = mf(44, bold=True)
fnt_big    = mf(28, bold=True)
fnt_med    = mf(20)
fnt_sm     = mf(15)
fnt_xs     = mf(13)
fnt_mono   = mf2(13)
fnt_cabinet= mf(14, bold=True)
fnt_emoji  = mf(26)

CABINETS = [
    {
        "id":      "sheep_maze",
        "name":    "The Lost Sheep",
        "wx": 380, "wy": 200,
        "cw": 130, "ch": 180,
        "col": CAB_COLORS[0],
        "unlocked": True,
        "screen_lines": ["LOST", "SHEEP"],
        "emoji": "🐑",
        "scroll_text": "FIND THE FLOCK · SEARCH IN DARKNESS · LUKE 15:4 ·· ",
    },
    {
        "id":      "feed_crowd",
        "name":    "Feed the Crowd",
        "wx": 700, "wy": 200,
        "cw": 130, "ch": 180,
        "col": CAB_COLORS[2],
        "unlocked": True,
        "screen_lines": ["MULTIPLY", "LOAVES"],
        "emoji": "🍞",
        "scroll_text": "FEEDING THE 5000 · MATTHEW 14:20 ·· ",
    },
    {
        "id":      "fish_coin",
        "name":    "Noah's Ark",
        "wx": 1020, "wy": 200,
        "cw": 130, "ch": 180,
        "col": CAB_COLORS[3],
        "unlocked": True,
        "screen_lines": ["DEEP SEA", "HOOK"],
        "emoji": "🐋",
        "scroll_text": "PIECE OF MONEY · CAST AN HOOK · MATTHEW 17:27 ·· ",
    },
    {
        "id":      "david_sling",
        "name":    "David & Goliath",
        "wx": 1340, "wy": 200,
        "cw": 130, "ch": 180,
        "col": CAB_COLORS[1],
        "unlocked": True,
        "screen_lines": ["DAVID &", "GOLIATH"],
        "emoji": "🪨",
        "scroll_text": "SLING AND A STONE · 1 SAMUEL 17 ·· ",
    },
    {
        "id":      "coming_soon4",
        "name":    "Jonah & the Whale",
        "wx": 380, "wy": 680,
        "cw": 130, "ch": 180,
        "col": CAB_COLORS[3],
        "unlocked": False,
        "screen_lines": ["JONAH", "& WHALE"],
        "emoji": "🐋",
        "scroll_text": "COMING SOON · JONAH 1 ·· ",
    },
    {
        "id":      "coming_soon5",
        "name":    "Moses & Red Sea",
        "wx": 700, "wy": 680,
        "cw": 130, "ch": 180,
        "col": CAB_COLORS[0],
        "unlocked": False,
        "screen_lines": ["MOSES", "RED SEA"],
        "emoji": "🌊",
        "scroll_text": "COMING SOON · EXODUS 14 ·· ",
    },
    {
        "id":      "babel_tower",
        "name":    "Tower of Babel",
        "wx": 1020, "wy": 680,
        "cw": 130, "ch": 180,
        "col": CAB_COLORS[2],
        "unlocked": True,
        "screen_lines": ["TOWER OF", "BABEL"],
        "emoji": "🧱",
        "scroll_text": "CARRY BRICKS · BEWARE CONFUSION · GENESIS 11 ·· ",
    },
    {
        "id":      "coming_soon7",
        "name":    "Creation Week",
        "wx": 1340, "wy": 680,
        "cw": 130, "ch": 180,
        "col": CAB_COLORS[1],
        "unlocked": False,
        "screen_lines": ["CREATION", "WEEK"],
        "emoji": "🌱",
        "scroll_text": "COMING SOON · GENESIS 1 ·· ",
    },
]

WALL_THICKNESS = 40

def make_walls():
    walls = []
    walls.append(pygame.Rect(0, 0, WORLD_W, WALL_THICKNESS))
    walls.append(pygame.Rect(0, WORLD_H - WALL_THICKNESS, WORLD_W, WALL_THICKNESS))
    walls.append(pygame.Rect(0, 0, WALL_THICKNESS, WORLD_H))
    walls.append(pygame.Rect(WORLD_W - WALL_THICKNESS, 0, WALL_THICKNESS, WORLD_H))

    pillar_xs = [180, 560, 870, 1190, 1500, 1830]
    for px in pillar_xs:
        for py in [160, 440, 740, 960]:
            walls.append(pygame.Rect(px, py, 36, 80))
    return walls

WALLS = make_walls()

def cabinet_rects():
    return [pygame.Rect(c["wx"], c["wy"], c["cw"], c["ch"]) for c in CABINETS]

TORCH_POSITIONS = []
for tx in range(200, WORLD_W - 100, 280):
    TORCH_POSITIONS.append((tx, 80))
    TORCH_POSITIONS.append((tx, WORLD_H - 80))
for ty in range(200, WORLD_H - 100, 240):
    TORCH_POSITIONS.append((80, ty))
    TORCH_POSITIONS.append((WORLD_W - 80, ty))

def build_floor_surface():
    surf = pygame.Surface((WORLD_W, WORLD_H))
    surf.fill(C_WALL)

    for row in range(WALL_THICKNESS // TILE, (WORLD_H - WALL_THICKNESS) // TILE + 1):
        for col in range(WALL_THICKNESS // TILE, (WORLD_W - WALL_THICKNESS) // TILE + 1):
            x = col * TILE
            y = row * TILE
            base = C_FLOOR_A if (row + col) % 2 == 0 else C_FLOOR_B
            r = random.Random(row * 9999 + col)
            v = r.randint(-6, 6)
            col_t = tuple(max(0, min(255, c + v)) for c in base)
            pygame.draw.rect(surf, col_t, pygame.Rect(x, y, TILE, TILE))
            pygame.draw.rect(surf, C_FLOOR_GRID, pygame.Rect(x, y, TILE, TILE), 1)

    pygame.draw.rect(surf, C_WALL_FACE, pygame.Rect(0, 0, WORLD_W, WALL_THICKNESS))
    pygame.draw.rect(surf, C_WALL_FACE, pygame.Rect(0, WORLD_H-WALL_THICKNESS, WORLD_W, WALL_THICKNESS))
    pygame.draw.rect(surf, C_WALL_FACE, pygame.Rect(0, 0, WALL_THICKNESS, WORLD_H))
    pygame.draw.rect(surf, C_WALL_FACE, pygame.Rect(WORLD_W-WALL_THICKNESS, 0, WALL_THICKNESS, WORLD_H))

    for bx in range(0, WORLD_W, 120):
        for by in [10, 25]:
            pygame.draw.rect(surf, C_FLOOR_GRID, pygame.Rect(bx, by, 118, 12), 1)
        for by in [WORLD_H - 38, WORLD_H - 23]:
            pygame.draw.rect(surf, C_FLOOR_GRID, pygame.Rect(bx, by, 118, 12), 1)

    for rect in WALLS[4:]:
        pygame.draw.rect(surf, (80, 62, 42), rect)
        pygame.draw.rect(surf, (100, 78, 50), rect, 2)
        cap = pygame.Rect(rect.x - 5, rect.y - 6, rect.w + 10, 10)
        base_ = pygame.Rect(rect.x - 5, rect.bottom - 4, rect.w + 10, 10)
        pygame.draw.rect(surf, (105, 82, 54), cap, border_radius=2)
        pygame.draw.rect(surf, (105, 82, 54), base_, border_radius=2)

    banner = fnt_big.render("✦  BIBLE  QUEST  ARCADE  ✦", True, C_GOLD)
    surf.blit(banner, banner.get_rect(center=(WORLD_W // 2, 22)))
    return surf

def draw_cabinet(surf, cab, t, cam_x, cam_y, near):
    sx = cab["wx"] - cam_x
    sy = cab["wy"] - cam_y
    w  = cab["cw"]
    h  = cab["ch"]
    col = cab["col"]

    pygame.draw.rect(surf, col["wood"], pygame.Rect(sx, sy, w, h), border_radius=6)
    pygame.draw.rect(surf, col["trim"], pygame.Rect(sx, sy, w, h), 3, border_radius=6)

    screen_rect = pygame.Rect(sx + 10, sy + 12, w - 20, h // 2 - 10)
    pygame.draw.rect(surf, C_DARK, screen_rect, border_radius=4)

    glow_alpha = int(160 + 70 * math.sin(t * 2.5 + cab["wx"] * 0.01))
    if cab["unlocked"]:
        glow_surf = pygame.Surface((screen_rect.w, screen_rect.h), pygame.SRCALPHA)
        glow_surf.fill((*col["glow"], glow_alpha // 4))
        surf.blit(glow_surf, screen_rect.topleft)

    glow_col = col["glow"] if cab["unlocked"] else (80, 80, 80)

    em_surf = fnt_emoji.render(cab.get("emoji", "🎮"), True, C_WHITE)
    surf.blit(em_surf, em_surf.get_rect(center=(screen_rect.centerx, screen_rect.y + 22)))

    line_y = screen_rect.y + 44
    for line in cab["screen_lines"]:
        ls = fnt_cabinet.render(line, True, glow_col)
        surf.blit(ls, ls.get_rect(center=(screen_rect.centerx, line_y)))
        line_y += fnt_cabinet.get_height() + 2

    scroll_rect = pygame.Rect(sx + 10, sy + h // 2 + 5, w - 20, 16)
    pygame.draw.rect(surf, C_DARK, scroll_rect)
    scroll_text = cab["scroll_text"]
    char_w = 7
    offset = int((t * 40) % (len(scroll_text) * char_w))
    doubled = scroll_text * 3
    tick_surf = fnt_mono.render(doubled, True, glow_col)
    surf.blit(tick_surf, (scroll_rect.x - offset, scroll_rect.y + 1), area=pygame.Rect(0, 0, scroll_rect.w, scroll_rect.h))
    pygame.draw.rect(surf, C_DARK, scroll_rect, 1)

    panel_rect = pygame.Rect(sx + 8, sy + h // 2 + 25, w - 16, h // 2 - 35)
    pygame.draw.rect(surf, col["trim"], panel_rect, border_radius=3)

    js_x = sx + w // 2 - 20
    js_y = sy + h // 2 + 48
    pygame.draw.circle(surf, (30, 30, 30), (js_x, js_y), 10)
    pygame.draw.circle(surf, (50, 50, 50), (js_x, js_y), 10, 2)
    pygame.draw.circle(surf, (20, 20, 20), (js_x, js_y - 12), 7)

    if near:
        if cab["unlocked"]:
            pulse = int(50 + 25 * math.sin(t * 5))
            ps = fnt_sm.render("[ ENTER ] Play", True, (pulse, int(pulse * 0.7), 15))
            surf.blit(ps, ps.get_rect(center=(sx + w // 2, sy - 22)))
        else:
            ls = fnt_sm.render("Coming Soon", True, (130, 100, 60))
            surf.blit(ls, ls.get_rect(center=(sx + w // 2, sy - 22)))

def draw_torch(surf, wx, wy, cam_x, cam_y, t, idx):
    sx = wx - cam_x
    sy = wy - cam_y
    if not (-60 < sx < SCREEN_W + 60 and -60 < sy < SCREEN_H + 60):
        return
    phase = t * 8 + idx * 1.37
    flicker = math.sin(phase) * 3 + math.sin(phase * 2.3) * 2
    pygame.draw.rect(surf, (80, 60, 35), pygame.Rect(sx - 3, sy, 6, 14))
    for r, col in [(10, C_TORCH_ORG), (6, C_TORCH_YEL)]:
        fr = int(r + flicker * 0.4)
        pygame.draw.ellipse(surf, col, pygame.Rect(sx - fr, sy - fr * 2, fr * 2, fr * 2))

def draw_player(surf, sx, sy, facing, t, moving, skin):
    pygame.draw.ellipse(surf, (15, 10, 5), pygame.Rect(sx - 12, sy + 14, 24, 8))
    bob = int(2 * math.sin(t * 10)) if moving else 0

    pygame.draw.polygon(surf, skin["color"], [(sx, sy - 20 + bob), (sx - 11, sy + 18 + bob), (sx + 11, sy + 18 + bob)])
    pygame.draw.polygon(surf, skin["inner"], [(sx, sy - 14 + bob), (sx - 5, sy + 14 + bob), (sx + 5, sy + 14 + bob)])
    pygame.draw.line(surf, (100, 70, 30), (sx - 9, sy + 4 + bob), (sx + 9, sy + 4 + bob), 2)

    head_y = sy - 30 + bob
    pygame.draw.circle(surf, (210, 170, 115), (sx, head_y), 10)
    pygame.draw.arc(surf, skin["cloth"], pygame.Rect(sx - 11, head_y - 11, 22, 14), 0, math.pi, 3)
    pygame.draw.line(surf, skin["cloth"], (sx - 11, head_y - 4), (sx - 14, head_y + 5), 2)

    eye_offsets = {"right": [(3, -1), (8, -1)], "left": [(-8, -1), (-3, -1)],
                   "down":  [(-3, 2),  (3, 2)],  "up":   [(-3, -4), (3, -4)]}
    for ex, ey in eye_offsets.get(facing, [(- 3, 2), (3, 2)]):
        pygame.draw.circle(surf, (40, 25, 10), (sx + ex, head_y + ey), 2)

    if skin.get("has_staff", False):
        staff_x = sx + (12 if facing in ("right", "down") else -12)
        pygame.draw.line(surf, (100, 65, 25), (staff_x, sy + 18 + bob), (staff_x, sy - 28 + bob), 3)
        pygame.draw.arc(surf, (100, 65, 25), pygame.Rect(staff_x - 7, sy - 36 + bob, 14, 10), math.pi * 0.6, math.pi * 2, 3)

def draw_hud(surf, near_cab, t):
    hud_h = 38
    hud_bg = pygame.Surface((SCREEN_W, hud_h), pygame.SRCALPHA)
    hud_bg.fill((8, 5, 2, 200))
    surf.blit(hud_bg, (0, 0))
    pygame.draw.line(surf, C_GOLD, (0, hud_h), (SCREEN_W, hud_h), 1)

    title = fnt_med.render("✦  BIBLE QUEST ARCADE  ✦", True, C_GOLD)
    surf.blit(title, title.get_rect(center=(SCREEN_W // 2, hud_h // 2)))

    move_hint = fnt_xs.render("WASD / ↑↓←→  Move", True, C_TEXT_DIM)
    surf.blit(move_hint, (14, 10))

    # Display dynamically updated global wallet status items
    coins_txt = fnt_xs.render(f"Wallet: {global_fish_coins} Fish Coins", True, C_GOLD_LIT)
    surf.blit(coins_txt, (14, 22))

    door_rect = pygame.Rect(SCREEN_W - 55, 4, 28, 30)
    pygame.draw.rect(surf, (110, 75, 45), door_rect, border_top_left_radius=14, border_top_right_radius=14)
    pygame.draw.rect(surf, C_GOLD, door_rect, 2, border_top_left_radius=14, border_top_right_radius=14)
    pygame.draw.circle(surf, C_GOLD, (SCREEN_W - 34, 18), 3)

def run_settings_menu():
    global global_volume
    menu_running = True
    selected_option = 0

    while menu_running:
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((15, 10, 5, 225))
        screen.blit(overlay, (0, 0))

        frame = pygame.Rect(SCREEN_W // 2 - 250, SCREEN_H // 2 - 200, 500, 400)
        pygame.draw.rect(screen, (45, 32, 20), frame, border_radius=12)
        pygame.draw.rect(screen, C_GOLD, frame, 3, border_radius=12)

        m_title = fnt_big.render("SYSTEM OPTIONS", True, C_GOLD)
        screen.blit(m_title, m_title.get_rect(center=(SCREEN_W // 2, frame.y + 45)))
        pygame.draw.line(screen, C_FLOOR_GRID, (frame.x + 40, frame.y + 80), (frame.right - 40, frame.y + 80), 2)

        vol_label = fnt_med.render("Volume Level:", True, C_PARCHMENT)
        screen.blit(vol_label, (frame.x + 50, frame.y + 120))

        slider_rect = pygame.Rect(frame.x + 200, frame.y + 128, 220, 10)
        pygame.draw.rect(screen, C_DARK, slider_rect, border_radius=4)
        fill_w = int(220 * (global_volume / 100.0))
        pygame.draw.rect(screen, C_GOLD_LIT, pygame.Rect(slider_rect.x, slider_rect.y, fill_w, 10), border_radius=4)
        pygame.draw.circle(screen, C_WHITE, (slider_rect.x + fill_w, slider_rect.y + 5), 8)

        vol_pct = fnt_sm.render(f"{global_volume}%", True, C_TEXT_LIGHT)
        screen.blit(vol_pct, (slider_rect.right + 15, frame.y + 124))

        opt1_color = C_WHITE if selected_option == 1 else C_TEXT_DIM
        opt2_color = (255, 100, 100) if selected_option == 2 else (180, 70, 70)

        text_btn1 = fnt_big.render("[ Resume World ]", True, opt1_color)
        text_btn2 = fnt_big.render("[ Exit Game ]", True, opt2_color)

        rect_btn1 = text_btn1.get_rect(center=(SCREEN_W // 2, frame.y + 220))
        rect_btn2 = text_btn2.get_rect(center=(SCREEN_W // 2, frame.y + 290))

        if selected_option == 0:
            pygame.draw.rect(screen, (80, 60, 40), pygame.Rect(frame.x + 40, frame.y + 112, frame.w - 80, 35), 2, border_radius=6)
        elif selected_option == 1:
            pygame.draw.rect(screen, C_GOLD, rect_btn1.inflate(20, 10), 1, border_radius=6)
        elif selected_option == 2:
            pygame.draw.rect(screen, (255, 50, 50), rect_btn2.inflate(20, 10), 1, border_radius=6)

        screen.blit(text_btn1, rect_btn1)
        screen.blit(text_btn2, rect_btn2)

        hint = fnt_xs.render("Use UP/DOWN Arrows to Select • LEFT/RIGHT to Adjust Volume • ENTER to Select", True, C_TEXT_DIM)
        screen.blit(hint, hint.get_rect(center=(SCREEN_W // 2, frame.bottom - 25)))

        pygame.display.flip()
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    menu_running = False
                elif event.key == pygame.K_UP or event.key == pygame.K_w:
                    selected_option = (selected_option - 1) % 3
                elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                    selected_option = (selected_option + 1) % 3
                elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
                    if selected_option == 0: global_volume = max(0, global_volume - 5)
                elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                    if selected_option == 0: global_volume = min(100, global_volume + 5)
                elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                    if selected_option == 1: menu_running = False
                    elif selected_option == 2:
                        if run_confirmation_modal():
                            pygame.quit()
                            sys.exit()

def run_confirmation_modal():
    confirm_loop = True
    confirm_select = 1

    while confirm_loop:
        popup = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        popup.fill((0, 0, 0, 180))
        screen.blit(popup, (0, 0))

        box = pygame.Rect(SCREEN_W // 2 - 200, SCREEN_H // 2 - 90, 400, 180)
        pygame.draw.rect(screen, (30, 20, 15), box, border_radius=8)
        pygame.draw.rect(screen, (220, 70, 70), box, 2, border_radius=8)

        lbl = fnt_med.render("Are you sure you want to quit?", True, C_WHITE)
        screen.blit(lbl, lbl.get_rect(center=(SCREEN_W // 2, box.y + 45)))

        c0 = C_WHITE if confirm_select == 0 else C_TEXT_DIM
        c1 = C_WHITE if confirm_select == 1 else C_TEXT_DIM

        b0_text = fnt_big.render("YES", True, c0)
        b1_text = fnt_big.render("NO", True, c1)

        b0_rect = b0_text.get_rect(center=(SCREEN_W // 2 - 80, box.y + 115))
        b1_rect = b1_text.get_rect(center=(SCREEN_W // 2 + 80, box.y + 115))

        if confirm_select == 0:
            pygame.draw.rect(screen, (255, 0, 0), b0_rect.inflate(30, 10), 1, border_radius=4)
        else:
            pygame.draw.rect(screen, C_GOLD, b1_rect.inflate(30, 10), 1, border_radius=4)

        screen.blit(b0_text, b0_rect)
        screen.blit(b1_text, b1_rect)

        pygame.display.flip()
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_LEFT, pygame.K_RIGHT, pygame.K_a, pygame.K_d]:
                    confirm_select = 1 - confirm_select
                elif event.key in [pygame.K_RETURN, pygame.K_KP_ENTER]:
                    return True if confirm_select == 0 else False
                elif event.key == pygame.K_ESCAPE:
                    return False

def launch_game(game_id, active_player_name, chosen_skin):
    """Launches sub-game, evaluating live remote game balancing metrics."""
    global global_fish_coins

    # Live balance settings downloaded instantly right before game startup parameters attach
    live_config = get_live_game_config()
    print(f" Attaching live balancing rules: {live_config}")

    score = 0

    if game_id == "sheep_maze":
        import sheep_maze
        score = sheep_maze.run()
    elif game_id == "fish_coin":
        import fish_coin
        score = fish_coin.run()
        if score:
            global_fish_coins += int(score)  # Convert score output directly into wallet balance
    elif game_id == "feed_crowd":
        import feed_crowd
        # Inject skin configuration to match minigame graphics natively
        score = feed_crowd.run(chosen_skin)
    elif game_id == "david_sling":
        import david_sling
        # Inject live balancing config from Redis to control Goliath's parameters
        score = david_sling.run(chosen_skin)
    elif game_id == "babel_tower":
        import babel_tower
        score = babel_tower.run(chosen_skin)

    if score and isinstance(score, (int, float)):
        save_high_score(game_id, active_player_name, int(score))
        save_player_profile(active_player_name) # Ensure wallet backups sync cleanly

    print(f"\n--- {game_id.upper()} CLOUD LEADERBOARD ---")
    top_records = get_top_scores(game_id)
    if top_records:
        for idx, (player, pts) in enumerate(top_records, start=1):
            print(f" {idx}. {player} — {int(pts)} pts")
    else:
        print(" No records logged yet. Be the first!")
    print("───────────────────────────────────\n")

def player_rect(px, py):
    return pygame.Rect(px - PLAYER_R, py - PLAYER_R, PLAYER_R * 2, PLAYER_R * 2)

def collides_world(px, py):
    pr = player_rect(px, py)
    for wr in WALLS:
        if pr.colliderect(wr): return True
    for cr in cabinet_rects():
        if pr.colliderect(cr): return True
    return False

def save_daily_score(game_id, player_name, score):
    if r:
        key = f"leaderboard:daily:{game_id}"
        r.zadd(key, {player_name: score})
        r.expire(key, 86400)

# ──────────────────────────────────────────────────────────────────────────────
# MAIN LOOP
# ──────────────────────────────────────────────────────────────────────────────
def main():
    chosen_skin = character_select.run_character_selection()

    # Pull selected identity identifier name context
    active_player_name = chosen_skin.get("name", "ArcadeHero")
    load_player_profile(active_player_name)

    pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Bible Quest — Arcade World")

    floor_surf = build_floor_surface()

    px = float(WORLD_W // 2)
    py = float(WORLD_H // 2)
    facing  = "down"
    moving  = False
    t       = 0.0

    sand_particles = []

    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        t += dt

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    mx, my = pygame.mouse.get_pos()
                    if SCREEN_W - 55 <= mx <= SCREEN_W - 27 and 4 <= my <= 34:
                        run_settings_menu()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    run_settings_menu()
                if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                    for cab in CABINETS:
                        cr = pygame.Rect(cab["wx"] - 60, cab["wy"] - 60, cab["cw"] + 120, cab["ch"] + 120)
                        pr = player_rect(px, py)
                        if pr.colliderect(cr) and cab["unlocked"]:
                            launch_game(cab["id"], active_player_name, chosen_skin)
                            pygame.display.set_mode((SCREEN_W, SCREEN_H))
                            pygame.display.set_caption("Bible Quest — Arcade World")

        keys = pygame.key.get_pressed()
        dx = dy = 0
        if keys[pygame.K_LEFT]  or keys[pygame.K_a]: dx -= SPEED; facing = "left"
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx += SPEED; facing = "right"
        if keys[pygame.K_UP]    or keys[pygame.K_w]: dy -= SPEED; facing = "up"
        if keys[pygame.K_DOWN]  or keys[pygame.K_s]: dy += SPEED; facing = "down"
        moving = (dx != 0 or dy != 0)

        new_x = max(WALL_THICKNESS + PLAYER_R, min(WORLD_W - WALL_THICKNESS - PLAYER_R, px + dx))
        new_y = max(WALL_THICKNESS + PLAYER_R, min(WORLD_H - WALL_THICKNESS - PLAYER_R, py + dy))
        if not collides_world(new_x, py): px = new_x
        if not collides_world(px, new_y): py = new_y

        cam_x = int(px - SCREEN_W // 2)
        cam_y = int(py - SCREEN_H // 2)
        cam_x = max(0, min(WORLD_W - SCREEN_W, cam_x))
        cam_y = max(0, min(WORLD_H - SCREEN_H, cam_y))

        if moving and random.random() < 0.40:
            sand_particles.append({
                "x": px + random.uniform(-6, 6),
                "y": py + 12,
                "vx": random.uniform(-1.0, 1.0) - (dx * 0.2),
                "vy": random.uniform(-1.5, -0.2),
                "life": 1.0,
                "size": random.randint(2, 4)
            })

        for p in sand_particles[:]:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["life"] -= 0.04
            if p["life"] <= 0:
                sand_particles.remove(p)

        near_cab = None
        for cab in CABINETS:
            cr = pygame.Rect(cab["wx"] - 60, cab["wy"] - 60, cab["cw"] + 120, cab["ch"] + 120)
            if player_rect(px, py).colliderect(cr):
                near_cab = cab
                break

        # ── DRAW ──────────────────────────────────────────────────────────
        screen.blit(floor_surf, (-cam_x, -cam_y))

        for idx, (wx, wy) in enumerate(TORCH_POSITIONS):
            draw_torch(screen, wx, wy, cam_x, cam_y, t, idx)

        for cab in CABINETS:
            near = (near_cab is not None and near_cab["id"] == cab["id"])
            draw_cabinet(screen, cab, t, cam_x, cam_y, near)

        for p in sand_particles:
            psx = int(p["x"]) - cam_x
            psy = int(p["y"]) - cam_y
            if 0 <= psx <= SCREEN_W and 0 <= psy <= SCREEN_H:
                alpha = int(255 * p["life"])
                p_surf = pygame.Surface((p["size"], p["size"]), pygame.SRCALPHA)
                p_surf.fill((90, 60, 35, alpha))
                screen.blit(p_surf, (psx, psy))

        sx = int(px) - cam_x
        sy = int(py) - cam_y
        draw_player(screen, sx, sy, facing, t, moving, chosen_skin)

        draw_hud(screen, near_cab, t)

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()