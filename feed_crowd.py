"""
Catch and Multiply — Feeding of the 5,000
============================================
"And they all ate and were filled... and they took up of the fragments
that remained twelve baskets full." — Matthew 14:20 (KJV)
"""

import pygame
import sys
import math
import random

# ─── Screen Constants ───────────────────────────────────────────────────────
SCREEN_W, SCREEN_H = 800, 600
HUD_HEIGHT = 90
GROUND_Y = SCREEN_H - 60          # where the disciple stands

# ─── Gameplay Constants ──────────────────────────────────────────────────────
SURVIVE_SECONDS     = 60.0
PLAYER_SPEED        = 360.0       # px/sec
BASKET_W, BASKET_H  = 70, 36

ITEM_FALL_SPEED_MIN = 140.0
ITEM_FALL_SPEED_MAX = 230.0
SPAWN_INTERVAL_MIN  = 0.35        # seconds between spawns
SPAWN_INTERVAL_MAX  = 0.85

ROCK_CHANCE         = 0.16        # probability a spawned item is a rock
CATCH_MULTIPLY      = 3           # +3 per loaf/fish caught
FEED_THRESHOLD      = 15          # combined inventory that triggers feeding
HUNGER_REFILL       = 25.0        # % restored when crowd is fed
HUNGER_DRAIN_PER_SEC = 100.0 / 23.0   # empties in ~23s if never fed

ROCK_STUN_DURATION  = 1.5
ROCK_PENALTY        = 5           # loaves & fish lost when hit by a rock

FEED_FLASH_DURATION = 1.2

# ─── Colours ────────────────────────────────────────────────────────────────
C_SKY        = (160, 200, 225)
C_HILL_FAR   = (140, 175, 110)
C_HILL_NEAR  = (100, 150, 80)
C_GROUND     = (150, 190, 110)
C_CROWD_DARK = ( 90,  70,  55)
C_LOAF       = (170, 120,  60)
C_LOAF_DARK  = (120,  80,  35)
C_FISH_BODY  = (170, 190, 200)
C_FISH_DARK  = ( 90, 120, 140)
C_ROCK       = (110, 110, 115)
C_ROCK_DARK  = ( 70,  70,  75)
C_BASKET     = (160, 120,  60)
C_BASKET_DARK= (110,  75,  35)
C_ROBE       = (140, 100, 170)
C_ROBE_DARK  = ( 95,  65, 125)
C_SKIN       = (210, 170, 130)
C_HUD_BG     = ( 25,  20,  15)
C_WHITE      = (255, 255, 255)
C_GOLD       = (235, 195, 100)
C_HUNGER_FULL= ( 90, 190,  90)
C_HUNGER_MID = (220, 180,  60)
C_HUNGER_LOW = (210,  70,  60)


def load_font(size, bold=False):
    for name in ["Georgia", "Times New Roman", "serif", None]:
        try: return pygame.font.SysFont(name, size, bold=bold)
        except Exception: pass
    return pygame.font.Font(None, size)


# ─── Falling Items ──────────────────────────────────────────────────────────
class FallingItem:
    def __init__(self, kind):
        self.kind = kind                       # "loaf" | "fish" | "rock"
        self.size = 26 if kind != "rock" else 24
        self.x = random.uniform(40, SCREEN_W - 40)
        self.y = -self.size
        self.speed = random.uniform(ITEM_FALL_SPEED_MIN, ITEM_FALL_SPEED_MAX)
        self.wobble_phase = random.uniform(0, math.tau)
        self.spin = random.uniform(-1.5, 1.5)
        self.angle = 0.0

    def update(self, dt, t):
        self.y += self.speed * dt
        self.x += math.sin(t * 2 + self.wobble_phase) * 12 * dt
        self.angle += self.spin * dt

    def off_screen(self):
        return self.y > SCREEN_H + 40

    def radius(self):
        return self.size * 0.55

    def draw(self, surface):
        x, y = int(self.x), int(self.y)
        if self.kind == "loaf":
            draw_loaf(surface, x, y, self.size)
        elif self.kind == "fish":
            draw_fish_item(surface, x, y, self.size, self.angle)
        elif self.kind == "rock":
            draw_rock(surface, x, y, self.size, self.angle)


def draw_loaf(surface, x, y, size):
    rect = pygame.Rect(0, 0, size * 1.5, size)
    rect.center = (x, y)
    pygame.draw.ellipse(surface, C_LOAF, rect)
    pygame.draw.ellipse(surface, C_LOAF_DARK, rect, width=2)
    for i in range(-1, 2):
        sx = x + i * size * 0.3
        pygame.draw.line(surface, C_LOAF_DARK, (sx, y - size * 0.3), (sx + 4, y), 2)


def draw_fish_item(surface, x, y, size, angle):
    body_w, body_h = size * 1.7, size * 0.8
    facing = 1 if math.cos(angle) >= 0 else -1
    tail_pts = [
        (x - facing * body_w * 0.5, y),
        (x - facing * (body_w * 0.5 + size * 0.5), y - size * 0.4),
        (x - facing * (body_w * 0.5 + size * 0.5), y + size * 0.4),
    ]
    pygame.draw.polygon(surface, C_FISH_DARK, tail_pts)
    body_rect = pygame.Rect(0, 0, body_w, body_h)
    body_rect.center = (x, y)
    pygame.draw.ellipse(surface, C_FISH_BODY, body_rect)
    eye_x = x + facing * body_w * 0.28
    pygame.draw.circle(surface, (20, 20, 20), (int(eye_x), int(y - 1)), 2)


def draw_rock(surface, x, y, size, angle):
    pts = []
    n = 7
    rng_amp = size * 0.5
    for i in range(n):
        a = angle + (math.tau / n) * i
        r = rng_amp * (0.8 + 0.2 * math.sin(i * 2.3))
        pts.append((x + math.cos(a) * r, y + math.sin(a) * r))
    pygame.draw.polygon(surface, C_ROCK, pts)
    pygame.draw.polygon(surface, C_ROCK_DARK, pts, width=2)


def draw_scenery(surface, t):
    surface.fill(C_SKY)
    pygame.draw.ellipse(surface, C_HILL_FAR, pygame.Rect(-100, GROUND_Y - 140, 600, 200))
    pygame.draw.ellipse(surface, C_HILL_NEAR, pygame.Rect(300, GROUND_Y - 110, 650, 180))
    pygame.draw.rect(surface, C_GROUND, pygame.Rect(0, GROUND_Y, SCREEN_W, SCREEN_H - GROUND_Y))

    # Procedural crowd silhouettes standing in background hills
    for x in range(30, SCREEN_W, 45):
        cy = GROUND_Y - 15 + int(4 * math.sin(x * 0.05))
        pygame.draw.circle(surface, C_CROWD_DARK, (x, cy - 24), 8)
        pygame.draw.polygon(surface, C_CROWD_DARK, [(x, cy - 16), (x - 12, cy + 10), (x + 12, cy + 10)])


def run():
    pygame.display.set_caption("Bible Quest — Catch & Multiply")
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    clock = pygame.time.Clock()

    font_big   = load_font(44, bold=True)
    font_med   = load_font(22, bold=True)
    font_hud   = load_font(18, bold=True)
    font_small = load_font(15)

    px = float(SCREEN_W // 2)
    loaves = 0
    fish = 0
    hunger = 100.0
    time_remaining = SURVIVE_SECONDS
    stun_timer = 0.0
    feed_flash_timer = 0.0

    items = []
    spawn_timer = 0.0
    t = 0.0

    running = True
    while running:
        dt = min(clock.tick(60) / 1000.0, 0.05)
        t += dt
        time_remaining = max(0.0, time_remaining - dt)

        # Game conditions checked
        game_over = hunger <= 0
        game_won = time_remaining <= 0 and hunger > 0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if event.key == pygame.K_r and (game_over or game_won):
                    px = float(SCREEN_W // 2)
                    loaves, fish = 0, 0
                    hunger = 100.0
                    time_remaining = SURVIVE_SECONDS
                    stun_timer, feed_flash_timer = 0.0, 0.0
                    items.clear()

        if not game_over and not game_won:
            # Drain hunger
            hunger = max(0.0, hunger - HUNGER_DRAIN_PER_SEC * dt)

            # Process timers
            if stun_timer > 0:
                stun_timer -= dt
            if feed_flash_timer > 0:
                feed_flash_timer -= dt

            # Handle player movement inputs if not stunned
            keys = pygame.key.get_pressed()
            if stun_timer <= 0:
                if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                    px -= PLAYER_SPEED * dt
                if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                    px += PLAYER_SPEED * dt
            px = max(BASKET_W // 2, min(SCREEN_W - BASKET_W // 2, px))

            # Random item spawn manager engine
            spawn_timer -= dt
            if spawn_timer <= 0:
                kind = "rock" if random.random() < ROCK_CHANCE else random.choice(["loaf", "fish"])
                items.append(FallingItem(kind))
                spawn_timer = random.uniform(SPAWN_INTERVAL_MIN, SPAWN_INTERVAL_MAX)

            # Update item iterations
            for item in items[:]:
                item.update(dt, t)
                if item.off_screen():
                    items.remove(item)
                    continue

                # Basket bounding box collision overlapping detector check
                basket_rect = pygame.Rect(px - BASKET_W // 2, GROUND_Y - 25, BASKET_W, 15)
                if basket_rect.collidepoint(item.x, item.y + item.radius()):
                    items.remove(item)
                    if item.kind == "rock":
                        stun_timer = ROCK_STUN_DURATION
                        loaves = max(0, loaves - ROCK_PENALTY)
                        fish = max(0, fish - ROCK_PENALTY)
                    else:
                        if item.kind == "loaf": loaves += CATCH_MULTIPLY
                        else: fish += CATCH_MULTIPLY

                        # Evaluate feeding threshold criteria rule
                        if (loaves + fish) >= FEED_THRESHOLD:
                            loaves, fish = 0, 0
                            hunger = min(100.0, hunger + HUNGER_REFILL)
                            feed_flash_timer = FEED_FLASH_DURATION

        # ─── DRAWING ROUTINES ─────────────────────────────────────────────────
        draw_scenery(screen, t)

        for item in items:
            item.draw(screen)

        # Draw Disciple character
        flicker = stun_timer > 0 and int(t * 12) % 2 == 0
        robe_c = (210, 80, 70) if flicker else C_ROBE
        pygame.draw.polygon(screen, robe_c, [(int(px), GROUND_Y - 46), (int(px) - 20, GROUND_Y), (int(px) + 20, GROUND_Y)])
        pygame.draw.circle(screen, C_SKIN, (int(px), GROUND_Y - 56), 10)

        # Draw Basket catch tool asset
        b_rect = pygame.Rect(int(px) - BASKET_W // 2, GROUND_Y - 20, BASKET_W, BASKET_H)
        pygame.draw.rect(screen, C_BASKET, b_rect, border_radius=6)
        pygame.draw.rect(screen, C_BASKET_DARK, b_rect, width=2, border_radius=6)

        # Render UI Head Information Strip bar overlay panel
        pygame.draw.rect(screen, C_HUD_BG, pygame.Rect(0, 0, SCREEN_W, HUD_HEIGHT))
        pygame.draw.line(screen, C_GOLD, (0, HUD_HEIGHT), (SCREEN_W, HUD_HEIGHT), 2)

        screen.blit(font_hud.render("Catch & Multiply: Feeding 5,000", True, C_GOLD), (16, 12))
        screen.blit(font_small.render(f"Basket Inventory: {loaves} Loaves, {fish} Fishes", True, C_WHITE), (16, 40))
        screen.blit(font_small.render("Catch food (+3 miracle). Avoid crashing rocks!", True, (160, 180, 200)), (16, 62))

        # Hunger Level Gauge bar construction rendering components
        screen.blit(font_hud.render("Crowd Hunger:", True, C_WHITE), (SCREEN_W - 320, 16))
        bar_w, bar_h = 160, 16
        bx, by = SCREEN_W - 180, 18
        pygame.draw.rect(screen, (40, 35, 30), pygame.Rect(bx, by, bar_w, bar_h), border_radius=4)
        h_col = C_HUNGER_FULL if hunger > 50 else (C_HUNGER_MID if hunger > 20 else C_HUNGER_LOW)
        pygame.draw.rect(screen, h_col, pygame.Rect(bx, by, int(bar_w * (hunger / 100.0)), bar_h), border_radius=4)

        time_str = f"Service: {time_remaining:0.1f}s"
        screen.blit(font_hud.render(time_str, True, C_GOLD), (SCREEN_W - 180, 48))

        # Miracle event banners splash flash messages notification card strings
        if feed_flash_timer > 0 and not (game_over or game_won):
            pulse = int(180 + 75 * math.sin(t * 15))
            f_txt = font_big.render("CROWD FED!", True, (40, pulse, 100))
            screen.blit(f_txt, f_txt.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 - 50)))

        if game_over or game_won:
            overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 195))
            screen.blit(overlay, (0, 0))

            if game_won:
                title_msg = font_big.render("Miracle Accomplished!", True, C_GOLD)
                sub_msg = font_med.render("The massive crowd ate and was entirely filled.", True, C_WHITE)
            else:
                title_msg = font_big.render("The Crowd Left Hungry", True, C_HUNGER_LOW)
                sub_msg = font_med.render("The hunger level ran out before service concluded.", True, C_WHITE)

            screen.blit(title_msg, title_msg.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 - 120)))
            screen.blit(sub_msg, sub_msg.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 - 60)))

            v1 = font_small.render('"And they all ate and were filled: and they took up of the fragments', True, (210, 190, 140))
            v2 = font_small.render(' that remained twelve baskets full." — Matthew 14:20', True, (210, 190, 140))
            exit_hint = font_hud.render("Press R to restart • Press ESC to exit to Portal", True, C_GOLD)

            screen.blit(v1, v1.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 + 30)))
            screen.blit(v2, v2.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 + 55)))
            screen.blit(exit_hint, exit_hint.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 + 150)))

        pygame.display.flip()

    # Reset video frame parameters back context to main matrix hub configuration bounds safely
    pygame.display.set_mode((1100, 700))
    pygame.display.set_caption("Bible Quest — Arcade World")