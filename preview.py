#!/usr/bin/env python3
"""
Terminal preview for pi-indicator animations.
Renders braille-dot animations in the terminal.

Usage:
    python preview.py [snake|breakout|pacman|wave|equalizer|heart|fireworks|cat|invaders]
    python preview.py --all       # show all simultaneously
    # No argument → cycle through all, 10s each
"""

import sys
import math
import time
import random
from collections import deque

# ─── Braille primitives ─────────────────────────────────────────────

DOT_MAP = {
    (0, 0): 0x01, (1, 0): 0x02, (2, 0): 0x04, (3, 0): 0x40,
    (0, 1): 0x08, (1, 1): 0x10, (2, 1): 0x20, (3, 1): 0x80,
}

W, H = 16, 4
BRAILLE_OFFSET = 0x2800
EMPTY_BRAILLE = "\u2800"
RESET = "\x1b[0m"
CLEAR_LINE = "\x1b[2K"

DIRS = [(0, 1), (0, -1), (1, 0), (-1, 0)]


def chr_braille(val):
    return chr(BRAILLE_OFFSET + val)


def to_braille(grid):
    """Render grid (set of 'r,c' strings) to braille string."""
    parts = []
    for cx in range(0, W, 2):
        val = 0
        for r in range(H):
            for c in range(2):
                if f"{r},{cx + c}" in grid:
                    val |= DOT_MAP[(r, c)]
        parts.append(chr_braille(val))
    return "".join(parts)


def to_braille_2line(grid, W2=None):
    """Render grid (set of (row,col) tuples) as two-line braille (16x8)."""
    if W2 is None:
        W2 = W
    lines = []
    for half in range(2):
        parts = []
        for cx in range(0, W2, 2):
            val = 0
            for r in range(4):
                for c in range(2):
                    if (r + half * 4, cx + c) in grid:
                        val |= DOT_MAP[(r, c)]
            parts.append(chr_braille(val))
        lines.append("".join(parts))
    return "\n".join(lines)


# ─── 1. Snake Animation ─────────────────────────────────────────────

def random_food(snake):
    occupied = set(snake)
    candidates = [f"{r},{c}" for r in range(H) for c in range(W) if f"{r},{c}" not in occupied]
    return random.choice(candidates) if candidates else "0,0"


def bfs_next(head, food, occupied):
    queue = deque()
    queue.append((head, []))
    visited = {head}
    while queue:
        pos, path = queue.popleft()
        cr, cc = map(int, pos.split(","))
        for dr, dc in DIRS:
            nr, nc = cr + dr, cc + dc
            if nr < 0 or nr >= H or nc < 0 or nc >= W:
                continue
            nxt = f"{nr},{nc}"
            if nxt in visited or nxt in occupied:
                continue
            new_path = path + [nxt]
            if nxt == food:
                return new_path[0]
            visited.add(nxt)
            queue.append((nxt, new_path))
    return None


class SnakeAnimation:
    def __init__(self):
        self.snake = ["1,10", "1,9", "1,8", "1,7"]
        self.food = random_food(self.snake)

    def tick(self):
        head = self.snake[0]
        occupied = set(self.snake[:-1])
        nxt = bfs_next(head, self.food, occupied)
        if nxt is None:
            hr, hc = map(int, head.split(","))
            options = []
            for dr, dc in DIRS:
                nr, nc = hr + dr, hc + dc
                if 0 <= nr < H and 0 <= nc < W:
                    candidate = f"{nr},{nc}"
                    if candidate not in occupied:
                        options.append(candidate)
            nxt = random.choice(options) if options else head
        self.snake.insert(0, nxt)
        if nxt == self.food:
            self.snake.pop()
            self.food = random_food(self.snake)
        else:
            self.snake.pop()
        grid = set(self.snake)
        grid.add(self.food)
        return to_braille(grid)


# ─── 2. Breakout Animation ──────────────────────────────────────────

class BreakoutAnimation:
    def __init__(self):
        self.bricks = set()
        self.reset_bricks()
        self.paddle = 1
        self.br = 1.5
        self.bc = 10.0
        self.vr = 0.4
        self.vc = -0.9

    def reset_bricks(self):
        self.bricks.clear()
        for c in range(6):
            for r in range(H):
                self.bricks.add(f"{r},{c}")

    def tick(self):
        self.br += self.vr
        self.bc += self.vc
        if self.br <= 0:
            self.br = 0; self.vr = abs(self.vr)
        if self.br >= H - 1:
            self.br = H - 1; self.vr = -abs(self.vr)
        if self.bc <= 5:
            hit_r, hit_c = round(self.br), round(self.bc)
            hit_brick = False
            for dc in range(2):
                for dr in range(-1, 2):
                    key = f"{hit_r + dr},{hit_c + dc}"
                    if key in self.bricks:
                        self.bricks.discard(key)
                        hit_brick = True
            if hit_brick or self.bc <= 0:
                self.bc = max(self.bc, 0.5)
                self.vc = abs(self.vc)
        if self.bc >= W - 1:
            pr = round(self.br)
            if self.paddle <= pr <= self.paddle + 1:
                self.bc = W - 1.5
                self.vc = -abs(self.vc)
                self.vr += (self.br - (self.paddle + 0.5)) * 0.25
                self.vr = max(-0.6, min(0.6, self.vr))
            else:
                self.br = 1 + random.random() * 2
                self.bc = 10; self.vr = (random.random() - 0.5) * 0.4; self.vc = -0.9
                if not self.bricks: self.reset_bricks()
                return self._build_frame()
        if self.vc > 0:
            center = self.paddle + 0.5
            if center < self.br and self.paddle < H - 2: self.paddle += 1
            elif center > self.br and self.paddle > 0: self.paddle -= 1
        if not self.bricks: self.reset_bricks()
        return self._build_frame()

    def _build_frame(self):
        grid = set(self.bricks)
        grid.add(f"{self.paddle},{W - 1}")
        grid.add(f"{self.paddle + 1},{W - 1}")
        grid.add(f"{round(self.br)},{round(self.bc)}")
        return to_braille(grid)


# ─── 3. Pac-Man Animation ──────────────────────────────────────────

class PacManAnimation:
    def __init__(self):
        self.mouth_open = True
        self.mouth_phase = 0
        self.dots = []
        self.spawn_timer = 0

    def _get_pac_dots(self):
        s = {"1,0", "2,0"}
        if self.mouth_open:
            s.update(["0,1", "3,1", "0,2", "3,2", "0,3", "3,3"])
        else:
            s.update(["0,1", "1,1", "2,1", "3,1", "0,2", "1,2", "2,2", "3,2", "1,3", "2,3"])
        return s

    def tick(self):
        self.mouth_phase += 1
        if self.mouth_phase % 3 == 0:
            self.mouth_open = not self.mouth_open
        self.spawn_timer += 1
        if self.spawn_timer >= 6:
            self.spawn_timer = 0
            self.dots.append(W - 1)
        self.dots = [d - 1 for d in self.dots]
        self.dots = [d for d in self.dots if d > 4]

        grid = set()
        grid.update(self._get_pac_dots())
        for d in self.dots:
            grid.add(f"2,{d}")

        return to_braille(grid)



# ─── 4. Equalizer Animation ─────────────────────────────────────────

class EqualizerAnimation:
    def __init__(self):
        # 8 bars (one per braille char pair), height 0-4
        self.heights = [0.0] * 8
        self.targets = [random.randint(0, 4) for _ in range(8)]
        self.target_timer = 0

    def tick(self):
        self.target_timer += 1
        if self.target_timer >= 8:
            self.target_timer = 0
            # New random targets
            for i in range(8):
                self.targets[i] = random.randint(0, 4)

        # Smooth interpolation toward targets
        for i in range(8):
            diff = self.targets[i] - self.heights[i]
            self.heights[i] += diff * 0.25

        # Render
        grid = set()
        for i in range(8):
            h = round(self.heights[i])
            for row in range(H):
                # Fill from bottom: row 3 is bottom, row 0 is top
                if row >= (H - h):
                    grid.add(f"{row},{i * 2}")
                    grid.add(f"{row},{i * 2 + 1}")

        return to_braille(grid)


# ─── 5. Cat Animation (SVG-converted 5-frame pixel, no color) ──

class CatAnimation:
    # SVG-converted 5-frame running cat — pure braille, no color
    # Each frame is a frozenset of (row, col) pixel tuples
    FRAMES = [
        # Frame 1
        frozenset({(0,0),(0,9),(0,10),(0,12),(0,13),(1,0),(1,1),(1,9),(1,10),(1,11),(1,12),(1,13),
                    (2,2),(2,3),(2,4),(2,5),(2,6),(2,7),(2,8),(2,9),(2,10),(2,11),(2,12),(2,13),(2,14),
                    (3,0),(3,1),(3,2),(3,3),(3,4),(3,5),(3,6),(3,7),(3,8),(3,9),(3,10),(3,11),(3,12),(3,13),(3,14),
                    (4,0),(4,1),(4,2),(4,3),(4,4),(4,5),(4,6),(4,7),(4,8),(4,9),(4,10),(4,11),(4,12),(4,13),
                    (5,1),(5,2),(5,3),(5,11),(5,12),(5,13)}),
        # Frame 2
        frozenset({(0,0),(0,9),(0,10),(0,12),(0,13),(1,0),(1,1),(1,9),(1,10),(1,11),(1,12),(1,13),
                    (2,2),(2,3),(2,4),(2,5),(2,6),(2,7),(2,8),(2,9),(2,10),(2,11),(2,12),(2,13),(2,14),
                    (3,0),(3,1),(3,2),(3,3),(3,4),(3,5),(3,6),(3,7),(3,8),(3,9),(3,10),(3,11),(3,12),(3,13),(3,14),
                    (4,0),(4,1),(4,2),(4,3),(4,4),(4,5),(4,6),(4,7),(4,8),(4,9),(4,10),(4,11),(4,12),(4,13),
                    (5,3),(5,4),(5,10),(5,11)}),
        # Frame 3
        frozenset({(0,0),(0,9),(0,10),(0,12),(0,13),(1,0),(1,1),(1,9),(1,10),(1,11),(1,12),(1,13),
                    (2,2),(2,3),(2,4),(2,5),(2,6),(2,7),(2,8),(2,9),(2,10),(2,11),(2,12),(2,13),(2,14),
                    (3,0),(3,1),(3,2),(3,3),(3,4),(3,5),(3,6),(3,7),(3,8),(3,9),(3,10),(3,11),(3,12),(3,13),(3,14),
                    (4,0),(4,1),(4,2),(4,3),(4,4),(4,5),(4,6),(4,7),(4,8),(4,9),(4,10),(4,11),(4,12),(4,13),
                    (5,2),(5,3),(5,5),(5,6),(5,7),(5,12)}),
        # Frame 4
        frozenset({(0,0),(0,9),(0,10),(0,12),(0,13),(1,0),(1,1),(1,9),(1,10),(1,11),(1,12),(1,13),
                    (2,2),(2,3),(2,4),(2,5),(2,6),(2,7),(2,8),(2,9),(2,10),(2,11),(2,12),(2,13),(2,14),
                    (3,0),(3,1),(3,2),(3,3),(3,4),(3,5),(3,6),(3,7),(3,8),(3,9),(3,10),(3,11),(3,12),(3,13),(3,14),
                    (4,0),(4,1),(4,2),(4,3),(4,4),(4,5),(4,6),(4,7),(4,8),(4,9),(4,10),(4,11),(4,12),(4,13),
                    (5,4),(5,5),(5,9),(5,10)}),
        # Frame 5
        frozenset({(0,0),(0,9),(0,10),(0,12),(0,13),(1,0),(1,1),(1,9),(1,10),(1,11),(1,12),(1,13),
                    (2,2),(2,3),(2,4),(2,5),(2,6),(2,7),(2,8),(2,9),(2,10),(2,11),(2,12),(2,13),(2,14),
                    (3,0),(3,1),(3,2),(3,3),(3,4),(3,5),(3,6),(3,7),(3,8),(3,9),(3,10),(3,11),(3,12),(3,13),(3,14),
                    (4,0),(4,1),(4,2),(4,3),(4,4),(4,5),(4,6),(4,7),(4,8),(4,9),(4,10),(4,11),(4,12),(4,13),
                    (5,2),(5,3),(5,11),(5,12)}),
    ]

    def __init__(self):
        self.frame_idx = 0

    def tick(self):
        self.frame_idx = (self.frame_idx + 1) % len(self.FRAMES)
        pixels = self.FRAMES[self.frame_idx]

        # Convert pixel tuples to (row, col) set for to_braille_2line
        return to_braille_2line(pixels)


# ─── 6. Heart Animation (heartbeat, 16x8 two-line) ────────────────

class HeartAnimation:
    """Pulsing heart with lub-dub rhythm on 16x8 two-line canvas."""

    FRAMES = [
        # small (rest)
        frozenset({
            (2, 4), (2, 5), (2, 9), (2, 10),
            (3, 3), (3, 4), (3, 5), (3, 6), (3, 7), (3, 8), (3, 9), (3, 10), (3, 11),
            (4, 4), (4, 5), (4, 6), (4, 7), (4, 8), (4, 9), (4, 10),
            (5, 5), (5, 6), (5, 7), (5, 8), (5, 9),
            (6, 6), (6, 7), (6, 8),
            (7, 7),
        }),
        # big (beat)
        frozenset({
            (1, 3), (1, 4), (1, 5), (1, 9), (1, 10), (1, 11),
            (2, 2), (2, 3), (2, 4), (2, 5), (2, 6), (2, 7),
            (2, 8), (2, 9), (2, 10), (2, 11), (2, 12),
            (3, 2), (3, 3), (3, 4), (3, 5), (3, 6), (3, 7),
            (3, 8), (3, 9), (3, 10), (3, 11), (3, 12),
            (4, 3), (4, 4), (4, 5), (4, 6), (4, 7), (4, 8), (4, 9), (4, 10), (4, 11),
            (5, 4), (5, 5), (5, 6), (5, 7), (5, 8), (5, 9), (5, 10),
            (6, 5), (6, 6), (6, 7), (6, 8), (6, 9),
            (7, 6), (7, 7), (7, 8),
        }),
    ]
    # lub-dub pattern: rest, beat, rest, beat(smaller), rest...
    TIMING = [0, 0, 0, 1, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0]

    def __init__(self):
        self.phase = 0

    def tick(self):
        self.phase += 1
        frame_idx = self.TIMING[self.phase % len(self.TIMING)]
        pixels = self.FRAMES[frame_idx]

        return to_braille_2line(pixels)


# ─── 7. Wave Animation (flowing sine, 16x8 two-line) ───────────────

class WaveAnimation:
    """Multi-layered sine waves flowing across the display."""

    def __init__(self):
        self.phase = 0.0

    def tick(self):
        self.phase += 0.3

        grid = set()

        for c in range(W):
            r1 = int(round(4 + 2.5 * math.sin(c * 2 * math.pi / W + self.phase)))
            r2 = int(round(4 + 1.5 * math.sin(c * 2 * math.pi / W * 2 - self.phase * 0.7 + 1.0)))
            r3 = int(round(5 + 1.0 * math.sin(c * 2 * math.pi / W * 0.5 + self.phase * 0.3)))

            for r in [r1, r2, r3]:
                if 0 <= r < 8:
                    grid.add((r, c))

        return to_braille_2line(grid)


# ─── 8. Fireworks Animation (exploding particles, 16x8 two-line) ────

class FireworksAnimation:
    """Fireworks: rockets launch upward and burst into particles."""

    def __init__(self):
        self.particles = []   # [[r, c, vr, vc, life], ...]
        self.rockets = []     # [[c, row], ...]
        self.timer = 0

    def _explode(self, c, r):
        for _ in range(14):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(0.3, 1.2)
            vr = speed * math.sin(angle)
            vc = speed * math.cos(angle)
            life = random.randint(6, 14)
            self.particles.append([r, c, vr, vc, life])

    def tick(self):
        self.timer += 1

        # Spawn rockets
        if self.timer % 12 == 0:
            c = random.randint(2, W - 3)
            self.rockets.append([c, 7.0])

        # Update rockets
        new_rockets = []
        for c, r in self.rockets:
            r -= 0.8
            if r <= random.randint(1, 3):
                self._explode(c, r)
            else:
                new_rockets.append([c, r])
        self.rockets = new_rockets

        # Update particles
        new_particles = []
        for p in self.particles:
            p[0] += p[2]
            p[1] += p[3]
            p[2] *= 0.92
            p[3] *= 0.92
            p[4] -= 1
            if p[4] > 0 and 0 <= p[0] < 8 and 0 <= p[1] < W:
                new_particles.append(p)
        self.particles = new_particles

        # Build grid
        grid = set()
        for p in self.particles:
            r, c = int(round(p[0])), int(round(p[1]))
            if 0 <= r < 8 and 0 <= c < W:
                grid.add((r, c))
        for c, r in self.rockets:
            ri = int(round(r))
            if 0 <= ri < 8 and 0 <= c < W:
                grid.add((ri, c))

        return to_braille_2line(grid)


# ─── 9. Invaders Animation (horizontal) ─────────────────────────────
# Ship on LEFT (col 0-1), aliens invade from RIGHT
# Ship moves up/down, bullets shoot RIGHT, aliens approach LEFT

class InvadersAnimation:
    def __init__(self):
        self.ship_row = 2
        self.ship_dir = 1
        self.ship_pause = 0
        self.aliens = set()
        self.alien_dir = -1
        self.alien_timer = 0
        self.alien_speed = 6
        self.bullets = []
        self.shoot_timer = 0
        self.next_shoot_at = 3
        self.burst_count = 0
        self._spawn_aliens()

    def _spawn_aliens(self):
        self.aliens.clear()
        num_cols = random.randint(2, 4)
        base_col = W - 1 - random.randint(0, 1)
        for i in range(num_cols):
            c = base_col - i * 2
            if c < 4:
                continue
            num_rows = random.randint(1, 3)
            start_row = random.randint(0, H - num_rows)
            for j in range(num_rows):
                self.aliens.add(f"{start_row + j},{c}")
        self.alien_speed = random.randint(5, 8)
        self.alien_dir = -1

    def tick(self):
        self.alien_timer += 1
        self.shoot_timer += 1

        # Ship movement with random pauses and direction changes
        if self.ship_pause > 0:
            self.ship_pause -= 1
        else:
            self.ship_row += self.ship_dir
            if self.ship_row >= H - 1:
                self.ship_dir = -1
                self.ship_pause = random.randint(0, 2)
            elif self.ship_row <= 0:
                self.ship_dir = 1
                self.ship_pause = random.randint(0, 2)
            # Random direction change
            if random.random() < 0.1:
                self.ship_dir *= -1
                self.ship_pause = random.randint(0, 1)

        # Auto-shoot with randomized interval and burst
        if self.burst_count > 0:
            self.burst_count -= 1
            self.bullets.append([self.ship_row, 2])
            if self.burst_count == 0:
                self.shoot_timer = 0
        elif self.shoot_timer >= self.next_shoot_at:
            self.shoot_timer = 0
            self.next_shoot_at = random.randint(2, 5)
            self.bullets.append([self.ship_row, 2])
            if random.random() < 0.2:
                self.burst_count = random.randint(1, 2)

        # Move bullets right
        new_bullets = []
        for b in self.bullets:
            b[1] += 1
            if b[1] < W:
                key = f"{b[0]},{b[1]}"
                if key in self.aliens:
                    self.aliens.discard(key)
                else:
                    new_bullets.append(b)
        self.bullets = new_bullets

        # Move aliens
        if self.alien_timer >= self.alien_speed:
            self.alien_timer = 0
            if self.aliens:
                min_c = min(int(k.split(",")[1]) for k in self.aliens)
                max_c = max(int(k.split(",")[1]) for k in self.aliens)
                new_aliens = set()
                shift_v = False
                if self.alien_dir < 0 and min_c <= 4:
                    self.alien_dir = 1; shift_v = True
                elif self.alien_dir > 0 and max_c >= W - 1:
                    self.alien_dir = -1; shift_v = True

                for key in self.aliens:
                    r, c = map(int, key.split(","))
                    if shift_v: r += 1
                    else: c += self.alien_dir
                    if 0 <= r < H and 0 <= c < W:
                        new_aliens.add(f"{r},{c}")
                self.aliens = new_aliens

            if not self.aliens or any(int(k.split(",")[0]) >= H for k in self.aliens):
                self._spawn_aliens()

        # Render
        grid = set()
        grid.add(f"{self.ship_row},0")
        grid.add(f"{self.ship_row},1")
        grid.update(self.aliens)
        for b in self.bullets:
            if 0 <= b[1] < W:
                grid.add(f"{b[0]},{b[1]}")

        return to_braille(grid)


# ─── 10. Racer Animation (Road Fighter, 2-lane, colored, 16x8) ──

RACER_PLAYER_COL = 2
RACER_MAX_NPCS = 3
RACER_PLAYER_COLOR = "\x1b[38;5;82m"

# NPC type definitions: speed, template key, ANSI 256 color
RACER_NPC_DEFS = {
    'gray':   {'speed': 0.3, 'tmpl': 'small',    'color': 244},
    'blue':   {'speed': 0.5, 'tmpl': 'standard',  'color': 69},
    'yellow': {'speed': 0.7, 'tmpl': 'standard',  'color': 226},
    'red':    {'speed': 0.8, 'tmpl': 'standard',  'color': 196},
    'truck':  {'speed': 0.2, 'tmpl': 'truck',     'color': 240},
}

# Spawn weights: (type, early_weight)
RACER_SPAWN_EARLY = [('gray', 40), ('blue', 25), ('yellow', 15), ('red', 10), ('truck', 10)]
RACER_SPAWN_LATE  = [('gray', 15), ('blue', 20), ('yellow', 25), ('red', 30), ('truck', 10)]

# Car pixel templates (row, col) — all symmetric so no mirror needed
RACER_CAR_TEMPLATES = {
    'small':    frozenset({(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)}),
    'standard': frozenset({(0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (1, 3)}),
    'truck':    frozenset({(0, 1), (0, 2), (0, 3), (0, 4),
                           (1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (1, 5)}),
}
RACER_CAR_WIDTHS = {'small': 3, 'standard': 4, 'truck': 6}


def _racer_lane_off(lane):
    """Row offset for a 2-row car centered in a 4-row lane."""
    return (0 if lane == 0 else 4) + 1


class RacerNPC:
    """NPC car with Road Fighter–style AI behaviour."""
    __slots__ = ('lane', 'col', 'speed', 'color', 'npc_type', 'tmpl_key',
                 'accumulator', 'weave_timer', 'weave_interval', 'chase_cooldown')

    def __init__(self, lane, col, npc_type):
        self.lane = lane
        self.col = float(col)
        self.npc_type = npc_type
        defn = RACER_NPC_DEFS[npc_type]
        self.speed = defn['speed']
        self.color = f"\x1b[38;5;{defn['color']}m"
        self.tmpl_key = defn['tmpl']
        self.accumulator = 0.0
        self.weave_timer = 0
        self.weave_interval = random.randint(3, 5)
        self.chase_cooldown = 0


class RacerAnimation:
    """Road Fighter–style 2-lane racer on 16×8 canvas (two braille lines).
    5 NPC types: gray (slow), blue (dodge), yellow (weaver),
                 red (chaser), truck (obstacle).
    NPCs keep distance from each other. Collision = explosion + respawn.
    """

    # Explosion frames: expanding then fading cross pattern
    EXPLODE_FRAMES = [
        frozenset({(0,0),(0,1),(0,2),(1,0),(1,1),(1,2),(2,0),(2,1),(2,2)}),
        frozenset({(0,0),(0,2),(1,1),(2,0),(2,2)}),
        frozenset({(0,0),(0,2),(1,1),(2,0),(2,2)}),
        frozenset({(1,1)}),
    ]
    EXPLODE_COLOR = "\x1b[38;5;202m"  # orange-red

    def __init__(self):
        self.player_lane = 0
        self.npcs: list[RacerNPC] = []
        self.spawn_timer = 12  # start near interval so first NPC appears quickly
        self.ticks = 0
        self.exploding = 0  # frames remaining for explosion
        self.explode_col = 0  # explosion column

    # ── helpers ──

    def _difficulty(self):
        return min(self.ticks / 500.0, 1.0)

    def _pick_npc_type(self):
        diff = self._difficulty()
        late_dict = dict(RACER_SPAWN_LATE)
        weights = {}
        for name, early_w in RACER_SPAWN_EARLY:
            late_w = late_dict[name]
            weights[name] = early_w + (late_w - early_w) * diff
        total = sum(weights.values())
        r = random.uniform(0, total)
        cum = 0.0
        for name, w in weights.items():
            cum += w
            if r <= cum:
                return name
        return 'gray'

    def _npc_width(self, npc):
        return RACER_CAR_WIDTHS[npc.tmpl_key]

    def _can_switch_lane(self, npc, target_lane):
        """Check if NPC can switch to target_lane without overlapping others."""
        col_i = int(round(npc.col))
        nw = self._npc_width(npc)
        for other in self.npcs:
            if other is npc:
                continue
            if other.lane != target_lane:
                continue
            oc = int(round(other.col))
            ow = self._npc_width(other)
            # overlap check: need at least 2 cols gap
            if not (col_i + nw + 2 <= oc or col_i + oc + ow + 2 <= col_i):
                # actually: npc occupies [col_i, col_i+nw), other occupies [oc, oc+ow)
                # no overlap if npc right edge + gap <= other left, or other right edge + gap <= npc left
                if not (col_i + nw + 2 <= oc or oc + ow + 2 <= col_i):
                    return False
        return True

    def _spawn_npc(self):
        lane = random.randint(0, 1)
        # keep gap in the same lane
        for npc in self.npcs:
            if npc.lane == lane and npc.col >= W - 8:
                return
        npc_type = self._pick_npc_type()
        # Also check the other lane to avoid cross-lane spawn on top
        new_w = RACER_CAR_WIDTHS[RACER_NPC_DEFS[npc_type]['tmpl']]
        for npc in self.npcs:
            if npc.lane != lane:
                continue
            nw = self._npc_width(npc)
            # Ensure new NPC at col W+1 doesn't overlap
            if not (W + 1 + new_w + 2 <= int(round(npc.col)) or int(round(npc.col)) + nw + 2 <= W + 1):
                return
        self.npcs.append(RacerNPC(lane, W + 1, npc_type))

    # ── tick ──

    def tick(self):
        self.ticks += 1

        # ── Explosion phase ──
        if self.exploding > 0:
            self.exploding -= 1
            # Render explosion
            color_map = {}
            frame_idx = len(self.EXPLODE_FRAMES) - 1 - self.exploding
            if frame_idx < 0:
                frame_idx = 0
            if frame_idx >= len(self.EXPLODE_FRAMES):
                frame_idx = len(self.EXPLODE_FRAMES) - 1
            pattern = self.EXPLODE_FRAMES[frame_idx]
            p_off = _racer_lane_off(self.player_lane)
            for r, c in pattern:
                ar, ac = r + p_off, self.explode_col + c
                if 0 <= ac < W:
                    color_map[(ar, ac)] = self.EXPLODE_COLOR
            return self._render(color_map)

        diff = self._difficulty()
        pc = RACER_PLAYER_COL
        pw = RACER_CAR_WIDTHS['standard']

        # ── Spawn ──
        self.spawn_timer += 1
        base_interval = max(8, 16 - int(diff * 6))
        if self.spawn_timer >= base_interval and len(self.npcs) < RACER_MAX_NPCS:
            self.spawn_timer = 0
            self._spawn_npc()

        # ── Move NPCs (sub-pixel accumulator) ──
        for npc in self.npcs:
            npc.accumulator += npc.speed
            while npc.accumulator >= 1.0:
                npc.col -= 1
                npc.accumulator -= 1.0

        # ── NPC AI (per-type behaviour, with lane-switch safety) ──
        for npc in self.npcs:
            target_lane = None  # desired lane change

            if npc.npc_type == 'blue':
                # Dodge: player approaching in same lane → switch lane
                col_i = int(round(npc.col))
                if npc.lane == self.player_lane:
                    dist = col_i - (pc + pw)
                    if 0 <= dist < 6:
                        target_lane = 1 - npc.lane

            elif npc.npc_type == 'yellow':
                # Weaver: periodically auto-switch lanes (S-curve)
                npc.weave_timer += 1
                if npc.weave_timer >= npc.weave_interval:
                    npc.weave_timer = 0
                    npc.weave_interval = random.randint(3, 5)
                    target_lane = 1 - npc.lane

            elif npc.npc_type == 'red':
                # Chaser: actively track the player's lane
                if npc.chase_cooldown > 0:
                    npc.chase_cooldown -= 1
                if npc.lane != self.player_lane and npc.chase_cooldown == 0:
                    target_lane = self.player_lane

            # Execute lane switch only if safe
            if target_lane is not None and self._can_switch_lane(npc, target_lane):
                npc.lane = target_lane
                if npc.npc_type == 'red':
                    npc.chase_cooldown = 5

            # gray & truck: straight line, never change lane

        # ── NPC-NPC proximity: push apart if too close ──
        for i, npc in enumerate(self.npcs):
            col_i = int(round(npc.col))
            nw = self._npc_width(npc)
            for j, other in enumerate(self.npcs):
                if i >= j or other.lane != npc.lane:
                    continue
                oc = int(round(other.col))
                ow = self._npc_width(other)
                # Check overlap (no gap needed, just direct overlap)
                if not (col_i + nw <= oc or oc + ow <= col_i):
                    # Push the one that's further right to the other lane
                    if npc.col > other.col:
                        other_lane = 1 - npc.lane
                        if self._can_switch_lane(npc, other_lane):
                            npc.lane = other_lane
                    else:
                        other_lane = 1 - other.lane
                        if self._can_switch_lane(other, other_lane):
                            other.lane = other_lane

        # ── Remove off-screen ──
        self.npcs = [n for n in self.npcs
                     if n.col > -(RACER_CAR_WIDTHS[n.tmpl_key] + 2)]

        # ── Collision check FIRST (before player AI moves) ──
        p_off = _racer_lane_off(self.player_lane)
        player_set = frozenset((r + p_off, pc + c)
                               for r, c in RACER_CAR_TEMPLATES['standard'])

        hit = None
        for npc in self.npcs:
            n_off = _racer_lane_off(npc.lane)
            col_i = int(round(npc.col))
            npc_set = frozenset((r + n_off, col_i + c)
                                for r, c in RACER_CAR_TEMPLATES[npc.tmpl_key])
            if player_set & npc_set:
                hit = npc
                break

        if hit:
            self.npcs.remove(hit)
            self.exploding = len(self.EXPLODE_FRAMES)  # 4 frames
            self.explode_col = int(round(hit.col))

        # ── Player AI (after collision check) ──
        LOOKAHEAD = 14

        def lane_score(lane):
            min_dist = LOOKAHEAD + 1
            threat = 0
            for npc in self.npcs:
                if npc.lane != lane:
                    continue
                col_i = int(round(npc.col))
                nw = RACER_CAR_WIDTHS[npc.tmpl_key]
                gap = col_i - (pc + pw)
                if 0 <= gap < min_dist:
                    min_dist = gap
                if npc.npc_type == 'red' and col_i > pc - 2:
                    threat += 4
                if npc.npc_type == 'yellow' and col_i > pc:
                    threat += 2
                if npc.npc_type == 'truck' and col_i > pc:
                    threat += 1
            return min_dist - threat

        cur_score = lane_score(self.player_lane)
        other_lane = 1 - self.player_lane
        other_score = lane_score(other_lane)

        def lane_safe(lane):
            for npc in self.npcs:
                if npc.lane != lane:
                    continue
                col_i = int(round(npc.col))
                nw = RACER_CAR_WIDTHS[npc.tmpl_key]
                if not (col_i + nw <= pc or col_i >= pc + pw):
                    return False
            return True

        if lane_safe(other_lane) and other_score > cur_score:
            self.player_lane = other_lane

        # ── Render ──
        color_map = {}

        # Player pixels (green)
        p_off = _racer_lane_off(self.player_lane)
        for r, c in RACER_CAR_TEMPLATES['standard']:
            ac = pc + c
            if 0 <= ac < W:
                color_map[(r + p_off, ac)] = RACER_PLAYER_COLOR

        # NPC pixels
        for npc in self.npcs:
            n_off = _racer_lane_off(npc.lane)
            col_i = int(round(npc.col))
            for r, c in RACER_CAR_TEMPLATES[npc.tmpl_key]:
                ac = col_i + c
                if 0 <= ac < W:
                    color_map[(r + n_off, ac)] = npc.color

        return self._render(color_map)

    def _render(self, color_map):
        lines = []
        for half in range(2):
            parts = []
            for cx in range(0, W, 2):
                val = 0
                best_color = None
                for r in range(4):
                    for c in range(2):
                        pos = (r + half * 4, cx + c)
                        if pos in color_map:
                            val |= DOT_MAP[(r, c)]
                            if best_color is None:
                                best_color = color_map[pos]
                if val == 0:
                    parts.append(" ")
                else:
                    ch = chr_braille(val)
                    if best_color:
                        parts.append(f"{best_color}{ch}{RESET}")
                    else:
                        parts.append(ch)
            lines.append("".join(parts))
        return "\n".join(lines)


# ─── Terminal runner ─────────────────────────────────────────────────

ANIM_DEFS = [
    ("snake",      "Snake 🐍",      SnakeAnimation,      0.120),
    ("breakout",   "Breakout 🧱",   BreakoutAnimation,   0.100),
    ("pacman",     "Pac-Man 👾",    PacManAnimation,     0.140),
    ("equalizer",  "Equalizer 📊",  EqualizerAnimation,  0.150),
    ("cat",        "Cat 🐱",        CatAnimation,        0.160),
    ("heart",      "Heart ❤️",      HeartAnimation,      0.200),
    ("invaders",   "Invaders 🛸",   InvadersAnimation,   0.120),
    ("racer",      "Racer 🏎️",     RacerAnimation,      0.120),
]


def run_single(anim_id):
    for aid, label, cls, interval in ANIM_DEFS:
        if aid == anim_id:
            _run_loop([(aid, label, cls, interval)], label_only=label)
            return
    names = ", ".join(a for a, _, _, _ in ANIM_DEFS)
    print(f"Unknown animation: {anim_id}")
    print(f"Choose from: {names}")
    sys.exit(1)


def run_all():
    _run_loop(ANIM_DEFS, label_only=None)


def run_cycle():
    while True:
        for aid, label, cls, interval in ANIM_DEFS:
            _run_loop([(aid, label, cls, interval)], label_only=label, duration=10.0)


def _run_loop(anims, label_only=None, duration=None):
    instances = []
    for aid, label, cls, interval in anims:
        instances.append((label, cls(), interval))

    start = time.time()
    n = len(instances)

    # Tick once to measure frame heights, then re-create instances
    init_frames = [anim.tick() for _, anim, _ in instances]
    frame_heights = [f.count("\n") + 1 for f in init_frames]
    instances = [(l, type(a)(), iv) for (l, a, iv) in instances]

    total_lines = sum(frame_heights) + (n - 1)
    for _ in range(total_lines):
        sys.stdout.write("\n")
    sys.stdout.flush()

    try:
        while True:
            if duration is not None and (time.time() - start) >= duration:
                break

            frames = []
            for i, (label, anim, interval) in enumerate(instances):
                frame = anim.tick()
                if label_only:
                    frames.append(frame)
                else:
                    lines = frame.split("\n")
                    lines[-1] = f"{lines[-1]}  \x1b[1m{label}\x1b[0m"
                    frames.append("\n".join(lines))

            sys.stdout.write(f"\x1b[{total_lines}A")
            for i, frame in enumerate(frames):
                for line in frame.split("\n"):
                    sys.stdout.write(f"{CLEAR_LINE}\r{line}\n")
                if i < n - 1:
                    sys.stdout.write(f"{CLEAR_LINE}\r{'─' * 50}\n")
            sys.stdout.flush()

            time.sleep(max(iv for _, _, iv in instances))

    except KeyboardInterrupt:
        sys.stdout.write(f"\n{RESET}Stopped.\n")
        sys.stdout.flush()
        sys.exit(0)


def main():
    if len(sys.argv) > 1:
        arg = sys.argv[1].strip().lower()
        if arg in ("--help", "-h"):
            names = ", ".join(a for a, _, _, _ in ANIM_DEFS)
            print(f"Usage: python preview.py [{names}|--all]")
            print("  No argument → cycle through all, 10s each")
            print("  --all       → show all simultaneously")
            sys.exit(0)
        if arg == "--all":
            print("Showing all animations simultaneously. Ctrl+C to stop.\n")
            run_all()
        else:
            run_single(arg)
    else:
        print("Cycling through all animations (10s each). Ctrl+C to stop.\n")
        run_cycle()


if __name__ == "__main__":
    main()
