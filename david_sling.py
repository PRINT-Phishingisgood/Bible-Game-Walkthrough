"""
Sling Artillery — 1 Samuel 17 (David & Goliath)
================================================
"And David put his hand in his bag, and took thence a stone, and slang it,
and smote the Philistine in his forehead..." — 1 Samuel 17:49 (KJV)

Fully optimized for desktop PyCharm execution and Redis Cloud Leaderboard synchronization.
"""

import pygame
import sys
import math
import random

# ─── Screen / World Layout ──────────────────────────────────────────────────
SCREEN_W, SCREEN_H = 900, 600
GROUND_Y           = 500

DAVID_X            = 120
SLING_ANCHOR       = (138, 430)
GRAB_RADIUS        = 70

# ─── Sling Physics ──────────────────────────────────────────────────────────
MAX_PULL    = 175.0
POWER_SCALE = 7.0
MIN_PULL    = 14.0
STONE_R     = 9

PREVIEW_STEPS = 5
PREVIEW_DT    = 0.05
SUBSTEPS      = 5

# ─── Goliath Base States ────────────────────────────────────────────────────
GOLIATH_START_X = 775
DANGER_X        = 250
BODY_DAMAGE     = 0.04
KNOCKBACK       = 26

# ─── Colours ────────────────────────────────────────────────────────────────
C_SKY_TOP   = (150, 195, 225)
C_SKY_BOT   = (215, 230, 240)
C_HILL_FAR  = (150, 170, 130)
C_HILL_NEAR = (120, 150, 100)
C_GROUND    = (175, 145, 95)
C_GROUND_DK = (140, 112, 70)
C_GRASS     = (110, 160, 80)

C_SLING      = (90, 70, 50)
C_STONE      = (130, 128, 122)
C_STONE_HI   = (185, 182, 175)

C_GOL_SKIN   = (200, 160, 120)
C_GOL_SKIN_D = (160, 122, 88)
C_GOL_ARMOR  = (120, 95, 60)
C_GOL_ARMOR_D= (90, 70, 42)
C_GOL_HELM   = (110, 110, 125)
C_GOL_HELM_D = (75, 75, 90)
C_GOL_KILT   = (140, 60, 55)
C_GOL_BEARD  = (60, 45, 35)
C_FOREHEAD   = (235, 200, 160)
C_FOREHEAD_GLOW = (255, 235, 150)

C_HUD_BG     = (20, 25, 35)
C_WHITE      = (255, 255, 255)
C_GOLD       = (235, 195, 100)
C_RED        = (200, 70, 60)
C_GREEN      = (90, 180, 90)
C_TRAJ       = (40, 40, 50)


def load_font(size, bold=False):
    for name in ["Georgia", "Times New Roman", "serif", None]:
        try:
            return pygame.font.SysFont(name, size, bold=bold)
        except Exception:
            pass
    return pygame.font.Font(None, size)

def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def goliath_geometry(gx):
    head_r   = 42
    head_cx  = gx
    head_cy  = GROUND_Y - 248
    fh_w, fh_h = 60, 26
    forehead_rect = pygame.Rect(head_cx - fh_w // 2, head_cy - head_r, fh_w, fh_h)

    body_w   = 132
    body_top = head_cy + head_r - 6
    torso_rect = pygame.Rect(gx - body_w // 2, body_top, body_w, GROUND_Y - body_top)
    return {
        "gx": gx,
        "head_center": (head_cx, head_cy),
        "head_r": head_r,
        "forehead_rect": forehead_rect,
        "torso_rect": torso_rect,
        "body_w": body_w,
        "body_top": body_top,
    }


def circle_rect_collide(cx, cy, r, rect):
    nx = clamp(cx, rect.left, rect.right)
    ny = clamp(cy, rect.top, rect.bottom)
    dx, dy = cx - nx, cy - ny
    return dx * dx + dy * dy <= r * r


def predict_trajectory(ax, ay, vx, vy, gravity):
    pts = []
    x, y = ax, ay
    for _ in range(PREVIEW_STEPS):
        vy += gravity * PREVIEW_DT
        x  += vx * PREVIEW_DT
        y  += vy * PREVIEW_DT
        if y >= GROUND_Y:
            pts.append((x, GROUND_Y))
            break
        if x < -60 or x > SCREEN_W + 60:
            break
        pts.append((x, y))
    return pts


def draw_background(surf, t):
    for i in range(0, GROUND_Y, 4):
        f = i / GROUND_Y
        r = int(C_SKY_TOP[0] + (C_SKY_BOT[0] - C_SKY_TOP[0]) * f)
        g = int(C_SKY_TOP[1] + (C_SKY_BOT[1] - C_SKY_TOP[1]) * f)
        b = int(C_SKY_TOP[2] + (C_SKY_BOT[2] - C_SKY_TOP[2]) * f)
        pygame.draw.rect(surf, (r, g, b), pygame.Rect(0, i, SCREEN_W, 4))

    for cx0, cy0, s in [(180, 80, 1.0), (520, 130, 0.8), (760, 70, 1.1)]:
        cx = (cx0 + t * 12) % (SCREEN_W + 160) - 80
        for ox, oy, rr in [(0, 0, 26), (34, 6, 20), (-30, 8, 18)]:
            pygame.draw.circle(surf, (245, 248, 252), (int(cx + ox * s), int(cy0 + oy)), int(rr * s))

    pygame.draw.ellipse(surf, C_HILL_FAR, pygame.Rect(-120, GROUND_Y - 150, 700, 300))
    pygame.draw.ellipse(surf, C_HILL_NEAR, pygame.Rect(380, GROUND_Y - 120, 800, 260))

    pygame.draw.rect(surf, C_GROUND, pygame.Rect(0, GROUND_Y, SCREEN_W, SCREEN_H - GROUND_Y))
    pygame.draw.rect(surf, C_GRASS, pygame.Rect(0, GROUND_Y - 6, SCREEN_W, 8))
    for x in range(0, SCREEN_W, 26):
        pygame.draw.line(surf, C_GROUND_DK, (x, GROUND_Y + 18), (x + 12, GROUND_Y + 18), 2)


def draw_david(surf, anchor, aiming, t, skin_data):
    fx, fy = DAVID_X, GROUND_Y

    # Apply dynamic colors passed from Redis cloud state
    skin_col = (215, 175, 135)
    tunic_col = skin_data["color"] if skin_data else (180, 120, 70)
    sash_col = skin_data["inner"] if skin_data else (120, 70, 40)
    cloth_col = skin_data["cloth"] if skin_data else (90, 60, 40)

    pygame.draw.rect(surf, sash_col, pygame.Rect(fx - 12, fy - 34, 9, 34), border_radius=3)
    pygame.draw.rect(surf, sash_col, pygame.Rect(fx + 3, fy - 34, 9, 34), border_radius=3)

    pygame.draw.rect(surf, tunic_col, pygame.Rect(fx - 16, fy - 70, 32, 42), border_radius=6)
    pygame.draw.line(surf, sash_col, (fx - 16, fy - 56), (fx + 16, fy - 48), 4)

    pygame.draw.circle(surf, skin_col, (fx, fy - 84), 13)
    pygame.draw.arc(surf, cloth_col, pygame.Rect(fx - 13, fy - 99, 26, 24), math.pi * 0.1, math.pi * 0.9, 5)

    pygame.draw.line(surf, skin_col, (fx + 8, fy - 64), anchor, 6)

    if not aiming:
        rr = 30 + int(4 * math.sin(t * 4))
        ring = pygame.Surface((rr * 2 + 4, rr * 2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(ring, (255, 235, 120, 70), (rr + 2, rr + 2), rr, 2)
        surf.blit(ring, (fx - rr - 2, fy - 60 - rr))


def draw_sling(surf, anchor, pouch, power_frac):
    fork_top = (anchor[0] - 10, anchor[1] - 26)
    fork_bot = (anchor[0] - 10, anchor[1] + 8)
    pygame.draw.line(surf, C_SLING, fork_top, pouch, 4)
    pygame.draw.line(surf, C_SLING, fork_bot, pouch, 4)

    col = (int(C_STONE[0] + (C_RED[0] - C_STONE[0]) * power_frac),
           int(C_STONE[1] * (1 - power_frac) + 40 * power_frac),
           int(C_STONE[2] * (1 - power_frac) + 40 * power_frac))
    pygame.draw.circle(surf, col, (int(pouch[0]), int(pouch[1])), STONE_R + 1)
    pygame.draw.circle(surf, C_STONE_HI, (int(pouch[0]) - 3, int(pouch[1]) - 3), 3)


def draw_trajectory(surf, pts):
    for i, (x, y) in enumerate(pts):
        fade = 1.0 - i / max(1, len(pts))
        r = 4 if i % 2 == 0 else 3
        col = (C_TRAJ[0], C_TRAJ[1], C_TRAJ[2])
        dot = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(dot, (*col, int(60 + 150 * fade)), (r, r), r)
        surf.blit(dot, (int(x - r), int(y - r)))


def draw_stone(surf, x, y):
    pygame.draw.circle(surf, C_STONE, (int(x), int(y)), STONE_R)
    pygame.draw.circle(surf, C_STONE_HI, (int(x) - 3, int(y) - 3), 3)
    pygame.draw.circle(surf, (90, 88, 84), (int(x), int(y)), STONE_R, 1)


def draw_goliath(surf, geom, health_frac, flash, walk_phase, defeated):
    gx = geom["gx"]
    hx, hy = geom["head_center"]
    hr = geom["head_r"]
    body = geom["torso_rect"]
    fh = geom["forehead_rect"]

    pygame.draw.rect(surf, C_GOL_ARMOR_D, pygame.Rect(gx - 34, GROUND_Y - 78, 26, 78), border_radius=4)
    pygame.draw.rect(surf, C_GOL_ARMOR_D, pygame.Rect(gx + 8, GROUND_Y - 78, 26, 78), border_radius=4)
    pygame.draw.ellipse(surf, (60, 45, 30), pygame.Rect(gx - 40, GROUND_Y - 12, 34, 14))
    pygame.draw.ellipse(surf, (60, 45, 30), pygame.Rect(gx + 6, GROUND_Y - 12, 34, 14))

    pygame.draw.rect(surf, C_GOL_KILT, pygame.Rect(gx - 40, GROUND_Y - 92, 80, 28), border_radius=4)
    for i in range(-3, 4):
        pygame.draw.line(surf, C_GOL_ARMOR_D, (gx + i * 11, GROUND_Y - 92), (gx + i * 11, GROUND_Y - 64), 2)

    torso = pygame.Rect(gx - 50, body.top, 100, GROUND_Y - 92 - body.top)
    pygame.draw.rect(surf, C_GOL_ARMOR, torso, border_radius=10)
    pygame.draw.rect(surf, C_GOL_ARMOR_D, torso, width=3, border_radius=10)
    for ry in range(torso.top + 12, torso.bottom - 6, 14):
        for rx in range(torso.left + 12, torso.right - 6, 18):
            pygame.draw.arc(surf, C_GOL_ARMOR_D, pygame.Rect(rx, ry, 16, 14), math.pi, math.tau, 2)

    pygame.draw.circle(surf, C_GOL_ARMOR, (torso.left + 6, torso.top + 8), 16)
    pygame.draw.circle(surf, C_GOL_ARMOR, (torso.right - 6, torso.top + 8), 16)

    sp_top = (gx + 70, GROUND_Y - 250)
    sp_bot = (gx + 52, GROUND_Y - 70)
    pygame.draw.line(surf, (110, 80, 45), sp_bot, sp_top, 5)
    pygame.draw.polygon(surf, (180, 180, 195),
                        [(sp_top[0] - 7, sp_top[1] + 14), (sp_top[0] + 7, sp_top[1] + 14), (sp_top[0], sp_top[1] - 12)])

    pygame.draw.circle(surf, C_GOL_HELM_D, (gx - 56, GROUND_Y - 150), 30)
    pygame.draw.circle(surf, C_GOL_HELM, (gx - 56, GROUND_Y - 150), 30, 4)
    pygame.draw.circle(surf, C_GOLD, (gx - 56, GROUND_Y - 150), 7)

    pygame.draw.rect(surf, C_GOL_SKIN_D, pygame.Rect(hx - 12, hy + hr - 12, 24, 18))
    pygame.draw.circle(surf, C_GOL_SKIN, (hx, hy), hr)
    pygame.draw.circle(surf, C_GOL_SKIN_D, (hx, hy), hr, 2)
    pygame.draw.polygon(surf, C_GOL_BEARD, [(hx - hr + 6, hy + 6), (hx + hr - 6, hy + 6), (hx + 16, hy + hr + 22), (hx - 16, hy + hr + 22)])
    pygame.draw.line(surf, C_GOL_BEARD, (hx - 22, hy - 6), (hx - 6, hy - 1), 4)
    pygame.draw.line(surf, C_GOL_BEARD, (hx + 22, hy - 6), (hx + 6, hy - 1), 4)
    pygame.draw.circle(surf, C_WHITE, (hx - 14, hy + 3), 5)
    pygame.draw.circle(surf, C_WHITE, (hx + 14, hy + 3), 5)
    pygame.draw.circle(surf, (20, 20, 20), (hx - 13, hy + 4), 2)
    pygame.draw.circle(surf, (20, 20, 20), (hx + 13, hy + 4), 2)

    pygame.draw.arc(surf, C_GOL_HELM, pygame.Rect(hx - hr - 2, hy - hr - 8, (hr + 2) * 2, hr * 2), math.radians(35), math.radians(145), 8)

    glow = pygame.Surface((fh.w + 30, fh.h + 30), pygame.SRCALPHA)
    pygame.draw.circle(glow, (255, 235, 150, 70), (glow.get_width() // 2, glow.get_height() // 2), 22)
    surf.blit(glow, (fh.centerx - glow.get_width() // 2, fh.centery - glow.get_height() // 2), special_flags=pygame.BLEND_RGBA_ADD)
    pygame.draw.rect(surf, C_FOREHEAD, fh, border_radius=6)
    pygame.draw.rect(surf, C_FOREHEAD_GLOW, fh, width=2, border_radius=6)
    pygame.draw.line(surf, (200, 60, 50), (fh.centerx - 7, fh.centery), (fh.centerx + 7, fh.centery), 2)
    pygame.draw.line(surf, (200, 60, 50), (fh.centerx, fh.centery - 7), (fh.centerx, fh.centery + 7), 2)

    if flash > 0:
        ov = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        a = int(120 * flash)
        pygame.draw.rect(ov, (255, 255, 255, a), torso, border_radius=10)
        pygame.draw.circle(ov, (255, 255, 255, a), (hx, hy), hr)
        surf.blit(ov, (0, 0))

    bw, bh = 110, 12
    bx, by = gx - bw // 2, hy - hr - 30
    pygame.draw.rect(surf, (30, 30, 30), pygame.Rect(bx - 2, by - 2, bw + 4, bh + 4), border_radius=4)
    pygame.draw.rect(surf, (90, 30, 30), pygame.Rect(bx, by, bw, bh), border_radius=3)
    col = C_GREEN if health_frac > 0.5 else (C_GOLD if health_frac > 0.2 else C_RED)
    pygame.draw.rect(surf, col, pygame.Rect(bx, by, int(bw * clamp(health_frac, 0, 1)), bh), border_radius=3)


def draw_particles(surf, parts):
    for p in parts:
        a = clamp(p["life"] / p["max"], 0, 1)
        s = pygame.Surface((p["r"] * 2, p["r"] * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*p["color"], int(255 * a)), (p["r"], p["r"]), p["r"])
        surf.blit(s, (p["x"] - p["r"], p["y"] - p["r"]))


def spawn_burst(parts, x, y, color, n=16, speed=320):
    for _ in range(n):
        ang = random.uniform(0, math.tau)
        sp = random.uniform(speed * 0.3, speed)
        parts.append({"x": x, "y": y, "vx": math.cos(ang) * sp, "vy": math.sin(ang) * sp - 80,
                      "r": random.randint(2, 5), "color": color, "life": random.uniform(0.4, 0.8), "max": 0.8})


def draw_floats(surf, floats, font):
    for f in floats:
        a = clamp(f["life"] / 1.0, 0, 1)
        s = font.render(f["text"], True, f["color"])
        s.set_alpha(int(255 * a))
        surf.blit(s, s.get_rect(center=(int(f["x"]), int(f["y"]))))


def draw_hud(surf, font_t, font_s, aiming, power_frac):
    pygame.draw.rect(surf, C_HUD_BG, pygame.Rect(0, 0, SCREEN_W, 56))
    pygame.draw.line(surf, C_GOLD, (0, 56), (SCREEN_W, 56), 2)
    surf.blit(font_t.render("Sling Artillery", True, C_GOLD), (16, 12))

    msg = "Drag David back & release — aim for the glowing forehead!"
    surf.blit(font_s.render(msg, True, (190, 205, 220)), font_s.render(msg, True, (190, 205, 220)).get_rect(center=(SCREEN_W // 2 + 60, 28)))

    if aiming:
        bw, bh = 150, 12
        bx, by = SCREEN_W - bw - 16, 22
        pygame.draw.rect(surf, (40, 40, 50), pygame.Rect(bx, by, bw, bh), border_radius=5)
        col = (int(90 + 165 * power_frac), int(180 - 110 * power_frac), 70)
        pygame.draw.rect(surf, col, pygame.Rect(bx, by, int(bw * power_frac), bh), border_radius=5)
        surf.blit(font_s.render("POWER", True, C_WHITE), (bx, by - 16))


def draw_end_screen(surf, won, font_big, font_med, font_small, t):
    ov = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    ov.fill((0, 0, 0, 180))
    surf.blit(ov, (0, 0))
    glow = int(200 + 55 * math.sin(t * 2))
    gold = (glow, int(glow * 0.82), 60)

    if won:
        head = ("The Giant Falls!", gold)
        sub = "Your stone struck true and Goliath is defeated."
    else:
        head = ("Goliath Reached You", (220, 90, 70))
        sub = "The giant closed the distance before he fell."

    verse = [
        '"And David put his hand in his bag, and took thence a stone,',
        ' and slang it, and smote the Philistine in his forehead..."',
        "— 1 Samuel 17:49 (KJV)",
        "Press ESC/ENTER to return to the Portal and Record Score",
    ]

    y = SCREEN_H // 2 - 150
    s = font_big.render(head[0], True, head[1])
    surf.blit(s, s.get_rect(center=(SCREEN_W // 2, y))); y += font_big.get_height() + 8
    s = font_med.render(sub, True, C_WHITE)
    surf.blit(s, s.get_rect(center=(SCREEN_W // 2, y))); y += font_med.get_height() + 22
    for i, line in enumerate(verse):
        col = (150, 150, 150) if i == 3 else (200, 175, 120)
        s = font_small.render(line, True, col)
        surf.blit(s, s.get_rect(center=(SCREEN_W // 2, y)))
        y += font_small.get_height() + (12 if i == 2 else 4)

def _apply_body_hit(state, stone, knock):
    state["health"] = max(0.0, state["health"] - BODY_DAMAGE)
    state["flash"] = 1.0
    state["shake"] = max(state["shake"], 0.25)
    spawn_burst(state["particles"], stone["x"], stone["y"], (210, 200, 180), 12, 240)
    state["floats"].append({"x": stone["x"], "y": stone["y"] - 16, "text": "-10%", "color": (255, 200, 120), "life": 1.0})
    if knock:
        state["goliath_x"] += KNOCKBACK
    stone["vx"] = -abs(stone["vx"]) * 0.5 - 80
    stone["vy"] = -abs(stone["vy"]) * 0.3 - 120


# ═══════════════════════════════════════════════════════════════════════════
#  MAIN GAME WITH DYNAMIC CONFIG
# ═══════════════════════════════════════════════════════════════════════════
def run(skin_data=None, live_config=None):
    pygame.display.set_caption("Bible Quest — Sling Artillery")
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    clock = pygame.time.Clock()

    font_big   = load_font(50, bold=True)
    font_med   = load_font(22)
    font_hud   = load_font(22, bold=True)
    font_small = load_font(15)
    font_float = load_font(24, bold=True)

    # Process live rules
    current_gravity = float(live_config.get("gravity", 1350.0)) if live_config else 1350.0
    current_walk_speed = float(live_config.get("goliath_speed", 12.0)) if live_config else 12.0

    def new_game():
        return {
            "goliath_x": float(GOLIATH_START_X),
            "health": 1.0,
            "armed": True,
            "aiming": False,
            "pouch": SLING_ANCHOR,
            "stone": None,
            "flash": 0.0,
            "shake": 0.0,
            "walk_phase": 0.0,
            "particles": [],
            "floats": [],
            "result": None,
            "shots_fired": 0,
        }

    state = new_game()
    t = 0.0
    running = True

    while running:
        dt = min(clock.tick(60) / 1000.0, 0.05)
        t += dt

        mx, my = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE and state["result"] is None:
                    running = False
                if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_ESCAPE) and state["result"] is not None:
                    # Send Score Calculation to Leaderboard (Critical headshot + Speed vs Shots Fired)
                    score_calc = 0
                    if state["result"] == "win":
                        score_calc = max(1000, 10000 - (state["shots_fired"] * 500) - int(t * 10))
                    return score_calc

            if state["result"] is None:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if state["armed"] and state["stone"] is None:
                        if math.hypot(mx - SLING_ANCHOR[0], my - SLING_ANCHOR[1]) <= GRAB_RADIUS \
                           or math.hypot(mx - DAVID_X, my - (GROUND_Y - 60)) <= GRAB_RADIUS:
                            state["aiming"] = True

                if event.type == pygame.MOUSEBUTTONUP and event.button == 1 and state["aiming"]:
                    state["aiming"] = False
                    pdx, pdy = state["pouch"][0] - SLING_ANCHOR[0], state["pouch"][1] - SLING_ANCHOR[1]
                    pull = math.hypot(pdx, pdy)
                    if pull >= MIN_PULL:
                        vx = -pdx * POWER_SCALE
                        vy = -pdy * POWER_SCALE
                        state["stone"] = {
                            "x": float(SLING_ANCHOR[0]), "y": float(SLING_ANCHOR[1]),
                            "vx": vx, "vy": vy, "life": 0.0, "bounced": False,
                        }
                        state["armed"] = False
                        state["shots_fired"] += 1
                    state["pouch"] = SLING_ANCHOR

        power_frac = 0.0
        if state["aiming"]:
            pdx, pdy = mx - SLING_ANCHOR[0], my - SLING_ANCHOR[1]
            dist = math.hypot(pdx, pdy)
            if dist > MAX_PULL:
                k = MAX_PULL / dist
                pdx, pdy = pdx * k, pdy * k
            state["pouch"] = (SLING_ANCHOR[0] + pdx, SLING_ANCHOR[1] + pdy)
            power_frac = min(1.0, math.hypot(pdx, pdy) / MAX_PULL)

        if state["result"] is None:
            rage = 1.0 + (1.0 - state["health"]) * 0.6
            state["goliath_x"] -= current_walk_speed * rage * dt
            state["walk_phase"] += dt * 4.5
            if state["goliath_x"] <= DANGER_X:
                state["result"] = "lose"

        geom = goliath_geometry(int(state["goliath_x"]))

        if state["stone"] is not None and state["result"] is None:
            s = state["stone"]
            s["life"] += dt
            sub = dt / SUBSTEPS
            for _ in range(SUBSTEPS):
                s["vy"] += current_gravity * sub
                s["x"]  += s["vx"] * sub
                s["y"]  += s["vy"] * sub

                if circle_rect_collide(s["x"], s["y"], STONE_R, geom["forehead_rect"]):
                    state["result"] = "win"
                    state["health"] = 0.0
                    state["shake"] = 0.6
                    spawn_burst(state["particles"], s["x"], s["y"], (255, 230, 120), 28, 420)
                    state["floats"].append({"x": s["x"], "y": s["y"] - 20, "text": "CRITICAL!", "color": (255, 220, 90), "life": 1.2})
                    state["stone"] = None
                    break

                hcx, hcy = geom["head_center"]
                if math.hypot(s["x"] - hcx, s["y"] - hcy) < geom["head_r"] + STONE_R:
                    _apply_body_hit(state, s, knock=False)
                    break

                if circle_rect_collide(s["x"], s["y"], STONE_R, geom["torso_rect"]):
                    _apply_body_hit(state, s, knock=True)
                    break

                if s["y"] >= GROUND_Y - STONE_R:
                    s["y"] = GROUND_Y - STONE_R
                    s["vy"] = -s["vy"] * 0.42
                    s["vx"] *= 0.6
                    s["bounced"] = True
                    if abs(s["vy"]) < 60:
                        state["stone"] = None
                        state["armed"] = True
                        break

            if state["stone"] is not None:
                s = state["stone"]
                if s["x"] < -40 or s["x"] > SCREEN_W + 40 or s["life"] > 4.0:
                    state["stone"] = None
                    state["armed"] = True

        if state["result"] is None and state["health"] <= 0.0001:
            state["result"] = "win"
            state["shake"] = 0.5
            spawn_burst(state["particles"], *geom["head_center"], (255, 230, 120), 24, 380)

        for p in state["particles"]:
            p["vy"] += 600 * dt
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            p["life"] -= dt
        state["particles"] = [p for p in state["particles"] if p["life"] > 0]

        for f in state["floats"]:
            f["y"] -= 40 * dt
            f["life"] -= dt
        state["floats"] = [f for f in state["floats"] if f["life"] > 0]

        state["flash"] = max(0.0, state["flash"] - dt * 3)
        state["shake"] = max(0.0, state["shake"] - dt)

        world = pygame.Surface((SCREEN_W, SCREEN_H))
        draw_background(world, t)
        draw_goliath(world, geom, state["health"], state["flash"], state["walk_phase"], state["result"] == "win")

        pygame.draw.line(world, (200, 70, 60), (DANGER_X, GROUND_Y - 4), (DANGER_X, GROUND_Y - 70), 2)
        draw_david(world, SLING_ANCHOR, state["aiming"], t, skin_data)

        if state["aiming"]:
            pdx, pdy = state["pouch"][0] - SLING_ANCHOR[0], state["pouch"][1] - SLING_ANCHOR[1]
            vx, vy = -pdx * POWER_SCALE, -pdy * POWER_SCALE
            draw_trajectory(world, predict_trajectory(SLING_ANCHOR[0], SLING_ANCHOR[1], vx, vy, current_gravity))
            draw_sling(world, SLING_ANCHOR, state["pouch"], power_frac)

        if state["stone"] is not None:
            draw_stone(world, state["stone"]["x"], state["stone"]["y"])

        draw_particles(world, state["particles"])
        draw_floats(world, state["floats"], font_float)

        ox = oy = 0
        if state["shake"] > 0:
            amp = 10 * state["shake"]
            ox = random.uniform(-amp, amp); oy = random.uniform(-amp, amp)
        screen.fill((0, 0, 0))
        screen.blit(world, (ox, oy))

        draw_hud(screen, font_hud, font_small, state["aiming"], power_frac)
        if state["result"] is not None:
            draw_end_screen(screen, state["result"] == "win", font_big, font_med, font_small, t)

        pygame.display.flip()

    return 0


if __name__ == "__main__":
    pygame.init()
    pygame.font.init()
    run()
    pygame.quit()
    sys.exit()