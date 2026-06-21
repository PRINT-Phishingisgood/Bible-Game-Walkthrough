import pygame
import sys
import math


def run_character_selection():
    """Standard local desktop character selector loop."""
    pygame.init()
    pygame.font.init()

    w, h = 1100, 700
    screen = pygame.display.set_mode((w, h))
    pygame.display.set_caption("Bible Quest — Character Selection")
    clock = pygame.time.Clock()

    # Fonts
    font_main_title = pygame.font.SysFont("Georgia", 48, bold=True)
    font_title = pygame.font.SysFont("Georgia", 32, bold=True)
    font_author = pygame.font.SysFont("Georgia", 16, italic=True)
    font_med = pygame.font.SysFont("Arial", 22)
    font_sm = pygame.font.SysFont("Arial", 16)

    # Options
    characters = [
        {"name": "Shepherd", "color": (170, 130, 70), "inner": (145, 108, 55), "cloth": (140, 105, 55),
         "has_staff": True},
        {"name": "Mary", "color": (80, 120, 190), "inner": (60, 95, 160), "cloth": (220, 220, 240), "has_staff": False}
    ]
    selected = 0

    def draw_preview(surf, cx, cy, char, bob):
        pygame.draw.ellipse(surf, (15, 10, 5), pygame.Rect(cx - 24, cy + 28, 48, 16))
        robe_pts = [(cx, cy - 40 + bob), (cx - 22, cy + 36 + bob), (cx + 22, cy + 36 + bob)]
        pygame.draw.polygon(surf, char["color"], robe_pts)
        inner_pts = [(cx, cy - 28 + bob), (cx - 10, cy + 28 + bob), (cx + 10, cy + 28 + bob)]
        pygame.draw.polygon(surf, char["inner"], inner_pts)

        head_y = cy - 60 + bob
        pygame.draw.circle(surf, (210, 170, 115), (cx, head_y), 20)
        pygame.draw.arc(surf, char["cloth"], pygame.Rect(cx - 22, head_y - 22, 44, 28), 0, 3.14, 6)
        pygame.draw.circle(surf, (40, 25, 10), (cx - 6, head_y + 4), 4)
        pygame.draw.circle(surf, (40, 25, 10), (cx + 6, head_y + 4), 4)

        if char["has_staff"]:
            pygame.draw.line(surf, (100, 65, 25), (cx + 26, cy + 36 + bob), (cx + 26, cy - 70 + bob), 5)
            pygame.draw.arc(surf, (100, 65, 25), pygame.Rect(cx + 12, cy - 86 + bob, 28, 20), 0.6 * 3.14, 2 * 3.14, 5)

    t = 0
    running = True
    while running:
        t += 1
        bob = int(4 * math.sin(t * 0.1))

        screen.fill((25, 18, 12))

        main_title_surf = font_main_title.render("The Gospel Game", True, (235, 190, 60))
        screen.blit(main_title_surf, main_title_surf.get_rect(center=(w // 2, 45)))

        author_surf = font_author.render("Created by Andrew Zheng & Anisa Chang", True, (160, 130, 80))
        screen.blit(author_surf, author_surf.get_rect(center=(w // 2, 85)))

        title_surf = font_title.render("SELECT YOUR HERO", True, (210, 170, 50))
        screen.blit(title_surf, title_surf.get_rect(center=(w // 2, 140)))

        for idx, char in enumerate(characters):
            box_x = w // 2 - 320 + idx * 360
            box_y = 200
            box_rect = pygame.Rect(box_x, box_y, 280, 340)

            bg_col = (50, 38, 26) if idx == selected else (35, 26, 18)
            border_col = (255, 215, 80) if idx == selected else (80, 60, 45)
            border_w = 4 if idx == selected else 2

            pygame.draw.rect(screen, bg_col, box_rect, border_radius=12)
            pygame.draw.rect(screen, border_col, box_rect, border_w, border_radius=12)

            draw_preview(screen, box_rect.centerx, box_rect.centery - 20, char, bob if idx == selected else 0)

            lbl = font_med.render(char["name"], True, (240, 220, 170) if idx == selected else (160, 130, 80))
            screen.blit(lbl, lbl.get_rect(center=(box_rect.centerx, box_rect.bottom - 40)))

        hint = font_sm.render("Use LEFT / RIGHT Arrow Keys to Switch Selection • Press ENTER to Confirm", True,
                              (130, 100, 60))
        screen.blit(hint, hint.get_rect(center=(w // 2, 620)))

        pygame.display.flip()
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_LEFT, pygame.K_a, pygame.K_RIGHT, pygame.K_d]:
                    selected = 1 - selected
                if event.key in [pygame.K_RETURN, pygame.K_KP_ENTER]:
                    return characters[selected]