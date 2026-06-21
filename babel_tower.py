import pygame
import sys
import random

# ──────────────────────────────────────────────────────────────────────────────
# INIT & CONSTANTS
# ──────────────────────────────────────────────────────────────────────────────
SCREEN_W = 1100
SCREEN_H = 700

# Colors
C_SKY = (135, 206, 235)
C_CLOUDS = (255, 255, 255)
C_BRICK = (180, 70, 40)
C_BRICK_OUT = (100, 30, 20)
C_WOOD = (139, 69, 19)
C_SCAFFOLD = (205, 133, 63)
C_PLAYER = (40, 100, 200)
C_WORKER_SHIRT = (200, 180, 40)
C_SKIN = (220, 180, 140)
C_HAT = (200, 50, 50)
C_CONFUSED = (255, 100, 255)
C_TEXT = (255, 255, 255)
C_UI_BG = (0, 0, 0, 150)

GRAVITY = 0.5
PLAYER_SPEED = 5
JUMP_POWER = -10
CONFUSION_TIME = 180  # Frames (~3 seconds at 60fps)


def mf(size, bold=False):
    for n in ["Segoe UI Symbol", "Arial", "Georgia", None]:
        try:
            return pygame.font.SysFont(n, size, bold=bold)
        except Exception:
            pass
    return pygame.font.Font(None, size)


# ──────────────────────────────────────────────────────────────────────────────
# GAME ENTITIES
# ──────────────────────────────────────────────────────────────────────────────
class Player:
    def __init__(self):
        self.rect = pygame.Rect(100, SCREEN_H - 80, 20, 40)
        self.vel_y = 0
        self.on_ground = False
        self.on_ladder = False
        self.has_brick = False
        self.confusion_timer = 0
        self.fnt_small = mf(16, bold=True)

    def draw(self, surf):
        # Flash if confused
        is_confused = self.confusion_timer > 0
        shirt_color = C_CONFUSED if is_confused and (self.confusion_timer // 5) % 2 == 0 else C_PLAYER

        # Body
        pygame.draw.rect(surf, shirt_color, (self.rect.x, self.rect.y + 15, 20, 25))
        pygame.draw.rect(surf, (0, 0, 0), (self.rect.x, self.rect.y + 15, 20, 25), 2)
        # Head
        pygame.draw.circle(surf, C_SKIN, (self.rect.centerx, self.rect.y + 10), 10)

        # Draw brick if carrying
        if self.has_brick:
            pygame.draw.rect(surf, C_BRICK, (self.rect.centerx - 15, self.rect.top - 20, 30, 20))
            pygame.draw.rect(surf, C_BRICK_OUT, (self.rect.centerx - 15, self.rect.top - 20, 30, 20), 2)

        # Draw confusion text
        if is_confused:
            txt = self.fnt_small.render("CONFUSED!", True, (255, 50, 50))
            surf.blit(txt, txt.get_rect(center=(self.rect.centerx, self.rect.top - (30 if self.has_brick else 15))))


class Worker:
    def __init__(self, x, y, speed, min_x, max_x):
        self.rect = pygame.Rect(x, y, 20, 40)
        self.speed = speed
        self.min_x = min_x
        self.max_x = max_x

    def update(self):
        self.rect.x += self.speed
        # Reverse direction if hitting the edge of their platform bounds
        if self.rect.left <= self.min_x:
            self.rect.left = self.min_x + 1
            self.speed *= -1
        elif self.rect.right >= self.max_x:
            self.rect.right = self.max_x - 1
            self.speed *= -1

    def draw(self, surf):
        # Body
        pygame.draw.rect(surf, C_WORKER_SHIRT, (self.rect.x, self.rect.y + 15, 20, 25))
        pygame.draw.rect(surf, (0, 0, 0), (self.rect.x, self.rect.y + 15, 20, 25), 2)
        # Head
        pygame.draw.circle(surf, C_SKIN, (self.rect.centerx, self.rect.y + 10), 10)
        # Builder Hat
        pygame.draw.polygon(surf, C_HAT, [
            (self.rect.x - 2, self.rect.y + 5),
            (self.rect.right + 2, self.rect.y + 5),
            (self.rect.centerx, self.rect.y - 5)
        ])

        # Confusing speech bubble
        pygame.draw.circle(surf, (255, 255, 255), (self.rect.centerx + 15, self.rect.top - 10), 10)
        pygame.draw.circle(surf, (0, 0, 0), (self.rect.centerx + 15, self.rect.top - 10), 10, 1)
        # Little scribble text inside bubble
        pygame.draw.line(surf, (0, 0, 0), (self.rect.centerx + 10, self.rect.top - 12),
                         (self.rect.centerx + 20, self.rect.top - 12), 2)
        pygame.draw.line(surf, (0, 0, 0), (self.rect.centerx + 12, self.rect.top - 8),
                         (self.rect.centerx + 18, self.rect.top - 8), 2)


# ──────────────────────────────────────────────────────────────────────────────
# MAIN RUN FUNCTION
# ──────────────────────────────────────────────────────────────────────────────
def run():
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Tower of Babel - Action Builder")
    clock = pygame.time.Clock()

    fnt_big = mf(36, bold=True)
    fnt_med = mf(24)

    player = Player()

    # Level Design
    platforms = [
        pygame.Rect(0, SCREEN_H - 40, SCREEN_W, 40),  # Ground
        pygame.Rect(150, SCREEN_H - 180, 800, 20),  # Level 1
        pygame.Rect(150, SCREEN_H - 320, 800, 20),  # Level 2
        pygame.Rect(250, SCREEN_H - 460, 600, 20),  # Level 3
        pygame.Rect(350, SCREEN_H - 600, 400, 20),  # Top Level
    ]

    ladders = [
        pygame.Rect(200, SCREEN_H - 180, 40, 140),
        pygame.Rect(850, SCREEN_H - 180, 40, 140),
        pygame.Rect(530, SCREEN_H - 320, 40, 140),
        pygame.Rect(300, SCREEN_H - 460, 40, 140),
        pygame.Rect(750, SCREEN_H - 460, 40, 140),
        pygame.Rect(530, SCREEN_H - 600, 40, 140),
    ]

    # Workers now explicitly respect the platform bounds (min_x, max_x)
    workers = [
        Worker(300, SCREEN_H - 220, 2, 150, 950),  # On Level 1
        Worker(600, SCREEN_H - 220, -2.5, 150, 950),  # On Level 1
        Worker(200, SCREEN_H - 360, 3, 150, 950),  # On Level 2
        Worker(700, SCREEN_H - 360, -2, 150, 950),  # On Level 2
        Worker(400, SCREEN_H - 500, 3.5, 250, 850),  # On Level 3
    ]

    # Supply and Target Zones
    supply_zone = pygame.Rect(50, SCREEN_H - 100, 80, 60)
    target_zone = pygame.Rect(500, SCREEN_H - 680, 100, 80)

    tower_bricks_placed = 0
    bricks_needed = 5
    game_state = "playing"  # playing, won

    running = True
    while running:
        dt = clock.tick(60)

        # ─── EVENTS ───────────────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False  # Return to arcade

                if event.key == pygame.K_RETURN and game_state == "won":
                    running = False  # Return to arcade

        if game_state == "playing":
            keys = pygame.key.get_pressed()

            # Confusion logic
            dx = 0
            speed = PLAYER_SPEED

            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                dx = -speed
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                dx = speed

            # Reverse controls if confused!
            if player.confusion_timer > 0:
                dx = -dx
                player.confusion_timer -= 1

            # Ladder Logic
            player.on_ladder = False
            for lad in ladders:
                if player.rect.colliderect(lad):
                    player.on_ladder = True
                    break

            if player.on_ladder:
                player.vel_y = 0
                if keys[pygame.K_UP] or keys[pygame.K_w]:
                    player.vel_y = -speed
                elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
                    player.vel_y = speed
            else:
                # Apply Gravity
                player.vel_y += GRAVITY

                # Jump
                if (keys[pygame.K_UP] or keys[pygame.K_w] or keys[pygame.K_SPACE]) and player.on_ground:
                    player.vel_y = JUMP_POWER
                    player.on_ground = False

            # Apply X Movement & Collisions
            player.rect.x += dx
            player.rect.left = max(0, player.rect.left)
            player.rect.right = min(SCREEN_W, player.rect.right)

            # Apply Y Movement & Platform Collisions
            player.rect.y += player.vel_y
            player.on_ground = False

            if not player.on_ladder or player.vel_y > 0:
                for plat in platforms:
                    if player.rect.colliderect(plat) and player.vel_y > 0:
                        # Only land if falling from above
                        if player.rect.bottom <= plat.top + 15:
                            player.rect.bottom = plat.top
                            player.vel_y = 0
                            player.on_ground = True

            # Respawn logic if player falls completely off the screen
            if player.rect.top > SCREEN_H:
                player.rect.x = 100
                player.rect.y = SCREEN_H - 80
                player.vel_y = 0
                player.has_brick = False
                player.confusion_timer = 0

            # Worker Collisions (Causes Confusion and drops brick)
            for w in workers:
                w.update()
                if player.rect.colliderect(w.rect):
                    player.confusion_timer = CONFUSION_TIME
                    if player.has_brick:
                        player.has_brick = False  # Drop the brick!

            # Item Logic
            if not player.has_brick and player.rect.colliderect(supply_zone):
                player.has_brick = True

            if player.has_brick and player.rect.colliderect(target_zone):
                player.has_brick = False
                tower_bricks_placed += 1
                if tower_bricks_placed >= bricks_needed:
                    game_state = "won"

        # ─── DRAW ─────────────────────────────────────────────────────────────
        screen.fill(C_SKY)

        # Draw Scaffolding & Ladders
        for lad in ladders:
            pygame.draw.rect(screen, C_SCAFFOLD, lad)
            for ly in range(lad.top, lad.bottom, 20):
                pygame.draw.line(screen, C_WOOD, (lad.left, ly), (lad.right, ly), 3)

        for plat in platforms:
            pygame.draw.rect(screen, C_WOOD, plat)
            pygame.draw.rect(screen, (80, 40, 10), plat, 2)

        # Draw Supply & Target
        pygame.draw.rect(screen, (50, 50, 50), supply_zone)
        sz_text = fnt_med.render("BRICKS", True, C_TEXT)
        screen.blit(sz_text, sz_text.get_rect(center=supply_zone.center))

        pygame.draw.rect(screen, (200, 200, 200, 100), target_zone, 2, border_radius=5)
        tz_text = fnt_med.render("BUILD HERE", True, (50, 50, 50))
        screen.blit(tz_text, tz_text.get_rect(center=target_zone.center))

        # Draw built tower blocks in the target zone
        bx = target_zone.left + 10
        by = target_zone.bottom - 20
        for i in range(tower_bricks_placed):
            pygame.draw.rect(screen, C_BRICK, (bx, by, 80, 20))
            pygame.draw.rect(screen, C_BRICK_OUT, (bx, by, 80, 20), 2)
            by -= 20

        # Draw Entities
        for w in workers:
            w.draw(screen)
        player.draw(screen)

        # HUD
        hud = pygame.Surface((SCREEN_W, 50), pygame.SRCALPHA)
        hud.fill(C_UI_BG)
        screen.blit(hud, (0, 0))

        score_t = fnt_med.render(f"Bricks Placed: {tower_bricks_placed} / {bricks_needed}", True, C_TEXT)
        screen.blit(score_t, (20, 15))

        hint_t = fnt_med.render("Avoid workers! They confuse your languages (controls)!", True, (255, 200, 100))
        screen.blit(hint_t, hint_t.get_rect(center=(SCREEN_W // 2, 25)))

        if game_state == "won":
            overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))

            win_msg = fnt_big.render("TOWER COMPLETE!", True, (100, 255, 100))
            screen.blit(win_msg, win_msg.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 - 20)))

            ret_msg = fnt_med.render("Press ENTER to return to Arcade", True, C_TEXT)
            screen.blit(ret_msg, ret_msg.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 + 30)))

        pygame.display.flip()


if __name__ == "__main__":
    pygame.init()
    run()
    pygame.quit()