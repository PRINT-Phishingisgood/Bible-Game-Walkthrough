"""
Deep Sea Arcade Hook — Matthew 17:27
======================================
"...go thou to the sea, and cast an hook, and take up the fish that first
cometh up; and when thou hast opened his mouth, thou shalt find a piece
of money..." — Matthew 17:27 (KJV)

Asynchronous engine updated for native desktop PyCharm and linked directly
to automated Redis Cloud high-score submission vectors.
"""

import asyncio
import pygame
import sys
import math
import random

# ─── Screen / Layout Constants ─────────────────────────────────────────────
SCREEN_W, SCREEN_H = 800, 600
HUD_HEIGHT = 70
VIEWPORT_TOP = HUD_HEIGHT
VIEWPORT_H = SCREEN_H - HUD_HEIGHT

# ─── World Constants ────────────────────────────────────────────────────────
BOAT_WORLD_Y      = 0
HOOK_START_Y      = 14
WORLD_DEPTH       = 1700
TARGET_WORLD_Y    = WORLD_DEPTH

CAMERA_MIN = BOAT_WORLD_Y - 90
CAMERA_MAX = TARGET_WORLD_Y - VIEWPORT_H + 60

DROP_SPEED       = 900.0
ASCENT_DURATION  = 15.0
HOOK_H_SPEED     = 260.0
HOOK_RADIUS      = 14

NUM_OBSTACLES = 16

# ─── Colours ────────────────────────────────────────────────────────────────
C_SKY        = (130, 180, 210)
C_WATER_TOP  = ( 40, 110, 150)
C_WATER_DEEP = (  6,  25,  45)
C_BOAT_HULL  = (110,  70,  35)
C_BOAT_DARK  = ( 70,  40,  15)
C_BOAT_DECK  = (160, 120,  70)
C_ROPE       = (200, 180, 140)
C_HOOK       = (210, 210, 215)
C_HOOK_DARK  = (120, 120, 130)
C_GOLD       = (235, 190,  60)
C_GOLD_DARK  = (160, 120,  30)
C_COIN       = (250, 215, 100)
C_FISH_BODY  = [(180, 90, 90), (90, 130, 180), (90, 170, 110), (190, 150, 80), (150, 90, 170), (90, 160, 170)]
C_FISH_FIN   = (255, 255, 255)
C_HUD_BG     = ( 10,  20,  30)
C_WHITE      = (255, 255, 255)
C_TEXT_GOLD  = (235, 195, 100)
C_BUBBLE     = (200, 230, 240)


def load_font(size, bold=False):
    for name in ["Georgia", "Times New Roman", "serif", None]:
        try: return pygame.font.SysFont(name, size, bold=bold)
        except Exception: pass
    return pygame.font.Font(None, size)


def compute_camera_y(focus_world_y):
    cam = focus_world_y - VIEWPORT_H / 2
    return max(CAMERA_MIN, min(CAMERA_MAX, cam))


def world_to_screen_y(world_y, camera_y):
    return VIEWPORT_TOP + (world_y - camera_y)


# ─── Obstacle Fish ──────────────────────────────────────────────────────────
class ObstacleFish:
    def __init__(self, world_y=None):
        self.reset(random_x=True, world_y=world_y)

    def reset(self, random_x=False, world_y=None):
        self.world_y = world_y if world_y is not None else random.uniform(60, WORLD_DEPTH - 60)
        self.speed = random.uniform(50, 160)
        self.direction = random.choice([-1, 1])
        self.size = random.randint(14, 24)
        self.color = random.choice(C_FISH_BODY)
        self.bob_phase = random.uniform(0, math.tau)
        if random_x:
            self.x = random.uniform(0, SCREEN_W)
        else:
            self.x = -40 if self.direction == 1 else SCREEN_W + 40

    def update(self, dt, t):
        self.x += self.speed * self.direction * dt
        self.draw_world_y = self.world_y + math.sin(t * 2 + self.bob_phase) * 5
        if self.x < -50 or self.x > SCREEN_W + 50:
            self.reset(random_x=False, world_y=self.world_y)

    def rect_radius(self):
        return self.size * 0.9

    def draw(self, surface, camera_y):
        sy = world_to_screen_y(self.draw_world_y, camera_y)
        if sy < VIEWPORT_TOP - 40 or sy > SCREEN_H + 40:
            return
        x, y = int(self.x), int(sy)
        facing_right = self.direction > 0
        body_w, body_h = self.size * 1.8, self.size

        tail_dx = -1 if facing_right else 1
        tail_pts = [
            (x + tail_dx * body_w * 0.55, y),
            (x + tail_dx * (body_w * 0.55 + self.size * 0.7), y - self.size * 0.55),
            (x + tail_dx * (body_w * 0.55 + self.size * 0.7), y + self.size * 0.55),
        ]
        pygame.draw.polygon(surface, self.color, tail_pts)

        body_rect = pygame.Rect(0, 0, body_w, body_h)
        body_rect.center = (x, y)
        pygame.draw.ellipse(surface, self.color, body_rect)

        pygame.draw.polygon(surface, C_FISH_FIN, [
            (x, y - body_h * 0.5),
            (x - 6, y - body_h * 0.95),
            (x + 6, y - body_h * 0.95),
        ])

        eye_dx = body_w * 0.28 if facing_right else -body_w * 0.28
        pygame.draw.circle(surface, C_WHITE, (int(x + eye_dx), int(y - 2)), 4)
        pygame.draw.circle(surface, (10, 10, 10), (int(x + eye_dx + (2 if facing_right else -2)), int(y - 2)), 2)

    def collides_with(self, hook_x, hook_world_y, radius):
        dist = math.hypot(self.x - hook_x, self.draw_world_y - hook_world_y)
        return dist < (self.rect_radius() + radius)


# ─── Procedural Drawing ─────────────────────────────────────────────────────
def draw_water(surface, camera_y, t):
    surface.fill(C_SKY)
    pygame.draw.rect(surface, C_WATER_TOP, pygame.Rect(0, VIEWPORT_TOP, SCREEN_W, VIEWPORT_H))

    steps = 50
    band_h = VIEWPORT_H / steps
    for i in range(steps):
        screen_y = VIEWPORT_TOP + i * band_h
        world_y = camera_y + (screen_y - VIEWPORT_TOP)
        frac = max(0.0, min(1.0, world_y / WORLD_DEPTH))
        r = int(C_WATER_TOP[0] + (C_WATER_DEEP[0] - C_WATER_TOP[0]) * frac)
        g = int(C_WATER_TOP[1] + (C_WATER_DEEP[1] - C_WATER_TOP[1]) * frac)
        b = int(C_WATER_TOP[2] + (C_WATER_DEEP[2] - C_WATER_TOP[2]) * frac)
        pygame.draw.rect(surface, (r, g, b), pygame.Rect(0, int(screen_y), SCREEN_W, int(band_h) + 1))

    surface_screen_y = world_to_screen_y(0, camera_y)
    if VIEWPORT_TOP - 10 <= surface_screen_y <= SCREEN_H + 10:
        for x in range(0, SCREEN_W, 6):
            wy = surface_screen_y + math.sin(x * 0.05 + t * 2) * 3
            pygame.draw.line(surface, (200, 230, 240), (x, wy), (x + 6, wy), 2)


def draw_boat(surface, camera_y, t):
    bx = SCREEN_W // 2
    deck_sy = world_to_screen_y(BOAT_WORLD_Y, camera_y)

    if deck_sy > SCREEN_H + 80 or deck_sy < VIEWPORT_TOP - 120:
        return None

    bob = math.sin(t * 1.5) * 4

    hull_pts = [
        (bx - 110, deck_sy + 10), (bx + 110, deck_sy + 10),
        (bx + 85, deck_sy + 38), (bx - 85, deck_sy + 38),
    ]
    pygame.draw.polygon(surface, C_BOAT_HULL, hull_pts)
    pygame.draw.polygon(surface, C_BOAT_DARK, hull_pts, width=3)

    pygame.draw.rect(surface, C_BOAT_DECK, pygame.Rect(bx - 100, deck_sy - 8, 200, 18), border_radius=3)
    pygame.draw.line(surface, C_BOAT_DARK, (bx, deck_sy - 8), (bx, deck_sy - 60), 5)
    pygame.draw.polygon(surface, (230, 225, 210), [
        (bx, deck_sy - 58),
        (bx + 40, deck_sy - 38 + bob * 0.3),
        (bx, deck_sy - 22),
    ])
    return deck_sy


def draw_rope(surface, boat_x, deck_sy, hook_x, hook_sy, skin_data=None):
    if deck_sy is None:
        return
    rod_tip = (boat_x + 95, deck_sy + 4)
    pygame.draw.line(surface, C_BOAT_DARK, (boat_x + 70, deck_sy + 2), rod_tip, 4)
    # Map line rope colors to selected player characteristics for portal uniformity
    line_color = skin_data["color"] if skin_data else C_ROPE
    pygame.draw.line(surface, line_color, rod_tip, (hook_x, hook_sy), 2)


def draw_hook(surface, x, y, carrying_fish):
    if carrying_fish:
        draw_coin_fish(surface, x, y - 10)

    pygame.draw.line(surface, C_HOOK_DARK, (x, y - 14), (x, y + 2), 3)
    pygame.draw.arc(surface, C_HOOK, pygame.Rect(x - 10, y - 4, 20, 20), math.pi * 0.05, math.pi * 1.5, 3)
    pygame.draw.circle(surface, C_HOOK, (x + 9, y + 8), 2)


def draw_coin_fish(surface, x, y):
    glow = pygame.Surface((70, 70), pygame.SRCALPHA)
    pygame.draw.circle(glow, (255, 220, 120, 60), (35, 35), 30)
    surface.blit(glow, (x - 35, y - 35), special_flags=pygame.BLEND_RGBA_ADD)

    body_rect = pygame.Rect(0, 0, 46, 26)
    body_rect.center = (x, y)
    pygame.draw.ellipse(surface, C_GOLD, body_rect)
    pygame.draw.ellipse(surface, C_GOLD_DARK, body_rect, width=2)

    pygame.draw.polygon(surface, C_GOLD_DARK, [(x - 23, y), (x - 36, y - 12), (x - 36, y + 12)])
    pygame.draw.circle(surface, C_WHITE, (x + 14, y - 3), 4)
    pygame.draw.circle(surface, (20, 15, 5), (x + 16, y - 3), 2)
    pygame.draw.circle(surface, C_COIN, (x + 22, y + 2), 6)
    pygame.draw.circle(surface, C_GOLD_DARK, (x + 22, y + 2), 6, width=1)


def draw_bubbles(surface, bubbles, camera_y, t):
    for b in bubbles:
        sy = world_to_screen_y(b["world_y"], camera_y)
        if sy < VIEWPORT_TOP - 10 or sy > SCREEN_H + 10:
            continue
        wob = math.sin(t * 3 + b["phase"]) * 3
        pygame.draw.circle(surface, C_BUBBLE, (int(b["x"] + wob), int(sy)), b["r"], width=1)


def update_bubbles(bubbles, dt):
    for b in bubbles:
        b["world_y"] -= b["speed"] * dt
        if b["world_y"] < -20:
            b["world_y"] = WORLD_DEPTH + random.uniform(0, 40)
            b["x"] = random.uniform(0, SCREEN_W)


def draw_hud(surface, font_hud, font_small, phase, time_left, depth_frac):
    hud_rect = pygame.Rect(0, 0, SCREEN_W, HUD_HEIGHT)
    pygame.draw.rect(surface, C_HUD_BG, hud_rect)
    pygame.draw.line(surface, C_GOLD, (0, HUD_HEIGHT), (SCREEN_W, HUD_HEIGHT), 2)

    title = font_hud.render("Deep Sea Arcade Hook", True, C_TEXT_GOLD)
    surface.blit(title, (16, 8))

    if phase == "ascent":
        timer_txt = font_hud.render(f"Surface in: {time_left:0.1f}s", True, C_WHITE)
        surface.blit(timer_txt, (SCREEN_W - timer_txt.get_width() - 16, 8))
        hint = font_small.render("LEFT / RIGHT to steer the hook", True, (160, 190, 210))
        surface.blit(hint, (16, 40))
    elif phase == "drop":
        hint = font_small.render("Casting the line...", True, (160, 190, 210))
        surface.blit(hint, (16, 40))
    elif phase == "catch":
        hint = font_small.render("A fish has taken the hook!", True, C_TEXT_GOLD)
        surface.blit(hint, (16, 40))

    bar_w, bar_h = 140, 8
    bx, by = SCREEN_W - bar_w - 16, 36
    pygame.draw.rect(surface, (40, 40, 50), pygame.Rect(bx, by, bar_w, bar_h), border_radius=4)
    fill_w = int(bar_w * max(0.0, min(1.0, depth_frac)))
    pygame.draw.rect(surface, C_TEXT_GOLD, pygame.Rect(bx, by, fill_w, bar_h), border_radius=4)


def draw_end_screen(surface, won, font_big, font_med, font_small, t):
    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 185))
    surface.blit(overlay, (0, 0))

    glow = int(200 + 55 * math.sin(t * 2))
    gold = (glow, int(glow * 0.82), 50)

    if won:
        lines = [
            (font_big, "Miracle Unlocked!", gold),
            (font_med, "You hauled the fish safely and discovered a piece of money!", C_WHITE),
        ]
    else:
        lines = [
            (font_big, "The Line Snapped!", (220, 90, 70)),
            (font_med, "The hook struck another fish on the way up.", C_WHITE),
        ]

    verse_lines = [
        (font_small, '"...go thou to the sea, and cast an hook, and take up', (200, 175, 120)),
        (font_small, ' the fish that first cometh up; and when thou hast', (200, 175, 120)),
        (font_small, ' opened his mouth, thou shalt find a piece of money."', (200, 175, 120)),
        (font_small, "— Matthew 17:27", (170, 145, 95)),
        (font_small, "Press ENTER to return to Portal and collect your coins", (150, 150, 150)),
    ]

    y = SCREEN_H // 2 - 150
    for fnt, text, color in lines:
        surf = fnt.render(text, True, color)
        surface.blit(surf, surf.get_rect(center=(SCREEN_W // 2, y)))
        y += fnt.get_height() + 10

    y += 14
    for fnt, text, color in verse_lines:
        surf = fnt.render(text, True, color)
        surface.blit(surf, surf.get_rect(center=(SCREEN_W // 2, y)))
        y += fnt.get_height() + 4


# ─── Main Run ────────────────────────────────────────────────────────────────
def run(skin_data=None):
    pygame.display.set_caption("Bible Quest — Deep Sea Arcade Hook")
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    clock = pygame.time.Clock()

    font_big   = load_font(50, bold=True)
    font_med   = load_font(22)
    font_hud   = load_font(20, bold=True)
    font_small = load_font(15)

    def new_game():
        obstacles = []
        for i in range(NUM_OBSTACLES):
            band_y = (WORLD_DEPTH / NUM_OBSTACLES) * i + random.uniform(20, 60)
            obstacles.append(ObstacleFish(world_y=band_y))

        bubbles = [
            {"x": random.uniform(0, SCREEN_W),
             "world_y": random.uniform(0, WORLD_DEPTH),
             "r": random.randint(2, 5),
             "speed": random.uniform(40, 90),
             "phase": random.uniform(0, math.tau)}
            for _ in range(35)
        ]

        return {
            "phase": "drop",
            "hook_x": SCREEN_W // 2,
            "hook_world_y": float(HOOK_START_Y),
            "catch_timer": 0.0,
            "ascent_elapsed": 0.0,
            "obstacles": obstacles,
            "bubbles": bubbles,
        }

    state = new_game()
    t = 0.0
    running = True

    while running:
        dt = clock.tick(60) / 1000.0
        dt = min(dt, 0.05)
        t += dt

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if event.key == pygame.K_RETURN and state["phase"] in ("win", "lose"):
                    if state["phase"] == "win":
                        # Calculate final coin generation score: base value + speed bonus
                        coins_found = int(10 + max(0, 40 - int(state["ascent_elapsed"])))
                        return coins_found
                    return 0

        keys = pygame.key.get_pressed()
        move_left  = keys[pygame.K_LEFT]
        move_right = keys[pygame.K_RIGHT]

        boat_x = SCREEN_W // 2

        for fish in state["obstacles"]:
            fish.update(dt, t)
        update_bubbles(state["bubbles"], dt)

        # ── Phase logic ─────────────────────────────────────────────────
        if state["phase"] == "drop":
            state["hook_world_y"] += DROP_SPEED * dt
            if state["hook_world_y"] >= TARGET_WORLD_Y:
                state["hook_world_y"] = TARGET_WORLD_Y
                state["phase"] = "catch"
                state["catch_timer"] = 0.6

        elif state["phase"] == "catch":
            state["catch_timer"] -= dt
            if state["catch_timer"] <= 0:
                state["phase"] = "ascent"
                ascent_distance = TARGET_WORLD_Y - HOOK_START_Y
                state["ascent_speed"] = ascent_distance / ASCENT_DURATION
                state["ascent_elapsed"] = 0.0

        elif state["phase"] == "ascent":
            if move_left:
                state["hook_x"] -= HOOK_H_SPEED * dt
            if move_right:
                state["hook_x"] += HOOK_H_SPEED * dt
            state["hook_x"] = max(20, min(SCREEN_W - 20, state["hook_x"]))

            state["hook_world_y"] -= state["ascent_speed"] * dt
            state["ascent_elapsed"] += dt

            if state["hook_world_y"] <= HOOK_START_Y:
                state["hook_world_y"] = HOOK_START_Y
                state["phase"] = "win"

            for fish in state["obstacles"]:
                if fish.collides_with(state["hook_x"], state["hook_world_y"], HOOK_RADIUS):
                    state["phase"] = "lose"
                    break

        # ── Camera ───────────────────────────────────────────────────────
        camera_y = compute_camera_y(state["hook_world_y"])

        # ── Draw ─────────────────────────────────────────────────────────
        draw_water(screen, camera_y, t)
        draw_bubbles(screen, state["bubbles"], camera_y, t)

        for fish in state["obstacles"]:
            fish.draw(screen, camera_y)

        deck_sy = draw_boat(screen, camera_y, t)
        hook_sy = world_to_screen_y(state["hook_world_y"], camera_y)
        draw_rope(screen, boat_x, deck_sy, state["hook_x"], hook_sy, skin_data)

        carrying = state["phase"] in ("catch", "ascent", "win")
        draw_hook(screen, int(state["hook_x"]), int(hook_sy), carrying)

        time_left = max(0.0, ASCENT_DURATION - state["ascent_elapsed"])
        depth_frac = state["hook_world_y"] / WORLD_DEPTH
        draw_hud(screen, font_hud, font_small, state["phase"], time_left, depth_frac)

        if state["phase"] in ("win", "lose"):
            draw_end_screen(screen, state["phase"] == "win", font_big, font_med, font_small, t)

        pygame.display.flip()

    return 0


if __name__ == "__main__":
    pygame.init()
    pygame.font.init()
    run()
    pygame.quit()
    sys.exit()