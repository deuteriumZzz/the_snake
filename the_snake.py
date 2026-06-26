import json
import math
import os
import random
from datetime import date

import pygame

pygame.mixer.pre_init(22050, -16, 1, 512)
pygame.init()
pygame.font.init()

# ── Layout (portrait phone 400×720) ──────────────────────────────────────────
SCREEN_WIDTH    = 400
SCREEN_HEIGHT   = 400
HUD_HEIGHT      = 65
CONTROLS_HEIGHT = 255
WINDOW_HEIGHT   = HUD_HEIGHT + SCREEN_HEIGHT + CONTROLS_HEIGHT  # 720

GRID_SIZE   = 20
GRID_WIDTH  = SCREEN_WIDTH  // GRID_SIZE
GRID_HEIGHT = SCREEN_HEIGHT // GRID_SIZE

GAME_AREA = pygame.Rect(0, HUD_HEIGHT, SCREEN_WIDTH, SCREEN_HEIGHT)

# ── Directions ────────────────────────────────────────────────────────────────
UP    = (0, -1)
DOWN  = (0,  1)
LEFT  = (-1, 0)
RIGHT = (1,  0)

# ── Color palette ─────────────────────────────────────────────────────────────
BG_COLOR    = (12, 12, 20)
GRID_COLOR  = (20, 20, 34)
HUD_BG      = (8, 8, 18)
HUD_BORDER  = (0, 210, 175)

SNAKE_HEAD_COLOR   = (190, 255, 190)
SNAKE_BODY_COLOR   = (55, 210, 55)
SNAKE_BORDER_COLOR = (18, 110, 18)
SNAKE_GLOW_COLOR   = (12, 52, 12)

APPLE_COLOR = (255, 62, 50)
APPLE_SHINE = (255, 190, 180)
APPLE_GLOW  = (150, 25, 20)

WHITE      = (255, 255, 255)
GRAY       = (120, 120, 140)
LIGHT_GRAY = (185, 185, 205)
ACCENT     = (0, 220, 175)
ACCENT2    = (0, 180, 255)
YELLOW     = (255, 220, 0)
GOLD       = (255, 185, 0)
RED        = (225, 50, 50)
DARK_RED   = (85, 6, 6)
PANEL_BG   = (18, 18, 34)
PANEL_DARK = (11, 11, 22)
SEL_BG     = (0, 72, 58)
BTN_BG     = (22, 22, 42)
BTN_ACT    = (0, 60, 48)

# ── Compat aliases (kept for existing tests) ──────────────────────────────────
BOARD_BACKGROUND_COLOR = BG_COLOR
BORDER_COLOR           = HUD_BORDER
SNAKE_COLOR            = SNAKE_BODY_COLOR
SPEED                  = 8

# ── Difficulty ────────────────────────────────────────────────────────────────
DIFFICULTIES = ["Лёгкий", "Нормальный", "Сложный"]
DIFFICULTY_CFG = {
    "Лёгкий":     {"base_speed": 6,  "increment": 0},
    "Нормальный":  {"base_speed": 8,  "increment": 1},
    "Сложный":    {"base_speed": 12, "increment": 2},
}
DIFFICULTY_DESC = {
    "Лёгкий":     "Без ускорения — идеально для старта",
    "Нормальный":  "Скорость растёт каждые 5 очков",
    "Сложный":    "Быстрый старт и резкое ускорение",
}

MAX_RECORDS      = 5
POINTS_PER_LEVEL = 5

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gamedata.json")

# ── Game states ───────────────────────────────────────────────────────────────
MAIN_MENU = "main_menu"
SETTINGS  = "settings"
RECORDS   = "records"
PLAYING   = "playing"
PAUSED    = "paused"
GAME_OVER = "game_over"

MENU_ITEMS = ["ИГРАТЬ", "НАСТРОЙКИ", "РЕКОРДЫ", "ВЫХОД"]

# ── D-pad geometry ────────────────────────────────────────────────────────────
_BS  = 70
_CX  = SCREEN_WIDTH // 2
_CY  = HUD_HEIGHT + SCREEN_HEIGHT + 128

BTN_UP    = pygame.Rect(_CX - _BS // 2, _CY - 84 - _BS // 2, _BS, _BS)
BTN_DOWN  = pygame.Rect(_CX - _BS // 2, _CY + 84 - _BS // 2, _BS, _BS)
BTN_LEFT  = pygame.Rect(_CX - 84 - _BS // 2, _CY - _BS // 2, _BS, _BS)
BTN_RIGHT = pygame.Rect(_CX + 84 - _BS // 2, _CY - _BS // 2, _BS, _BS)
BTN_PAUSE = pygame.Rect(SCREEN_WIDTH - 50, 13, 36, 36)

# ── Menu geometry ─────────────────────────────────────────────────────────────
_MENU_ITEM_H   = 68
_MENU_ITEM_GAP = 12
_MENU_PANEL    = pygame.Rect(28, 202, 344, 344)


def _menu_item_rect(i):
    return pygame.Rect(
        _MENU_PANEL.x + 10,
        _MENU_PANEL.y + 14 + i * (_MENU_ITEM_H + _MENU_ITEM_GAP),
        _MENU_PANEL.width - 20,
        _MENU_ITEM_H,
    )


# ── Settings geometry ─────────────────────────────────────────────────────────
_SETT_PANEL  = pygame.Rect(24, 152, 352, 388)
_SETT_DIFF_Y = 278
_SETT_SND_Y  = 392
_ARR_W, _ARR_H = 38, 42


def _sett_left_rect(cy):
    return pygame.Rect(_SETT_PANEL.x + 12, cy - _ARR_H // 2, _ARR_W, _ARR_H)


def _sett_right_rect(cy):
    return pygame.Rect(_SETT_PANEL.right - 12 - _ARR_W, cy - _ARR_H // 2, _ARR_W, _ARR_H)


# ── Background star positions (x, y, freq, phase) ────────────────────────────
_STARS = [
    (48, 78, 0.0028, 0.0), (318, 42, 0.0038, 1.5), (275, 188, 0.0022, 0.8),
    (68, 248, 0.0048, 2.1), (348, 318, 0.0031, 1.2), (118, 178, 0.0042, 3.1),
    (378, 148, 0.0024, 0.3), (28, 398, 0.0052, 1.8), (228, 508, 0.0033, 2.5),
    (378, 478, 0.0041, 0.7), (148, 618, 0.0025, 1.1), (58, 558, 0.0048, 2.8),
    (195, 148, 0.0030, 0.4), (98, 348, 0.0058, 1.7), (335, 228, 0.0020, 3.5),
    (22, 168, 0.0044, 2.2), (358, 698, 0.0036, 0.9),
]

# ── Pygame window ─────────────────────────────────────────────────────────────
screen = pygame.display.set_mode((SCREEN_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Змейка")
clock = pygame.time.Clock()

_game_surf = pygame.Surface((SCREEN_WIDTH, WINDOW_HEIGHT))
_fade_surf = pygame.Surface((SCREEN_WIDTH, WINDOW_HEIGHT))
_fade_surf.fill((0, 0, 0))

# Pre-computed CRT scanlines overlay (horizontal lines every 3px, alpha 22)
_crt = pygame.Surface((SCREEN_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
for _y in range(0, WINDOW_HEIGHT, 3):
    pygame.draw.line(_crt, (0, 0, 0, 22), (0, _y), (SCREEN_WIDTH, _y))

# ── Fonts ─────────────────────────────────────────────────────────────────────
_FONT_DIR    = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "fonts")
_RUSSO       = os.path.join(_FONT_DIR, "RussoOne.ttf")
_PRESS_START = os.path.join(_FONT_DIR, "PressStart2P.ttf")


def _font(path, size):
    """Загрузить шрифт TTF с запасным вариантом Arial."""
    try:
        return pygame.font.Font(path, size)
    except (FileNotFoundError, pygame.error):
        return pygame.font.SysFont("Arial", size, bold=True)


# Russo One — all Russian/display text (supports Cyrillic)
FONT_TITLE = _font(_RUSSO, 46)
FONT_BIG   = _font(_RUSSO, 28)
FONT_MED   = _font(_RUSSO, 21)
FONT_SMALL = _font(_RUSSO, 15)
FONT_TINY  = _font(_RUSSO, 11)

# Press Start 2P — numbers and ASCII labels (Latin only, retro pixel style)
FONT_RETRO    = _font(_PRESS_START, 16)
FONT_RETRO_SM = _font(_PRESS_START, 10)
FONT_RETRO_XS = _font(_PRESS_START, 8)

# Alias kept for any existing tests that import FONT_HUD
FONT_HUD = FONT_RETRO_SM


# ── Sounds ────────────────────────────────────────────────────────────────────

def _make_tone(freq, ms, vol=0.22):
    sr, n = 22050, int(22050 * ms / 1000)
    fade = max(1, int(sr * 0.003))
    buf = bytearray(n * 2)
    for i in range(n):
        env = min(1.0, min(i, n - i) / fade)
        v = int(32767 * vol * env * math.sin(2 * math.pi * freq * i / sr))
        v = max(-32768, min(32767, v))
        buf[2 * i] = v & 0xFF
        buf[2 * i + 1] = (v >> 8) & 0xFF
    return pygame.mixer.Sound(buffer=bytes(buf))


try:
    SND_EAT   = _make_tone(880, 80)
    SND_DIE   = _make_tone(180, 380, 0.28)
    SND_CLICK = _make_tone(660, 45, 0.14)
    SND_LEVEL = _make_tone(1046, 120, 0.18)
except Exception:
    SND_EAT = SND_DIE = SND_CLICK = SND_LEVEL = None


def _play(snd, enabled):
    if enabled and snd:
        snd.play()


# ── Data persistence ──────────────────────────────────────────────────────────

def _default_data():
    return {"difficulty": "Нормальный", "sound": True, "high_score": 0, "scores": []}


def load_data():
    try:
        with open(DATA_FILE, encoding="utf-8") as f:
            raw = json.load(f)
        data = _default_data()
        data.update({k: raw[k] for k in data if k in raw})
        if not isinstance(data["scores"], list):
            data["scores"] = []
        return data
    except (FileNotFoundError, json.JSONDecodeError):
        return _default_data()


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def add_score(data, score):
    today = date.today().strftime("%d.%m.%Y")
    data["scores"].append({"score": score, "date": today})
    data["scores"].sort(key=lambda r: r["score"], reverse=True)
    data["scores"] = data["scores"][:MAX_RECORDS]
    if score > data["high_score"]:
        data["high_score"] = score
        return True
    return False


# ── Visual effect classes ─────────────────────────────────────────────────────

class Particle:
    """Одна частица для эффекта взрыва."""

    _COLORS = [APPLE_COLOR, YELLOW, GOLD, (255, 120, 60), WHITE, ACCENT]

    def __init__(self, x, y, color=None):
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(1.5, 5.5)
        self.x, self.y = float(x), float(y)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.life  = 1.0
        self.decay = random.uniform(0.045, 0.10)
        self.r     = random.randint(3, 7)
        self.color = color or random.choice(self._COLORS)

    def update(self):
        self.x  += self.vx
        self.y  += self.vy
        self.vx *= 0.90
        self.vy *= 0.90
        self.life -= self.decay
        return self.life > 0

    def draw(self, surface):
        c = tuple(int(v * self.life) for v in self.color)
        pygame.draw.circle(surface, c,
                           (int(self.x), int(self.y)),
                           max(1, int(self.r * self.life)))


class FloatingText:
    """Всплывающий текст очков, который поднимается и исчезает."""

    def __init__(self, text, x, y, color=YELLOW):
        self.surf  = FONT_RETRO.render(text, True, color)
        self.x     = float(x - self.surf.get_width() // 2)
        self.y     = float(y)
        self.vy    = -1.4
        self.life  = 1.0
        self.decay = 0.030

    def update(self):
        self.y    += self.vy
        self.life -= self.decay
        return self.life > 0

    def draw(self, surface):
        s = self.surf.copy()
        s.set_alpha(int(255 * max(0.0, self.life)))
        surface.blit(s, (int(self.x), int(self.y)))


class LevelBanner:
    """Уведомление о новом уровне, которое постепенно исчезает."""

    def __init__(self, level):
        self.surf  = FONT_BIG.render(f"УРОВЕНЬ  {level}", True, YELLOW)
        self.life  = 1.0
        self.decay = 0.016

    def update(self):
        self.life -= self.decay
        return self.life > 0

    def draw(self, surface):
        s = self.surf.copy()
        s.set_alpha(int(255 * min(1.0, self.life * 3)))
        cy = HUD_HEIGHT + SCREEN_HEIGHT // 2
        surface.blit(s, (_CX - s.get_width() // 2, cy - s.get_height() // 2))


# ── Drawing helpers ───────────────────────────────────────────────────────────

def _draw_grid(surface):
    for x in range(0, SCREEN_WIDTH, GRID_SIZE):
        pygame.draw.line(surface, GRID_COLOR, (x, HUD_HEIGHT),
                         (x, HUD_HEIGHT + SCREEN_HEIGHT))
    for y in range(HUD_HEIGHT, HUD_HEIGHT + SCREEN_HEIGHT + GRID_SIZE, GRID_SIZE):
        pygame.draw.line(surface, GRID_COLOR, (0, y), (SCREEN_WIDTH, y))


def _draw_bg_grid(surface):
    for x in range(0, SCREEN_WIDTH, GRID_SIZE):
        pygame.draw.line(surface, GRID_COLOR, (x, 0), (x, WINDOW_HEIGHT))
    for y in range(0, WINDOW_HEIGHT, GRID_SIZE):
        pygame.draw.line(surface, GRID_COLOR, (0, y), (SCREEN_WIDTH, y))


def _retro_panel(surface, rect, bg=PANEL_BG, border=HUD_BORDER, notch=12):
    """Панель с пиксельными срезанными углами в стиле ретро."""
    x, y, w, h = rect.x, rect.y, rect.width, rect.height
    pts = [
        (x + notch, y),     (x + w - notch, y),
        (x + w, y + notch), (x + w, y + h - notch),
        (x + w - notch, y + h), (x + notch, y + h),
        (x, y + h - notch), (x, y + notch),
    ]
    pygame.draw.polygon(surface, bg, pts)
    pygame.draw.polygon(surface, border, pts, 2)


def _retro_divider(surface, x1, y, x2, color=HUD_BORDER):
    """Горизонтальный разделитель с прямоугольными заглушками на концах."""
    pygame.draw.line(surface, color, (x1, y), (x2, y), 1)
    for ex in (x1, x2):
        pygame.draw.rect(surface, color, pygame.Rect(ex - 3, y - 2, 6, 4))


def _overlay(surface, alpha=155):
    s = pygame.Surface((SCREEN_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    s.fill((0, 0, 0, alpha))
    surface.blit(s, (0, 0))


def _blit_cx(surface, surf, y):
    surface.blit(surf, (_CX - surf.get_width() // 2, y))


def _draw_stars(surface, ticks):
    """Мерцающие пиксельные звёзды на фоне меню."""
    for sx, sy, freq, phase in _STARS:
        brightness = 0.35 + 0.65 * ((math.sin(ticks * freq + phase) + 1) / 2)
        c = tuple(int(v * brightness) for v in ACCENT)
        pygame.draw.rect(surface, c, pygame.Rect(sx - 1, sy - 1, 2, 2))


def _draw_logo_snake(surface, cx, y):
    """Декоративная змейка в шапке экрана главного меню."""
    s = GRID_SIZE - 2
    segs = [(cx + (i - 3) * GRID_SIZE, y) for i in range(7)]
    for i, (px, py) in enumerate(segs):
        fade  = max(0.45, 1.0 - i / (len(segs) + 2))
        color = SNAKE_HEAD_COLOR if i == 0 else tuple(
            int(c * fade) for c in SNAKE_BODY_COLOR
        )
        pygame.draw.rect(surface, color, pygame.Rect(px, py, s, s), border_radius=3)
        if i == 0:
            pygame.draw.circle(surface, (10, 10, 10), (px + s - 4, py + 4), 2)
            pygame.draw.circle(surface, (10, 10, 10), (px + s - 4, py + s - 5), 2)


# ── Screen renderers ──────────────────────────────────────────────────────────

def draw_main_menu(surface, selected, ticks):
    surface.fill(BG_COLOR)
    _draw_bg_grid(surface)
    _draw_stars(surface, ticks)

    _draw_logo_snake(surface, _CX, 32)

    # Title with drop-shadow
    shadow = FONT_TITLE.render("ЗМЕЙКА", True, (0, 60, 48))
    title  = FONT_TITLE.render("ЗМЕЙКА", True, ACCENT)
    _blit_cx(surface, shadow, 70)
    _blit_cx(surface, title,  67)

    _retro_divider(surface, _CX - 115, 132, _CX + 115)
    sub = FONT_SMALL.render("Классическая игра — Python + Pygame", True, GRAY)
    _blit_cx(surface, sub, 140)

    _retro_panel(surface, _MENU_PANEL, bg=PANEL_DARK)

    pulse = 0.70 + 0.30 * math.sin(ticks * 0.003)

    for i, label in enumerate(MENU_ITEMS):
        ir = _menu_item_rect(i)
        if i == selected:
            sel_c = tuple(int(c * pulse) for c in SEL_BG)
            _retro_panel(surface, ir, bg=sel_c, border=HUD_BORDER, notch=6)
            arrow = FONT_MED.render("►", True, ACCENT)
            surface.blit(arrow, (ir.x + 12,
                                  ir.y + ir.h // 2 - arrow.get_height() // 2))
            txt_color = WHITE
        else:
            txt_color = GRAY

        txt = FONT_MED.render(label, True, txt_color)
        surface.blit(txt, (ir.x + 48, ir.y + ir.h // 2 - txt.get_height() // 2))

    hint = FONT_RETRO_XS.render("UP/DOWN  ENTER", True, GRAY)
    _blit_cx(surface, hint, _MENU_PANEL.bottom + 20)


def draw_settings(surface, diff_i, snd_on, sett_row):
    surface.fill(BG_COLOR)
    _draw_bg_grid(surface)

    _retro_panel(surface, _SETT_PANEL)
    title = FONT_BIG.render("НАСТРОЙКИ", True, ACCENT)
    _blit_cx(surface, title, _SETT_PANEL.y + 14)
    _retro_divider(surface, _CX - 140, _SETT_PANEL.y + 56, _CX + 140)

    def _row(label, value, cy, active):
        lbl = FONT_SMALL.render(label, True, ACCENT if active else GRAY)
        _blit_cx(surface, lbl, cy - 38)
        for r, sym in ((_sett_left_rect(cy), "◄"), (_sett_right_rect(cy), "►")):
            bc = ACCENT if active else GRAY
            bg = BTN_ACT if active else BTN_BG
            _retro_panel(surface, r, bg=bg, border=bc, notch=4)
            s = FONT_MED.render(sym, True, bc)
            surface.blit(s, (r.x + r.w // 2 - s.get_width() // 2,
                              r.y + r.h // 2 - s.get_height() // 2))
        val = FONT_MED.render(value, True, WHITE if active else LIGHT_GRAY)
        _blit_cx(surface, val, cy - val.get_height() // 2)

    _row("Сложность", DIFFICULTIES[diff_i], _SETT_DIFF_Y, sett_row == 0)
    desc = FONT_TINY.render(DIFFICULTY_DESC[DIFFICULTIES[diff_i]], True, GRAY)
    _blit_cx(surface, desc, _SETT_DIFF_Y + 28)
    _row("Звук", "Вкл" if snd_on else "Выкл", _SETT_SND_Y, sett_row == 1)

    _retro_divider(surface, _CX - 140, _SETT_PANEL.bottom - 52, _CX + 140)
    hint = FONT_RETRO_XS.render("UP/DN ROW  LFT/RGT CHANGE  ENTER SAVE", True, GRAY)
    _blit_cx(surface, hint, _SETT_PANEL.bottom - 38)


def draw_records(surface, scores):
    surface.fill(BG_COLOR)
    _draw_bg_grid(surface)

    panel = pygame.Rect(24, 138, 352, 408)
    _retro_panel(surface, panel)
    title = FONT_BIG.render("РЕКОРДЫ", True, ACCENT)
    _blit_cx(surface, title, panel.y + 14)
    _retro_divider(surface, _CX - 140, panel.y + 56, _CX + 140)

    row_h = 54
    medal_colors = [GOLD, LIGHT_GRAY, (180, 110, 50)]

    for i in range(MAX_RECORDS):
        ry = panel.y + 68 + i * row_h
        rr = pygame.Rect(panel.x + 10, ry, panel.width - 20, row_h - 4)

        if i < len(scores):
            entry = scores[i]
            if i == 0:
                _retro_panel(surface, rr, bg=(40, 32, 0), border=GOLD, notch=6)
            elif i == 1:
                _retro_panel(surface, rr, bg=(28, 28, 36), border=LIGHT_GRAY, notch=6)

            mc  = medal_colors[i] if i < 3 else GRAY
            num = FONT_SMALL.render(f"#{i + 1}", True, mc)
            sc  = FONT_RETRO.render(str(entry["score"]).zfill(4), True,
                                     GOLD if i == 0 else WHITE)
            dt  = FONT_RETRO_XS.render(entry["date"], True, GRAY)
            surface.blit(num, (rr.x + 10, ry + 14))
            surface.blit(sc,  (rr.x + 56, ry + 10))
            surface.blit(dt,  (rr.right - dt.get_width() - 10, ry + 20))
        else:
            surface.blit(FONT_SMALL.render(f"#{i + 1}", True, (50, 50, 68)),
                         (rr.x + 10, ry + 14))
            surface.blit(FONT_RETRO_XS.render("----", True, (50, 50, 68)),
                         (rr.x + 56, ry + 20))

    _retro_divider(surface, _CX - 140, panel.bottom - 46, _CX + 140)
    _blit_cx(surface, FONT_RETRO_XS.render("ESC  BACK", True, GRAY),
             panel.bottom - 32)


def draw_hud(surface, score, high_score, level):
    """Двухстрочный HUD: метка Russo One над числом Press Start 2P."""
    pygame.draw.rect(surface, HUD_BG, (0, 0, SCREEN_WIDTH, HUD_HEIGHT))
    pygame.draw.line(surface, HUD_BORDER, (0, HUD_HEIGHT - 2),
                     (SCREEN_WIDTH, HUD_HEIGHT - 2), 2)
    pygame.draw.line(surface, (0, 80, 65), (0, HUD_HEIGHT - 5),
                     (SCREEN_WIDTH, HUD_HEIGHT - 5), 1)

    lbl_y = 9
    num_y = 27

    # Score — left column
    surface.blit(FONT_TINY.render("СЧЁТ", True, GRAY), (14, lbl_y))
    surface.blit(FONT_RETRO.render(str(score).zfill(4), True, WHITE), (14, num_y))

    # Level — center column
    lv_lbl = FONT_TINY.render("УРОВЕНЬ", True, GRAY)
    lv_num = FONT_RETRO.render(str(level), True, ACCENT)
    _blit_cx(surface, lv_lbl, lbl_y)
    _blit_cx(surface, lv_num, num_y)

    # High score — right column (left of pause button)
    hs_num = FONT_RETRO.render(str(high_score).zfill(4), True, GOLD)
    hs_lbl = FONT_TINY.render("РЕКОРД", True, GRAY)
    hs_x   = BTN_PAUSE.x - hs_num.get_width() - 12
    surface.blit(hs_lbl, (hs_x, lbl_y))
    surface.blit(hs_num, (hs_x, num_y))

    # Pause button
    _retro_panel(surface, BTN_PAUSE, bg=PANEL_BG, border=HUD_BORDER, notch=5)
    sym = FONT_SMALL.render("||", True, WHITE)
    surface.blit(sym, (BTN_PAUSE.x + BTN_PAUSE.w // 2 - sym.get_width() // 2,
                        BTN_PAUSE.y + BTN_PAUSE.h // 2 - sym.get_height() // 2))


def draw_dpad(surface, active_dir):
    """Панель управления D-pad под игровым полем."""
    bar = pygame.Rect(0, HUD_HEIGHT + SCREEN_HEIGHT, SCREEN_WIDTH, CONTROLS_HEIGHT)
    pygame.draw.rect(surface, HUD_BG, bar)
    pygame.draw.line(surface, HUD_BORDER, (0, bar.y), (SCREEN_WIDTH, bar.y), 2)
    pygame.draw.line(surface, (0, 80, 65), (0, bar.y + 3), (SCREEN_WIDTH, bar.y + 3), 1)

    hint = FONT_RETRO_XS.render("SWIPE OR BUTTONS", True, GRAY)
    _blit_cx(surface, hint, bar.y + 10)

    for btn, sym, d in (
        (BTN_UP,    "▲", UP),
        (BTN_DOWN,  "▼", DOWN),
        (BTN_LEFT,  "◀", LEFT),
        (BTN_RIGHT, "▶", RIGHT),
    ):
        active = active_dir == d
        bg     = BTN_ACT if active else BTN_BG
        border = ACCENT  if active else HUD_BORDER
        _retro_panel(surface, btn, bg=bg, border=border, notch=10)
        s = FONT_BIG.render(sym, True, ACCENT if active else LIGHT_GRAY)
        surface.blit(s, (btn.x + btn.w // 2 - s.get_width() // 2,
                          btn.y + btn.h // 2 - s.get_height() // 2))

    cr = pygame.Rect(_CX - 12, _CY - 12, 24, 24)
    _retro_panel(surface, cr, bg=BTN_BG, border=GRAY, notch=5)


def draw_pause_screen(surface):
    _overlay(surface, 120)
    cx, cy = _CX, WINDOW_HEIGHT // 2
    panel  = pygame.Rect(cx - 150, cy - 76, 300, 152)
    _retro_panel(surface, panel)
    _blit_cx(surface, FONT_BIG.render("ПАУЗА", True, ACCENT), cy - 54)
    _retro_divider(surface, cx - 110, cy - 8, cx + 110)
    _blit_cx(surface,
             FONT_SMALL.render("P / ESC / || — продолжить", True, GRAY),
             cy + 10)


def draw_game_over_screen(surface, score, high_score, new_record):
    _overlay(surface, 165)
    cx, cy = _CX, WINDOW_HEIGHT // 2

    panel = pygame.Rect(cx - 182, cy - 148, 364, 305)
    _retro_panel(surface, panel, border=RED)

    _blit_cx(surface, FONT_BIG.render("ИГРА ОКОНЧЕНА", True, RED), cy - 130)
    _retro_divider(surface, cx - 145, cy - 84, cx + 145, color=RED)

    row = cy - 64
    if new_record:
        _blit_cx(surface, FONT_MED.render("★  НОВЫЙ РЕКОРД!", True, GOLD), row)
        row += 40

    _blit_cx(surface, FONT_MED.render("СЧЁТ:", True, GRAY), row)
    _blit_cx(surface,
             FONT_RETRO.render(str(score).zfill(4), True, WHITE),
             row + 30)
    _blit_cx(surface,
             FONT_SMALL.render(f"РЕКОРД:  {str(high_score).zfill(4)}", True, GOLD),
             row + 62)

    _retro_divider(surface, cx - 145, cy + 88, cx + 145)
    _blit_cx(surface,
             FONT_RETRO_XS.render("ENTER NEW GAME    ESC MENU", True, GRAY),
             cy + 100)


# ── Game objects ──────────────────────────────────────────────────────────────

class GameObject:
    """Базовый класс для всех игровых объектов."""

    def __init__(self, bg_color=None):
        """Инициализировать общие атрибуты."""
        self.body_color = bg_color
        self.position   = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)

    def draw(self, surface):
        """Отрисовать объект на поверхности *surface*."""
        pass


class Apple(GameObject):
    """Собираемое яблоко с анимацией пульсации."""

    def __init__(self, bg_color=APPLE_COLOR):
        """Инициализировать яблоко и разместить его на поле."""
        super().__init__(bg_color)
        self.randomize_position([])

    def randomize_position(self, snake_positions):
        """Выбрать случайную клетку, не занятую змейкой (*snake_positions*)."""
        while True:
            p = (
                random.randint(0, GRID_WIDTH  - 1) * GRID_SIZE,
                random.randint(0, GRID_HEIGHT - 1) * GRID_SIZE,
            )
            if p not in snake_positions:
                self.position = p
                break

    def draw(self, surface):
        """Отрисовать яблоко с пульсацией, свечением и бликом."""
        t     = pygame.time.get_ticks()
        pulse = 0.88 + 0.12 * math.sin(t * 0.004)
        sz    = int(GRID_SIZE * pulse)
        off   = (GRID_SIZE - sz) // 2
        x, y  = self.position
        dy    = y + HUD_HEIGHT

        glow = pygame.Rect(x - 2, dy - 2, GRID_SIZE + 4, GRID_SIZE + 4)
        pygame.draw.rect(surface, APPLE_GLOW, glow, border_radius=8)

        rect = pygame.Rect(x + off, dy + off, sz, sz)
        pygame.draw.rect(surface, self.body_color, rect,
                         border_radius=max(3, int(6 * pulse)))

        pygame.draw.rect(surface, APPLE_SHINE,
                         pygame.Rect(x + off + 4, dy + off + 3, 5, 4),
                         border_radius=2)


class Snake(GameObject):
    """Змейка под управлением игрока со светящейся головой и градиентным телом."""

    def __init__(self, bg_color=SNAKE_BODY_COLOR):
        """Инициализировать змейку в центре экрана, направление — вправо."""
        super().__init__(bg_color)
        self.length         = 1
        self.direction      = RIGHT
        self.next_direction = None
        self.positions      = [(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)]

    def update_direction(self, event):
        """Поставить в очередь смену направления по нажатию клавиши (стрелки + WASD)."""
        k = event.key
        if k in (pygame.K_UP, pygame.K_w) and self.direction != DOWN:
            self.next_direction = UP
        elif k in (pygame.K_DOWN, pygame.K_s) and self.direction != UP:
            self.next_direction = DOWN
        elif k in (pygame.K_LEFT, pygame.K_a) and self.direction != RIGHT:
            self.next_direction = LEFT
        elif k in (pygame.K_RIGHT, pygame.K_d) and self.direction != LEFT:
            self.next_direction = RIGHT

    def move(self):
        """Переместить змейку на одну клетку вперёд."""
        if self.next_direction:
            self.direction      = self.next_direction
            self.next_direction = None
        dx, dy = self.direction
        hx, hy = self.get_head_position()
        self.positions.insert(0, (
            (hx + dx * GRID_SIZE) % SCREEN_WIDTH,
            (hy + dy * GRID_SIZE) % SCREEN_HEIGHT,
        ))
        if len(self.positions) > self.length:
            self.positions.pop()

    def draw(self, surface):
        """Отрисовать змейку с градиентным телом и светящейся головой."""
        total = len(self.positions)
        for i, (x, y) in enumerate(self.positions):
            dy   = y + HUD_HEIGHT
            rect = pygame.Rect(x, dy, GRID_SIZE, GRID_SIZE)
            if i == 0:
                hcx = x + GRID_SIZE // 2
                hcy = dy + GRID_SIZE // 2
                pygame.draw.circle(surface, SNAKE_GLOW_COLOR, (hcx, hcy), GRID_SIZE)
                pygame.draw.circle(surface, (18, 72, 18), (hcx, hcy), GRID_SIZE - 4)
                pygame.draw.rect(surface, SNAKE_HEAD_COLOR, rect, border_radius=5)
                pygame.draw.rect(surface, SNAKE_BORDER_COLOR, rect, 1, border_radius=5)
                self._draw_eyes(surface, x, dy)
            else:
                fade  = max(0.40, 1.0 - i / (total + 2))
                color = tuple(int(c * fade) for c in SNAKE_BODY_COLOR)
                pygame.draw.rect(surface, color, rect, border_radius=3)
                pygame.draw.rect(surface, SNAKE_BORDER_COLOR, rect, 1, border_radius=3)

    def _draw_eyes(self, surface, x, y):
        dx, dy = self.direction
        s = GRID_SIZE
        if dx == 1:
            p1, p2 = (x + s - 5, y + 5), (x + s - 5, y + 12)
        elif dx == -1:
            p1, p2 = (x + 4, y + 5), (x + 4, y + 12)
        elif dy == -1:
            p1, p2 = (x + 5, y + 4), (x + 12, y + 4)
        else:
            p1, p2 = (x + 5, y + s - 5), (x + 12, y + s - 5)
        for p in (p1, p2):
            pygame.draw.circle(surface, (10, 10, 10), p, 3)
            pygame.draw.circle(surface, WHITE, (p[0] - 1, p[1] - 1), 1)

    def get_head_position(self):
        """Вернуть пиксельную позицию головы змейки."""
        return self.positions[0]

    def self_collision(self):
        """Вернуть True, если голова пересекается с любым сегментом тела."""
        return self.get_head_position() in self.positions[1:]

    def reset(self):
        """Сбросить змейку до начального состояния из одной клетки."""
        self.length         = 1
        self.direction      = RIGHT
        self.next_direction = None
        self.positions      = [(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)]


def handle_keys(snake):
    """Обработать события; вернуть False при выходе пользователя."""
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return False
        elif event.type == pygame.KEYDOWN:
            snake.update_direction(event)
    return True


# ── Helpers ───────────────────────────────────────────────────────────────────

def _change_direction(snake, new_dir):
    opp = {UP: DOWN, DOWN: UP, LEFT: RIGHT, RIGHT: LEFT}
    if new_dir != opp.get(snake.direction):
        snake.next_direction = new_dir


def _new_game(data):
    cfg = DIFFICULTY_CFG[data["difficulty"]]
    return Snake(), Apple(), 0, 1, cfg["base_speed"]


def _spawn_eat_fx(particles, float_texts, apple_pos, score):
    gx = apple_pos[0] + GRID_SIZE // 2
    gy = apple_pos[1] + HUD_HEIGHT + GRID_SIZE // 2
    for _ in range(12):
        particles.append(Particle(gx, gy))
    float_texts.append(FloatingText(f"+{score}", gx, gy - 16))


def _spawn_death_fx(particles, snake_positions):
    hx, hy = snake_positions[0]
    cx = hx + GRID_SIZE // 2
    cy = hy + HUD_HEIGHT + GRID_SIZE // 2
    for _ in range(20):
        particles.append(Particle(cx, cy, color=RED))


# ── Main loop ─────────────────────────────────────────────────────────────────

def main():
    """Инициализировать и запустить основной игровой цикл."""
    data = load_data()
    snake, apple, score, level, speed = _new_game(data)
    new_record   = False
    flash_frames = 0

    state    = MAIN_MENU
    menu_sel = 0
    diff_i   = DIFFICULTIES.index(data.get("difficulty", "Нормальный"))
    snd_on   = data.get("sound", True)
    sett_row = 0

    swipe_start  = None
    active_dir   = None
    particles    = []
    float_texts  = []
    level_banner = None
    shake        = 0
    fade_alpha   = 220
    prev_state   = None

    while True:
        ticks = pygame.time.get_ticks()

        if state != prev_state:
            fade_alpha = 220
            prev_state = state

        # ── Events ───────────────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_data(data)
                pygame.quit()
                return

            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = event.pos

                if state == MAIN_MENU:
                    for i in range(len(MENU_ITEMS)):
                        if _menu_item_rect(i).collidepoint(pos):
                            menu_sel = i
                            _play(SND_CLICK, snd_on)

                elif state == SETTINGS:
                    for cy_row, row_i in ((_SETT_DIFF_Y, 0), (_SETT_SND_Y, 1)):
                        if _sett_left_rect(cy_row).collidepoint(pos):
                            sett_row = row_i
                            if row_i == 0:
                                diff_i = (diff_i - 1) % len(DIFFICULTIES)
                            else:
                                snd_on = not snd_on
                            _play(SND_CLICK, snd_on)
                        elif _sett_right_rect(cy_row).collidepoint(pos):
                            sett_row = row_i
                            if row_i == 0:
                                diff_i = (diff_i + 1) % len(DIFFICULTIES)
                            else:
                                snd_on = not snd_on
                            _play(SND_CLICK, snd_on)

                elif state == PLAYING:
                    if BTN_PAUSE.collidepoint(pos):
                        state = PAUSED
                        _play(SND_CLICK, snd_on)
                    elif BTN_UP.collidepoint(pos):
                        _change_direction(snake, UP)
                        active_dir = UP
                    elif BTN_DOWN.collidepoint(pos):
                        _change_direction(snake, DOWN)
                        active_dir = DOWN
                    elif BTN_LEFT.collidepoint(pos):
                        _change_direction(snake, LEFT)
                        active_dir = LEFT
                    elif BTN_RIGHT.collidepoint(pos):
                        _change_direction(snake, RIGHT)
                        active_dir = RIGHT
                    elif GAME_AREA.collidepoint(pos):
                        swipe_start = pos

                elif state == PAUSED:
                    if BTN_PAUSE.collidepoint(pos):
                        state = PLAYING
                        _play(SND_CLICK, snd_on)

            if event.type == pygame.MOUSEBUTTONUP:
                active_dir = None
                if swipe_start and state == PLAYING:
                    dx = event.pos[0] - swipe_start[0]
                    dy = event.pos[1] - swipe_start[1]
                    if max(abs(dx), abs(dy)) > 25:
                        if abs(dx) > abs(dy):
                            _change_direction(snake, RIGHT if dx > 0 else LEFT)
                        else:
                            _change_direction(snake, DOWN if dy > 0 else UP)
                swipe_start = None

            if event.type != pygame.KEYDOWN:
                continue
            key = event.key

            if state == MAIN_MENU:
                if key == pygame.K_UP:
                    menu_sel = (menu_sel - 1) % len(MENU_ITEMS)
                    _play(SND_CLICK, snd_on)
                elif key == pygame.K_DOWN:
                    menu_sel = (menu_sel + 1) % len(MENU_ITEMS)
                    _play(SND_CLICK, snd_on)
                elif key == pygame.K_RETURN:
                    _play(SND_CLICK, snd_on)
                    action = MENU_ITEMS[menu_sel]
                    if action == "ИГРАТЬ":
                        snake, apple, score, level, speed = _new_game(data)
                        new_record, particles, float_texts = False, [], []
                        level_banner = None
                        state = PLAYING
                    elif action == "НАСТРОЙКИ":
                        diff_i   = DIFFICULTIES.index(data.get("difficulty", "Нормальный"))
                        snd_on   = data.get("sound", True)
                        sett_row = 0
                        state    = SETTINGS
                    elif action == "РЕКОРДЫ":
                        state = RECORDS
                    elif action == "ВЫХОД":
                        save_data(data)
                        pygame.quit()
                        return

            elif state == SETTINGS:
                if key == pygame.K_UP:
                    sett_row = (sett_row - 1) % 2
                elif key == pygame.K_DOWN:
                    sett_row = (sett_row + 1) % 2
                elif key == pygame.K_LEFT:
                    if sett_row == 0:
                        diff_i = (diff_i - 1) % len(DIFFICULTIES)
                    else:
                        snd_on = not snd_on
                    _play(SND_CLICK, snd_on)
                elif key == pygame.K_RIGHT:
                    if sett_row == 0:
                        diff_i = (diff_i + 1) % len(DIFFICULTIES)
                    else:
                        snd_on = not snd_on
                    _play(SND_CLICK, snd_on)
                elif key in (pygame.K_RETURN, pygame.K_ESCAPE):
                    data["difficulty"] = DIFFICULTIES[diff_i]
                    data["sound"]      = snd_on
                    save_data(data)
                    state = MAIN_MENU

            elif state == RECORDS:
                if key == pygame.K_ESCAPE:
                    state = MAIN_MENU

            elif state == PLAYING:
                if key in (pygame.K_p, pygame.K_ESCAPE):
                    state = PAUSED
                else:
                    snake.update_direction(event)

            elif state == PAUSED:
                if key in (pygame.K_p, pygame.K_ESCAPE):
                    state = PLAYING

            elif state == GAME_OVER:
                if key == pygame.K_RETURN:
                    snake, apple, score, level, speed = _new_game(data)
                    new_record, particles, float_texts = False, [], []
                    level_banner = None
                    state = PLAYING
                    _play(SND_CLICK, snd_on)
                elif key == pygame.K_ESCAPE:
                    state    = MAIN_MENU
                    menu_sel = 0

        # ── Game logic ────────────────────────────────────────────────────────
        if state == PLAYING and flash_frames == 0:
            snake.move()

            if snake.get_head_position() == apple.position:
                score        += 1
                snake.length += 1
                prev_apple    = apple.position
                apple.randomize_position(snake.positions)
                _play(SND_EAT, snd_on)
                _spawn_eat_fx(particles, float_texts, prev_apple, score)

                new_level = score // POINTS_PER_LEVEL + 1
                if new_level != level:
                    level        = new_level
                    cfg          = DIFFICULTY_CFG[data["difficulty"]]
                    speed        = min(cfg["base_speed"] + (level - 1) * cfg["increment"], 20)
                    level_banner = LevelBanner(level)
                    _play(SND_LEVEL, snd_on)

                if score > data["high_score"]:
                    data["high_score"] = score

            if snake.self_collision():
                _spawn_death_fx(particles, snake.positions)
                flash_frames = 10
                shake        = 14
                _play(SND_DIE, snd_on)
                new_record = add_score(data, score)
                save_data(data)
                state = GAME_OVER

        # ── Update effects ────────────────────────────────────────────────────
        particles   = [p for p in particles   if p.update()]
        float_texts = [f for f in float_texts if f.update()]
        if level_banner and not level_banner.update():
            level_banner = None

        if shake > 0:
            ox, oy = random.randint(-4, 4), random.randint(-3, 3)
            shake -= 1
        else:
            ox, oy = 0, 0

        # ── Render ────────────────────────────────────────────────────────────
        if flash_frames > 0:
            screen.fill(DARK_RED)
            flash_frames -= 1

        elif state in (MAIN_MENU, SETTINGS, RECORDS):
            if state == MAIN_MENU:
                draw_main_menu(screen, menu_sel, ticks)
            elif state == SETTINGS:
                draw_settings(screen, diff_i, snd_on, sett_row)
            else:
                draw_records(screen, data["scores"])
            screen.blit(_crt, (0, 0))

        else:
            _game_surf.fill(BG_COLOR)
            _draw_grid(_game_surf)
            apple.draw(_game_surf)
            snake.draw(_game_surf)
            draw_hud(_game_surf, score, data["high_score"], level)
            draw_dpad(_game_surf, active_dir)

            for p in particles:
                p.draw(_game_surf)
            for f in float_texts:
                f.draw(_game_surf)
            if level_banner:
                level_banner.draw(_game_surf)

            if state == PAUSED:
                draw_pause_screen(_game_surf)
            elif state == GAME_OVER:
                draw_game_over_screen(_game_surf, score, data["high_score"], new_record)

            _game_surf.blit(_crt, (0, 0))
            screen.fill(BG_COLOR)
            screen.blit(_game_surf, (ox, oy))

        if fade_alpha > 0:
            _fade_surf.set_alpha(fade_alpha)
            screen.blit(_fade_surf, (0, 0))
            fade_alpha = max(0, fade_alpha - 14)

        pygame.display.update()
        clock.tick(speed if state == PLAYING else 60)


if __name__ == "__main__":
    main()
