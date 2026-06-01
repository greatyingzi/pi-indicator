#!/usr/bin/env python3
"""
Terminal preview for pi-indicator animations.
Renders braille-dot animations in the terminal.

Usage:
    python preview.py [snake|breakout|pacman|wave|equalizer|heart|fireworks|cat|invaders|gif|stickman]
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


def to_braille_colored(color_map):
    """Render color_map {(row,col): ansi_color} to colored braille string (16x4)."""
    parts = []
    for cx in range(0, W, 2):
        val = 0
        best_color = None
        for r in range(H):
            for c in range(2):
                pos = (r, cx + c)
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
    return "".join(parts)


def to_braille_2line_colored(color_map):
    """Render color_map {(row,col): ansi_color} as two-line colored braille (16x8)."""
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
        color_map = {}
        # Head (bright green)
        hr, hc = map(int, self.snake[0].split(","))
        color_map[(hr, hc)] = "\x1b[38;5;118m"
        # Body (green)
        for pos in self.snake[1:]:
            r, c = map(int, pos.split(","))
            color_map[(r, c)] = "\x1b[38;5;34m"
        # Food (red)
        fr, fc = map(int, self.food.split(","))
        color_map[(fr, fc)] = "\x1b[38;5;196m"
        return to_braille_colored(color_map)


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
        color_map = {}
        # Bricks — color by row
        BRICK_COLORS = {
            0: "\x1b[38;5;226m",  # yellow
            1: "\x1b[38;5;214m",  # orange
            2: "\x1b[38;5;196m",  # red
            3: "\x1b[38;5;196m",  # red
        }
        for key in self.bricks:
            r, c = map(int, key.split(","))
            color_map[(r, c)] = BRICK_COLORS.get(r, "\x1b[38;5;196m")
        # Paddle (white)
        color_map[(self.paddle, W - 1)] = "\x1b[38;5;252m"
        color_map[(self.paddle + 1, W - 1)] = "\x1b[38;5;252m"
        # Ball (bright cyan)
        color_map[(round(self.br), round(self.bc))] = "\x1b[38;5;51m"
        return to_braille_colored(color_map)


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

        color_map = {}
        # Pac-Man (yellow)
        pac_color = "\x1b[38;5;226m"
        for pos in self._get_pac_dots():
            r, c = map(int, pos.split(","))
            color_map[(r, c)] = pac_color
        # Dots (cyan)
        dot_color = "\x1b[38;5;51m"
        for d in self.dots:
            color_map[(2, d)] = dot_color

        return to_braille_colored(color_map)



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
        color_map = {}
        for i in range(8):
            h = round(self.heights[i])
            # Color by height: low=green, mid=yellow, high=red
            if h <= 2:
                bar_color = "\x1b[38;5;46m"
            elif h == 3:
                bar_color = "\x1b[38;5;226m"
            else:
                bar_color = "\x1b[38;5;196m"
            for row in range(H):
                # Fill from bottom: row 3 is bottom, row 0 is top
                if row >= (H - h):
                    color_map[(row, i * 2)] = bar_color
                    color_map[(row, i * 2 + 1)] = bar_color

        return to_braille_colored(color_map)


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

        # Convert pixel tuples to colored braille
        color_map = {}
        cat_color = "\x1b[38;5;226m"
        for (r, c) in pixels:
            color_map[(r, c)] = cat_color
        return to_braille_2line_colored(color_map)


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

        color_map = {}
        # Bright red when beating, darker red when resting
        heart_color = "\x1b[38;5;203m" if frame_idx == 1 else "\x1b[38;5;196m"
        for (r, c) in pixels:
            color_map[(r, c)] = heart_color
        return to_braille_2line_colored(color_map)


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
        color_map = {}
        # Ship (green)
        ship_color = "\x1b[38;5;46m"
        color_map[(self.ship_row, 0)] = ship_color
        color_map[(self.ship_row, 1)] = ship_color
        # Aliens (red)
        alien_color = "\x1b[38;5;196m"
        for key in self.aliens:
            r, c = map(int, key.split(","))
            color_map[(r, c)] = alien_color
        # Bullets (yellow)
        bullet_color = "\x1b[38;5;226m"
        for b in self.bullets:
            if 0 <= b[1] < W:
                color_map[(b[0], b[1])] = bullet_color

        return to_braille_colored(color_map)


# ─── 10. Racer Animation (Road Fighter, 2-lane, colored, 16x8) ──

RACER_PLAYER_MIN_COL = 1
RACER_PLAYER_MAX_COL = 4
RACER_MAX_NPCS = 2
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


# ─── Bloom (flower bloom) ─────────────────────────────────────────

class BloomAnimation:
    """Colorful petals expanding from center, continuous color cycling."""

    def __init__(self):
        self.frame = 0
        self.cx = (H - 1) / 2.0   # center row
        self.cy = (W - 1) / 2.0   # center col
        self.max_dist = math.sqrt(self.cy**2 + self.cx**2)

    @staticmethod
    def _hsl_to_ansi256(h, s, l):
        """HSL (h:0-360, s:0-1, l:0-1) → ANSI 256 color code."""
        h = h % 360
        c = (1 - abs(2 * l - 1)) * s
        x = c * (1 - abs((h / 60) % 2 - 1))
        m = l - c / 2
        if   h < 60:  r1, g1, b1 = c, x, 0
        elif h < 120: r1, g1, b1 = x, c, 0
        elif h < 180: r1, g1, b1 = 0, c, x
        elif h < 240: r1, g1, b1 = 0, x, c
        elif h < 300: r1, g1, b1 = x, 0, c
        else:         r1, g1, b1 = c, 0, x
        r = max(0, min(5, int((r1 + m) * 5 + 0.5)))
        g = max(0, min(5, int((g1 + m) * 5 + 0.5)))
        b = max(0, min(5, int((b1 + m) * 5 + 0.5)))
        return 16 + 36 * r + 6 * g + b

    def tick(self):
        color_map = {}  # (row, col) → ansi_color_code
        phase = self.frame * 0.22
        hue_base = self.frame * 8

        for row in range(H):
            for col in range(W):
                dx = col - self.cy
                dy = row - self.cx
                dist = math.sqrt(dx * dx + dy * dy)

                brightness = 0.0
                best_hue = hue_base

                # 4 concentric wave fronts expanding outward
                for w in range(4):
                    wave_r = (phase + w * (self.max_dist / 4)) % self.max_dist
                    diff = dist - wave_r
                    pulse = math.exp(-0.5 * (diff * diff) / 0.6)
                    if pulse > brightness:
                        brightness = pulse
                        best_hue = hue_base + w * 90 + dist * 40

                if brightness > 0.10:
                    ansi_code = self._hsl_to_ansi256(
                        best_hue, 0.85, 0.50 + brightness * 0.15
                    )
                    color_map[(row, col)] = f"\x1b[38;5;{ansi_code}m"

        self.frame += 1
        return to_braille_colored(color_map)


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
        self.player_col = 2
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
        """Check if NPC can switch to target_lane with at least 4 cols gap from others."""
        col_i = int(round(npc.col))
        nw = self._npc_width(npc)
        for other in self.npcs:
            if other is npc:
                continue
            if other.lane != target_lane:
                continue
            oc = int(round(other.col))
            ow = self._npc_width(other)
            # need at least 4 cols gap between edges
            if not (col_i + nw + 4 <= oc or oc + ow + 4 <= col_i):
                return False
        return True

    def _spawn_npc(self):
        lane = random.randint(0, 1)
        # keep gap in the same lane
        for npc in self.npcs:
            if npc.lane == lane and npc.col >= W - 10:
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
        pc = self.player_col
        pw = RACER_CAR_WIDTHS['standard']

        # ── Spawn ──
        self.spawn_timer += 1
        base_interval = max(12, 22 - int(diff * 8))
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

        # ── Player AI: lane + column positioning ──

        # Evaluate each (lane, col) combination for safety
        def eval_position(lane, col):
            """Score a position: higher = safer. Considers distance to NPCs."""
            score = 0
            for npc in self.npcs:
                col_i = int(round(npc.col))
                nw = RACER_CAR_WIDTHS[npc.tmpl_key]
                # Gap between player front and NPC back
                gap = col_i - (col + pw)
                if gap < 0:
                    # NPC is behind or overlapping — penalty
                    overlap_penalty = abs(gap) + 1
                    if npc.lane == lane:
                        score -= 50 * overlap_penalty  # same lane overlap = very bad
                    else:
                        score -= 5  # other lane, less concern
                else:
                    # NPC ahead — closer = more dangerous
                    if npc.lane == lane:
                        score += gap  # more gap = better
                        if npc.npc_type == 'red':
                            score -= 4  # red might chase
                        elif npc.npc_type == 'yellow':
                            score -= 2  # yellow unpredictable
                    else:
                        score += 2  # other lane NPC is fine
            # Prefer staying in range [1,3] — avoid edges
            if col > 3: score -= 1
            if col < 1: score -= 1
            return score

        best_lane = self.player_lane
        best_col = self.player_col
        best_score = eval_position(self.player_lane, self.player_col)

        for lane in [0, 1]:
            for col in range(RACER_PLAYER_MIN_COL, RACER_PLAYER_MAX_COL + 1):
                # Skip if this position overlaps an NPC
                overlap = False
                for npc in self.npcs:
                    if npc.lane != lane: continue
                    ci = int(round(npc.col))
                    nw = RACER_CAR_WIDTHS[npc.tmpl_key]
                    if not (ci + nw <= col or ci >= col + pw):
                        overlap = True
                        break
                if overlap: continue

                s = eval_position(lane, col)
                # Add small bonus for staying in current lane/col (reduce jitter)
                if lane == self.player_lane: s += 0.5
                if col == self.player_col: s += 0.3

                if s > best_score:
                    best_score = s
                    best_lane = lane
                    best_col = col

        # Apply: lane switches instantly, col moves 1 step per frame
        self.player_lane = best_lane
        if self.player_col < best_col:
            self.player_col += 1
        elif self.player_col > best_col:
            self.player_col -= 1

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



# ─── 11. GifAnimation (basketball pre-converted frames, AI-rembg) ─

BASKETBALL_FRAMES = [
    '⠀⠀⠀⠀⠀⠀\x1b[38;5;102m⢀\x1b[0m\x1b[38;5;102m⣸\x1b[0m\x1b[38;5;102m⣿\x1b[0m\x1b[38;5;139m⠂\x1b[0m⠀⠀⠀⠀⠀⠀\n⠀⠀⠀⠀\x1b[38;5;102m⢀\x1b[0m\x1b[38;5;59m⣴\x1b[0m\x1b[38;5;59m⣿\x1b[0m\x1b[38;5;60m⣿\x1b[0m\x1b[38;5;59m⣿\x1b[0m\x1b[38;5;60m⣷\x1b[0m\x1b[38;5;103m⣄\x1b[0m⠀⠀⠀⠀⠀\n⠀⠀⠀⠀\x1b[38;5;102m⠏\x1b[0m\x1b[38;5;102m⠘\x1b[0m\x1b[38;5;96m⣿\x1b[0m\x1b[38;5;59m⣿\x1b[0m\x1b[38;5;145m⣿\x1b[0m\x1b[38;5;189m⣿\x1b[0m\x1b[38;5;145m⣿\x1b[0m\x1b[38;5;102m⣷\x1b[0m⠀⠀⠀⠀',
    '⠀⠀⠀⠀⠀⠀\x1b[38;5;145m⢰\x1b[0m\x1b[38;5;146m⣿\x1b[0m\x1b[38;5;188m⣗\x1b[0m⠀⠀⠀⠀⠀⠀⠀\n⠀⠀⠀⠀⠀\x1b[38;5;60m⢠\x1b[0m\x1b[38;5;145m⣿\x1b[0m\x1b[38;5;138m⣿\x1b[0m\x1b[38;5;53m⣿\x1b[0m\x1b[38;5;145m⡇\x1b[0m⠀⠀⠀⠀⠀⠀\n⠀⠀⠀⠀⠀\x1b[38;5;59m⢸\x1b[0m\x1b[38;5;17m⣿\x1b[0m\x1b[38;5;59m⣿\x1b[0m\x1b[38;5;59m⣿\x1b[0m\x1b[38;5;59m⡇\x1b[0m⠀⠀⠀⠀⠀⠀',
    '⠀⠀⠀⠀⠀⠀\x1b[38;5;145m⣾\x1b[0m\x1b[38;5;145m⣿\x1b[0m\x1b[38;5;59m⣀\x1b[0m⠀⠀⠀⠀⠀⠀⠀\n⠀⠀⠀⠀⠀\x1b[38;5;59m⢠\x1b[0m\x1b[38;5;139m⣿\x1b[0m\x1b[38;5;138m⣿\x1b[0m\x1b[38;5;59m⣿\x1b[0m\x1b[38;5;60m⡇\x1b[0m⠀⠀⠀⠀⠀⠀\n⠀⠀⠀⠀⠀\x1b[38;5;59m⠈\x1b[0m\x1b[38;5;53m⣿\x1b[0m\x1b[38;5;59m⣿\x1b[0m\x1b[38;5;53m⣿\x1b[0m\x1b[38;5;59m⣧\x1b[0m⠀⠀⠀⠀⠀⠀',
    '⠀⠀⠀⠀⠀⠀\x1b[38;5;145m⣾\x1b[0m\x1b[38;5;146m⣷\x1b[0m\x1b[38;5;103m⣀\x1b[0m⠀⠀⠀⠀⠀⠀⠀\n⠀⠀⠀⠀⠀\x1b[38;5;102m⢀\x1b[0m\x1b[38;5;145m⣿\x1b[0m\x1b[38;5;102m⣿\x1b[0m\x1b[38;5;60m⣿\x1b[0m\x1b[38;5;60m⣧\x1b[0m⠀⠀⠀⠀⠀⠀\n⠀⠀⠀\x1b[38;5;145m⢰\x1b[0m\x1b[38;5;145m⣾\x1b[0m\x1b[38;5;139m⡿\x1b[0m\x1b[38;5;102m⠃\x1b[0m\x1b[38;5;96m⢽\x1b[0m\x1b[38;5;17m⣿\x1b[0m\x1b[38;5;53m⣿\x1b[0m\x1b[38;5;102m⡇\x1b[0m⠀⠀⠀⠀⠀',
    '⠀⠀⠀⠀⠀\x1b[38;5;102m⠐\x1b[0m\x1b[38;5;102m⣿\x1b[0m\x1b[38;5;139m⣇\x1b[0m\x1b[38;5;102m⣀\x1b[0m⠀⠀⠀⠀⠀⠀⠀\n⠀⠀⠀⠀\x1b[38;5;59m⢀\x1b[0m\x1b[38;5;17m⡠\x1b[0m\x1b[38;5;96m⠿\x1b[0m\x1b[38;5;17m⣿\x1b[0m\x1b[38;5;59m⣿\x1b[0m\x1b[38;5;59m⣆\x1b[0m⠀⠀⠀⠀⠀⠀\n⠀⠀⠀⠀⠀⠀⠀\x1b[38;5;60m⣿\x1b[0m\x1b[38;5;59m⣿\x1b[0m\x1b[38;5;59m⣿\x1b[0m\x1b[38;5;59m⠄\x1b[0m⠀⠀⠀⠀⠀',
    '⠀⠀⠀⠀⠀\x1b[38;5;145m⣿\x1b[0m\x1b[38;5;145m⣷\x1b[0m\x1b[38;5;102m⡀\x1b[0m⠀⠀⠀⠀⠀⠀⠀⠀\n⠀\x1b[38;5;181m⢀\x1b[0m\x1b[38;5;188m⣤\x1b[0m\x1b[38;5;139m⡶\x1b[0m\x1b[38;5;102m⠾\x1b[0m\x1b[38;5;96m⠻\x1b[0m\x1b[38;5;17m⣿\x1b[0m\x1b[38;5;59m⣿\x1b[0m\x1b[38;5;103m⣷\x1b[0m⠀⠀⠀⠀⠀⠀⠀\n⠀⠀\x1b[38;5;174m⠙\x1b[0m\x1b[38;5;138m⠁\x1b[0m⠀⠀\x1b[38;5;102m⣿\x1b[0m\x1b[38;5;59m⣿\x1b[0m\x1b[38;5;102m⣏\x1b[0m⠀⠀⠀⠀⠀⠀⠀',
    '⠀⠀⠀⠀⠀\x1b[38;5;102m⣿\x1b[0m\x1b[38;5;96m⣇\x1b[0m\x1b[38;5;60m⣀\x1b[0m⠀⠀⠀⠀⠀⠀⠀⠀\n⠀\x1b[38;5;174m⢠\x1b[0m\x1b[38;5;181m⣶\x1b[0m\x1b[38;5;59m⠖\x1b[0m\x1b[38;5;53m⠚\x1b[0m\x1b[38;5;60m⠻\x1b[0m\x1b[38;5;17m⣿\x1b[0m\x1b[38;5;102m⣿\x1b[0m\x1b[38;5;96m⡟\x1b[0m\x1b[38;5;59m⠂\x1b[0m⠀⠀⠀⠀⠀⠀\n⠀⠀\x1b[38;5;138m⠉\x1b[0m⠀⠀⠀\x1b[38;5;102m⣿\x1b[0m\x1b[38;5;17m⣿\x1b[0m\x1b[38;5;59m⡇\x1b[0m⠀⠀⠀⠀⠀⠀⠀',
    '⠀⠀⠀⠀⠀\x1b[38;5;102m⣿\x1b[0m\x1b[38;5;102m⣇\x1b[0m\x1b[38;5;102m⣀\x1b[0m⠀⠀⠀⠀⠀⠀⠀⠀\n⠀\x1b[38;5;181m⢀\x1b[0m\x1b[38;5;181m⣤\x1b[0m\x1b[38;5;102m⡶\x1b[0m\x1b[38;5;59m⠾\x1b[0m\x1b[38;5;102m⢿\x1b[0m\x1b[38;5;17m⣿\x1b[0m\x1b[38;5;59m⣿\x1b[0m\x1b[38;5;59m⡛\x1b[0m\x1b[38;5;60m⢦\x1b[0m\x1b[38;5;145m⡀\x1b[0m⠀⠀⠀⠀⠀\n⠀⠀\x1b[38;5;174m⠙\x1b[0m\x1b[38;5;138m⠁\x1b[0m⠀\x1b[38;5;103m⢀\x1b[0m\x1b[38;5;60m⣿\x1b[0m\x1b[38;5;59m⣿\x1b[0m\x1b[38;5;59m⡇\x1b[0m\x1b[38;5;145m⠈\x1b[0m\x1b[38;5;188m⠓\x1b[0m⠀⠀⠀⠀⠀',
    '⠀⠀⠀⠀⠀\x1b[38;5;103m⢻\x1b[0m\x1b[38;5;102m⣷\x1b[0m\x1b[38;5;103m⡀\x1b[0m⠀⠀⠀⠀⠀⠀⠀⠀\n⠀⠀⠀\x1b[38;5;59m⣀\x1b[0m\x1b[38;5;59m⡴\x1b[0m\x1b[38;5;102m⢿\x1b[0m\x1b[38;5;17m⣿\x1b[0m\x1b[38;5;102m⣿\x1b[0m\x1b[38;5;59m⣧\x1b[0m\x1b[38;5;59m⡀\x1b[0m⠀⠀⠀⠀⠀⠀\n⠀⠀\x1b[38;5;139m⢺\x1b[0m\x1b[38;5;138m⣷\x1b[0m⠀\x1b[38;5;103m⢠\x1b[0m\x1b[38;5;60m⣿\x1b[0m\x1b[38;5;59m⣿\x1b[0m\x1b[38;5;59m⡇\x1b[0m\x1b[38;5;59m⠹\x1b[0m\x1b[38;5;102m⠄\x1b[0m⠀⠀⠀⠀⠀',
    '⠀⠀⠀⠀⠀⠀\x1b[38;5;145m⢿\x1b[0m\x1b[38;5;139m⣿\x1b[0m⠀⠀⠀⠀⠀⠀⠀⠀\n⠀⠀⠀⠀⠀\x1b[38;5;102m⣰\x1b[0m\x1b[38;5;139m⣿\x1b[0m\x1b[38;5;96m⣿\x1b[0m\x1b[38;5;103m⣷\x1b[0m⠀⠀⠀⠀⠀⠀⠀\n⠀⠀⠀⠀\x1b[38;5;102m⢠\x1b[0m\x1b[38;5;102m⣿\x1b[0m\x1b[38;5;102m⣿\x1b[0m\x1b[38;5;17m⣿\x1b[0m\x1b[38;5;102m⣿\x1b[0m\x1b[38;5;60m⡇\x1b[0m⠀⠀⠀⠀⠀⠀',
    '⠀⠀⠀⠀⠀⠀⠀\x1b[38;5;102m⢐\x1b[0m\x1b[38;5;102m⣿\x1b[0m\x1b[38;5;102m⡇\x1b[0m⠀⠀⠀⠀⠀⠀\n⠀⠀⠀⠀⠀⠀\x1b[38;5;102m⢰\x1b[0m\x1b[38;5;103m⣿\x1b[0m\x1b[38;5;59m⣿\x1b[0m\x1b[38;5;59m⣷\x1b[0m\x1b[38;5;60m⡄\x1b[0m⠀⠀⠀⠀⠀\n⠀⠀⠀⠀⠀⠀\x1b[38;5;60m⣸\x1b[0m\x1b[38;5;17m⣿\x1b[0m\x1b[38;5;53m⣿\x1b[0m\x1b[38;5;102m⣿\x1b[0m\x1b[38;5;53m⠁\x1b[0m⠀⠀⠀⠀⠀',
    '⠀⠀⠀⠀⠀⠀⠀\x1b[38;5;103m⣾\x1b[0m\x1b[38;5;139m⣿\x1b[0m\x1b[38;5;145m⠂\x1b[0m⠀⠀⠀⠀⠀⠀\n⠀⠀⠀⠀⠀⠀\x1b[38;5;102m⣾\x1b[0m\x1b[38;5;60m⣿\x1b[0m\x1b[38;5;96m⣿\x1b[0m\x1b[38;5;145m⣦\x1b[0m⠀⠀⠀⠀⠀⠀\n⠀⠀⠀⠀⠀\x1b[38;5;102m⢸\x1b[0m\x1b[38;5;59m⣿\x1b[0m\x1b[38;5;17m⣿\x1b[0m\x1b[38;5;59m⣿\x1b[0m\x1b[38;5;59m⣿\x1b[0m\x1b[38;5;145m⡀\x1b[0m⠀⠀⠀⠀⠀',
    '⠀⠀⠀⠀⠀⠀\x1b[38;5;145m⢀\x1b[0m\x1b[38;5;103m⣾\x1b[0m\x1b[38;5;103m⡷\x1b[0m⠀⠀⠀⠀⠀⠀⠀\n⠀⠀⠀⠀⠀\x1b[38;5;60m⣰\x1b[0m\x1b[38;5;60m⣿\x1b[0m\x1b[38;5;59m⣿\x1b[0m\x1b[38;5;59m⣿\x1b[0m\x1b[38;5;60m⡆\x1b[0m⠀⠀⠀⠀⠀⠀\n⠀⠀⠀⠀⠀\x1b[38;5;102m⣿\x1b[0m\x1b[38;5;53m⣿\x1b[0m\x1b[38;5;59m⣿\x1b[0m\x1b[38;5;59m⠈\x1b[0m\x1b[38;5;59m⢻\x1b[0m\x1b[38;5;102m⣦\x1b[0m\x1b[38;5;145m⡀\x1b[0m⠀⠀⠀⠀',
    '⠀⠀⠀⠀⠀⠀\x1b[38;5;103m⢀\x1b[0m\x1b[38;5;103m⣾\x1b[0m\x1b[38;5;102m⡿\x1b[0m⠀⠀⠀⠀⠀⠀⠀\n⠀⠀⠀⠀⠀\x1b[38;5;59m⣰\x1b[0m\x1b[38;5;59m⣿\x1b[0m\x1b[38;5;59m⣿\x1b[0m\x1b[38;5;59m⢿\x1b[0m\x1b[38;5;59m⡆\x1b[0m⠀⠀⠀⠀⠀⠀\n⠀⠀⠀⠀⠀\x1b[38;5;96m⣿\x1b[0m\x1b[38;5;59m⣿\x1b[0m\x1b[38;5;59m⣿\x1b[0m\x1b[38;5;59m⠈\x1b[0m\x1b[38;5;59m⢹\x1b[0m\x1b[38;5;59m⣷\x1b[0m\x1b[38;5;145m⡀\x1b[0m⠀⠀⠀⠀',
    '⠀⠀⠀⠀⠀⠀\x1b[38;5;145m⢀\x1b[0m\x1b[38;5;145m⣿\x1b[0m\x1b[38;5;145m⡟\x1b[0m⠀⠀⠀⠀⠀⠀⠀\n⠀⠀⠀⠀⠀\x1b[38;5;102m⢠\x1b[0m\x1b[38;5;102m⣿\x1b[0m\x1b[38;5;59m⣿\x1b[0m\x1b[38;5;59m⣿\x1b[0m\x1b[38;5;102m⠆\x1b[0m⠀⠀⠀⠀⠀⠀\n⠀⠀⠀⠀⠀\x1b[38;5;59m⢸\x1b[0m\x1b[38;5;59m⣿\x1b[0m\x1b[38;5;53m⣿\x1b[0m\x1b[38;5;96m⣿\x1b[0m\x1b[38;5;145m⡀\x1b[0m⠀⠀⠀⠀⠀⠀',
    '⠀⠀⠀⠀⠀⠀⠀\x1b[38;5;145m⣻\x1b[0m\x1b[38;5;102m⣿\x1b[0m\x1b[38;5;145m⠃\x1b[0m⠀⠀⠀⠀⠀⠀\n⠀⠀⠀⠀⠀⠀\x1b[38;5;60m⣼\x1b[0m\x1b[38;5;103m⣿\x1b[0m\x1b[38;5;102m⣿\x1b[0m\x1b[38;5;102m⡷\x1b[0m⠀⠀⠀⠀⠀⠀\n⠀⠀⠀⠀⠀⠀\x1b[38;5;59m⣿\x1b[0m\x1b[38;5;59m⣿\x1b[0m\x1b[38;5;59m⣿\x1b[0m\x1b[38;5;17m⡇\x1b[0m⠀⠀⠀⠀⠀⠀',
    '⠀⠀⠀⠀⠀⠀⠀\x1b[38;5;59m⢀\x1b[0m\x1b[38;5;103m⣿\x1b[0m\x1b[38;5;139m⣗\x1b[0m⠀⠀⠀⠀⠀⠀\n⠀⠀⠀⠀⠀\x1b[38;5;103m⢀\x1b[0m\x1b[38;5;102m⣴\x1b[0m\x1b[38;5;102m⣿\x1b[0m\x1b[38;5;59m⣿\x1b[0m\x1b[38;5;59m⣿\x1b[0m\x1b[38;5;102m⠇\x1b[0m⠀⠀⠀⠀⠀\n⠀⠀⠀⠀\x1b[38;5;103m⣴\x1b[0m\x1b[38;5;103m⡿\x1b[0m\x1b[38;5;59m⠻\x1b[0m\x1b[38;5;59m⣿\x1b[0m\x1b[38;5;17m⣿\x1b[0m\x1b[38;5;59m⣿\x1b[0m⠀⠀⠀⠀⠀⠀',
    '⠀⠀⠀⠀⠀⠀⠀\x1b[38;5;102m⣾\x1b[0m\x1b[38;5;102m⣿\x1b[0m\x1b[38;5;96m⡀\x1b[0m⠀⠀⠀⠀⠀⠀\n⠀⠀⠀⠀\x1b[38;5;59m⣠\x1b[0m\x1b[38;5;60m⣴\x1b[0m\x1b[38;5;59m⣿\x1b[0m\x1b[38;5;102m⣿\x1b[0m\x1b[38;5;95m⣿\x1b[0m\x1b[38;5;102m⣿\x1b[0m⠀⠀⠀⠀⠀⠀\n⠀⠀⠀\x1b[38;5;181m⢸\x1b[0m\x1b[38;5;175m⣿\x1b[0m\x1b[38;5;138m⠆\x1b[0m\x1b[38;5;59m⢹\x1b[0m\x1b[38;5;60m⣿\x1b[0m\x1b[38;5;17m⣿\x1b[0m\x1b[38;5;53m⣿\x1b[0m⠀⠀⠀⠀⠀⠀',
    '⠀⠀⠀⠀⠀\x1b[38;5;103m⠰\x1b[0m\x1b[38;5;102m⣿\x1b[0m\x1b[38;5;139m⣷\x1b[0m\x1b[38;5;59m⣀\x1b[0m⠀⠀⠀⠀⠀⠀⠀\n⠀⠀⠀\x1b[38;5;139m⢀\x1b[0m\x1b[38;5;182m⣾\x1b[0m\x1b[38;5;138m⣶\x1b[0m\x1b[38;5;102m⣿\x1b[0m\x1b[38;5;53m⣿\x1b[0m\x1b[38;5;59m⣿\x1b[0m\x1b[38;5;59m⣷\x1b[0m\x1b[38;5;102m⡄\x1b[0m⠀⠀⠀⠀⠀\n⠀⠀⠀⠀\x1b[38;5;138m⠉\x1b[0m\x1b[38;5;137m⠁\x1b[0m\x1b[38;5;102m⢸\x1b[0m\x1b[38;5;59m⣿\x1b[0m\x1b[38;5;17m⣿\x1b[0m\x1b[38;5;59m⡏\x1b[0m\x1b[38;5;59m⣿\x1b[0m⠀⠀⠀⠀⠀',
    '⠀⠀⠀⠀⠀\x1b[38;5;102m⠸\x1b[0m\x1b[38;5;102m⣿\x1b[0m\x1b[38;5;139m⣆\x1b[0m\x1b[38;5;102m⣀\x1b[0m⠀⠀⠀⠀⠀⠀⠀\n⠀⠀⠀⠀\x1b[38;5;182m⣴\x1b[0m\x1b[38;5;145m⣶\x1b[0m\x1b[38;5;102m⣿\x1b[0m\x1b[38;5;53m⣿\x1b[0m\x1b[38;5;102m⣿\x1b[0m\x1b[38;5;59m⣷\x1b[0m\x1b[38;5;59m⣄\x1b[0m⠀⠀⠀⠀⠀\n⠀⠀⠀⠀\x1b[38;5;181m⠛\x1b[0m\x1b[38;5;174m⠋\x1b[0m\x1b[38;5;102m⢸\x1b[0m\x1b[38;5;59m⣿\x1b[0m\x1b[38;5;17m⣿\x1b[0m\x1b[38;5;59m⡇\x1b[0m\x1b[38;5;59m⢹\x1b[0m\x1b[38;5;59m⡄\x1b[0m⠀⠀⠀⠀',
    '⠀⠀⠀⠀⠀\x1b[38;5;102m⠰\x1b[0m\x1b[38;5;102m⣿\x1b[0m\x1b[38;5;102m⣇\x1b[0m\x1b[38;5;102m⣀\x1b[0m⠀⠀⠀⠀⠀⠀⠀\n⠀⠀⠀⠀⠀\x1b[38;5;59m⢰\x1b[0m\x1b[38;5;102m⣿\x1b[0m\x1b[38;5;59m⣿\x1b[0m\x1b[38;5;102m⣿\x1b[0m\x1b[38;5;59m⡷\x1b[0m\x1b[38;5;102m⣦\x1b[0m\x1b[38;5;145m⡀\x1b[0m⠀⠀⠀⠀\n⠀⠀⠀⠀\x1b[38;5;102m⢀\x1b[0m\x1b[38;5;59m⡿\x1b[0m\x1b[38;5;59m⢹\x1b[0m\x1b[38;5;17m⣿\x1b[0m\x1b[38;5;16m⣿\x1b[0m\x1b[38;5;59m⡇\x1b[0m\x1b[38;5;60m⠈\x1b[0m\x1b[38;5;102m⠷\x1b[0m⠀⠀⠀⠀',
    '⠀⠀⠀⠀⠀\x1b[38;5;102m⠰\x1b[0m\x1b[38;5;102m⢿\x1b[0m\x1b[38;5;102m⣇\x1b[0m\x1b[38;5;102m⣀\x1b[0m⠀⠀⠀⠀⠀⠀⠀\n⠀⠀⠀⠀⠀\x1b[38;5;59m⢰\x1b[0m\x1b[38;5;102m⣿\x1b[0m\x1b[38;5;59m⣿\x1b[0m\x1b[38;5;60m⣿\x1b[0m\x1b[38;5;59m⠳\x1b[0m\x1b[38;5;59m⣦\x1b[0m\x1b[38;5;102m⡀\x1b[0m⠀⠀⠀⠀\n⠀⠀⠀⠀⠀\x1b[38;5;59m⣿\x1b[0m\x1b[38;5;59m⢻\x1b[0m\x1b[38;5;17m⣿\x1b[0m\x1b[38;5;17m⣿\x1b[0m\x1b[38;5;59m⡅\x1b[0m⠀\x1b[38;5;182m⠙\x1b[0m⠀⠀⠀⠀',
]

class GifAnimation:
    """Plays pre-converted braille frames (e.g. basketball GIF)."""
    def __init__(self):
        self.frames = BASKETBALL_FRAMES
        self.idx = 0

    def tick(self):
        f = self.frames[self.idx]
        self.idx = (self.idx + 1) % len(self.frames)
        return f

# ─── 10. StickMan Animation (procedural skeleton pet) ───────────────

STICK_W, STICK_H = 32, 12  # 16 braille chars wide × 3 lines = 32×12 dots

def stick_draw_line(x0, y0, x1, y1, color_map, color):
    """Bresenham line from (x0,y0) to (x1,y1) on 32×12 grid."""
    x0, y0, x1, y1 = int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1))
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy
    safety = 0
    while safety < 500:
        if 0 <= x0 < STICK_W and 0 <= y0 < STICK_H:
            color_map[(y0, x0)] = color
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x0 += sx
        if e2 < dx:
            err += dx
            y0 += sy
        safety += 1


def stick_draw_circle(cx, cy, r, color_map, color):
    """Midpoint circle on 32×12 grid."""
    cx, cy = int(round(cx)), int(round(cy))
    r = max(0, int(round(r)))
    if r == 0:
        if 0 <= cx < STICK_W and 0 <= cy < STICK_H:
            color_map[(cy, cx)] = color
        return
    x, y = r, 0
    d = 1 - r
    while x >= y:
        for dx, dy in [(x,y),(y,x),(-x,y),(-y,x),(x,-dy) if y != 0 else (x,0),
                        (y,-x) if x != 0 else (0,0),(-x,-y) if y != 0 else (-x,0),(-y,-x) if x != 0 else (0,0)]:
            px, py = cx + dx, cy + dy
            if 0 <= px < STICK_W and 0 <= py < STICK_H:
                color_map[(py, px)] = color
        # Fill the circle
        for ix in range(cx - x, cx + x + 1):
            for iy in [cy + y, cy - y]:
                if 0 <= ix < STICK_W and 0 <= iy < STICK_H:
                    color_map[(iy, ix)] = color
        for iy in range(cy - x, cy + x + 1):
            for ix in [cx + y, cx - y]:
                if 0 <= ix < STICK_W and 0 <= iy < STICK_H:
                    color_map[(iy, ix)] = color
        y += 1
        if d <= 0:
            d += 2 * y + 1
        else:
            x -= 1
            d += 2 * (y - x) + 1


def stick_draw_dot(cx, cy, color_map, color):
    """Draw a 2-3px joint dot."""
    for dx in range(-1, 2):
        for dy in range(-1, 2):
            px, py = int(round(cx)) + dx, int(round(cy)) + dy
            if 0 <= px < STICK_W and 0 <= py < STICK_H:
                color_map[(py, px)] = color


def to_braille_3line_colored(color_map):
    """Render color_map {(row,col): ansi_color} as three-line colored braille (32×12)."""
    lines = []
    for half in range(3):
        parts = []
        for cx in range(0, 32, 2):
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


class StickManAnimation:
    """Procedural stick figure that performs random actions like a pet."""

    # Skeleton segment lengths (in pixels)
    TORSO_LEN = 3.0
    NECK_LEN = 1.5
    HEAD_R = 1.5
    UPPER_ARM = 2.0
    LOWER_ARM = 1.8
    UPPER_LEG = 2.0
    LOWER_LEG = 2.0

    # Ground level
    GROUND_Y = 10

    # Action keyframes: each action is a list of poses
    # Each pose is a dict of joint angles (degrees) + torso_lean + offset_y
    # Angles: 0 = down for arms (relative to torso direction), 0 = straight for legs
    # Positive = forward (in facing direction)
    ACTIONS = {
        "idle": [
            {"l_shoulder": 15, "l_elbow": -10, "r_shoulder": -15, "r_elbow": 10,
             "l_hip": -5, "l_knee": 0, "r_hip": 5, "r_knee": 0,
             "torso_lean": 0, "offset_y": 0},
            {"l_shoulder": -10, "l_elbow": 10, "r_shoulder": 10, "r_elbow": -10,
             "l_hip": 5, "l_knee": 0, "r_hip": -5, "r_knee": 0,
             "torso_lean": 0, "offset_y": 0},
        ],
        "walk": [
            {"l_shoulder": -30, "l_elbow": -20, "r_shoulder": 30, "r_elbow": 15,
             "l_hip": 25, "l_knee": -10, "r_hip": -25, "r_knee": 5,
             "torso_lean": 3, "offset_y": 0},
            {"l_shoulder": 0, "l_elbow": -5, "r_shoulder": 0, "r_elbow": 5,
             "l_hip": 0, "l_knee": 0, "r_hip": 0, "r_knee": -15,
             "torso_lean": 2, "offset_y": -0.5},
            {"l_shoulder": 30, "l_elbow": 15, "r_shoulder": -30, "r_elbow": -20,
             "l_hip": -25, "l_knee": 5, "r_hip": 25, "r_knee": -10,
             "torso_lean": 3, "offset_y": 0},
            {"l_shoulder": 0, "l_elbow": 5, "r_shoulder": 0, "r_elbow": -5,
             "l_hip": 0, "l_knee": -15, "r_hip": 0, "r_knee": 0,
             "torso_lean": 2, "offset_y": -0.5},
        ],
        "run": [
            {"l_shoulder": -50, "l_elbow": -40, "r_shoulder": 50, "r_elbow": 30,
             "l_hip": 40, "l_knee": -20, "r_hip": -40, "r_knee": 15,
             "torso_lean": 8, "offset_y": -0.8},
            {"l_shoulder": 50, "l_elbow": 30, "r_shoulder": -50, "r_elbow": -40,
             "l_hip": -40, "l_knee": 15, "r_hip": 40, "r_knee": -20,
             "torso_lean": 8, "offset_y": -0.8},
        ],
        "jump": [
            {"l_shoulder": 15, "l_elbow": -10, "r_shoulder": -15, "r_elbow": 10,
             "l_hip": 15, "l_knee": -35, "r_hip": -15, "r_knee": -35,
             "torso_lean": 0, "offset_y": 1.5},  # crouch
            {"l_shoulder": -60, "l_elbow": -30, "r_shoulder": 60, "r_elbow": 30,
             "l_hip": -10, "l_knee": 5, "r_hip": 10, "r_knee": 5,
             "torso_lean": -5, "offset_y": -3.5},  # launch
            {"l_shoulder": -80, "l_elbow": -20, "r_shoulder": 80, "r_elbow": 20,
             "l_hip": -5, "l_knee": 0, "r_hip": 5, "r_knee": 0,
             "torso_lean": -3, "offset_y": -3.0},  # air
            {"l_shoulder": -40, "l_elbow": -10, "r_shoulder": 40, "r_elbow": 10,
             "l_hip": 0, "l_knee": 0, "r_hip": 0, "r_knee": 0,
             "torso_lean": -2, "offset_y": -1.5},  # descend
            {"l_shoulder": 10, "l_elbow": -5, "r_shoulder": -10, "r_elbow": 5,
             "l_hip": 10, "l_knee": -25, "r_hip": -10, "r_knee": -25,
             "torso_lean": 0, "offset_y": 1.0},  # land
            {"l_shoulder": 10, "l_elbow": -5, "r_shoulder": -10, "r_elbow": 5,
             "l_hip": 5, "l_knee": -10, "r_hip": -5, "r_knee": -10,
             "torso_lean": 0, "offset_y": 0.5},  # recover
        ],
        "sit": [
            {"l_shoulder": 20, "l_elbow": -30, "r_shoulder": -20, "r_elbow": 30,
             "l_hip": -60, "l_knee": -70, "r_hip": 60, "r_knee": -70,
             "torso_lean": 0, "offset_y": 2.5},
            {"l_shoulder": 25, "l_elbow": -25, "r_shoulder": -25, "r_elbow": 25,
             "l_hip": -65, "l_knee": -75, "r_hip": 65, "r_knee": -75,
             "torso_lean": 0, "offset_y": 2.8},
        ],
        "wave": [
            {"l_shoulder": 10, "l_elbow": -5, "r_shoulder": -120, "r_elbow": -100,
             "l_hip": -5, "l_knee": 0, "r_hip": 5, "r_knee": 0,
             "torso_lean": 0, "offset_y": 0},
            {"l_shoulder": 10, "l_elbow": -5, "r_shoulder": -120, "r_elbow": -50,
             "l_hip": -5, "l_knee": 0, "r_hip": 5, "r_knee": 0,
             "torso_lean": 0, "offset_y": 0},
            {"l_shoulder": 10, "l_elbow": -5, "r_shoulder": -120, "r_elbow": -100,
             "l_hip": -5, "l_knee": 0, "r_hip": 5, "r_knee": 0,
             "torso_lean": 0, "offset_y": 0},
            {"l_shoulder": 10, "l_elbow": -5, "r_shoulder": -120, "r_elbow": -50,
             "l_hip": -5, "l_knee": 0, "r_hip": 5, "r_knee": 0,
             "torso_lean": 0, "offset_y": 0},
        ],
        "kick": [
            {"l_shoulder": 15, "l_elbow": -10, "r_shoulder": -15, "r_elbow": 10,
             "l_hip": -5, "l_knee": 0, "r_hip": 5, "r_knee": 0,
             "torso_lean": 0, "offset_y": 0},
            {"l_shoulder": 30, "l_elbow": -15, "r_shoulder": -30, "r_elbow": 15,
             "l_hip": -10, "l_knee": 5, "r_hip": 50, "r_knee": -30,
             "torso_lean": -5, "offset_y": 0},
            {"l_shoulder": 40, "l_elbow": -20, "r_shoulder": -40, "r_elbow": 20,
             "l_hip": -15, "l_knee": 5, "r_hip": 80, "r_knee": -10,
             "torso_lean": -8, "offset_y": -0.5},
            {"l_shoulder": 30, "l_elbow": -15, "r_shoulder": -30, "r_elbow": 15,
             "l_hip": -10, "l_knee": 5, "r_hip": 50, "r_knee": -30,
             "torso_lean": -5, "offset_y": 0},
            {"l_shoulder": 15, "l_elbow": -10, "r_shoulder": -15, "r_elbow": 10,
             "l_hip": -5, "l_knee": 0, "r_hip": 5, "r_knee": 0,
             "torso_lean": 0, "offset_y": 0},
        ],
        "dance": [
            {"l_shoulder": -80, "l_elbow": -90, "r_shoulder": 30, "r_elbow": 15,
             "l_hip": 20, "l_knee": -5, "r_hip": -20, "r_knee": 5,
             "torso_lean": 5, "offset_y": -0.5},
            {"l_shoulder": 30, "l_elbow": 15, "r_shoulder": -80, "r_elbow": -90,
             "l_hip": -20, "l_knee": 5, "r_hip": 20, "r_knee": -5,
             "torso_lean": -5, "offset_y": -0.5},
            {"l_shoulder": -90, "l_elbow": -70, "r_shoulder": -90, "r_elbow": -70,
             "l_hip": 15, "l_knee": -15, "r_hip": -15, "r_knee": -15,
             "torso_lean": 0, "offset_y": -1.0},
            {"l_shoulder": 40, "l_elbow": 20, "r_shoulder": 40, "r_elbow": 20,
             "l_hip": -25, "l_knee": 10, "r_hip": 25, "r_knee": 10,
             "torso_lean": 0, "offset_y": 0},
        ],
    }

    ACTION_NAMES = list(ACTIONS.keys())

    def __init__(self):
        self.pose = dict(self.ACTIONS["idle"][0])  # current interpolated pose
        self.facing = 1  # 1=right, -1=left
        self.current_action = "idle"
        self.keyframe_idx = 0
        self.frames_in_step = 0
        self.frames_per_step = 4  # interpolation steps between keyframes
        self.from_pose = dict(self.pose)
        self.to_pose = dict(self.ACTIONS["idle"][0])
        self.idle_count = 0
        self.hip_x = 16.0  # hip center x
        self.hip_y = 6.0   # hip center y

    def _pick_action(self):
        old = self.current_action
        # Weight: idle and walk more common
        weights = {"idle": 3, "walk": 4, "run": 2, "jump": 2, "sit": 2,
                   "wave": 2, "kick": 2, "dance": 2}
        choices = []
        for a, w in weights.items():
            choices.extend([a] * w)
        action = random.choice(choices)
        # Maybe change direction when starting walk/run
        if action in ("walk", "run", "kick") and random.random() < 0.4:
            self.facing *= -1
        self.current_action = action
        self.keyframe_idx = 0
        self.frames_in_step = 0
        keyframes = self.ACTIONS[action]
        # Adjust speed per action
        speed_map = {"idle": 6, "walk": 4, "run": 3, "jump": 3,
                     "sit": 5, "wave": 3, "kick": 3, "dance": 3}
        self.frames_per_step = speed_map.get(action, 4)
        self.from_pose = dict(self.pose)
        self.to_pose = dict(keyframes[0])

    def _lerp_pose(self, t):
        """Linearly interpolate from from_pose to to_pose by t (0..1)."""
        for key in self.from_pose:
            self.pose[key] = self.from_pose[key] + (self.to_pose[key] - self.from_pose[key]) * t

    def _advance(self):
        """Advance animation by one sub-step."""
        self.frames_in_step += 1
        if self.frames_in_step >= self.frames_per_step:
            # Arrived at to_pose
            self.pose = dict(self.to_pose)
            self.from_pose = dict(self.pose)
            self.frames_in_step = 0

            keyframes = self.ACTIONS[self.current_action]
            self.keyframe_idx += 1

            if self.keyframe_idx >= len(keyframes):
                # Action finished, pick new one
                self._pick_action()
            else:
                self.to_pose = dict(keyframes[self.keyframe_idx])

    def _fk(self, pose):
        """Forward kinematics: compute joint positions from pose angles."""
        lean_rad = math.radians(pose["torso_lean"] * self.facing)
        oy = pose["offset_y"]

        # Hip (root)
        hx, hy = self.hip_x, self.hip_y + oy

        # Torso direction: mostly up, tilted by lean
        # 0 lean = straight up (-90 degrees from horizontal)
        torso_angle = -math.pi / 2 + lean_rad
        nx = hx + self.TORSO_LEN * math.cos(torso_angle)
        ny = hy + self.TORSO_LEN * math.sin(torso_angle)

        # Head
        head_cx = nx + self.NECK_LEN * math.cos(torso_angle)
        head_cy = ny + self.NECK_LEN * math.sin(torso_angle)

        # Arms: shoulders at neck base, angle relative to torso
        # Arm hangs down from shoulder; positive angle swings forward
        shoulder_angle_base = torso_angle + math.pi / 2  # perpendicular to torso = down

        # Left arm
        la_angle = shoulder_angle_base + math.radians(pose["l_shoulder"] * self.facing)
        l_elbow_x = nx + self.UPPER_ARM * math.cos(la_angle)
        l_elbow_y = ny + self.UPPER_ARM * math.sin(la_angle)
        la2_angle = la_angle + math.radians(pose["l_elbow"] * self.facing)
        l_hand_x = l_elbow_x + self.LOWER_ARM * math.cos(la2_angle)
        l_hand_y = l_elbow_y + self.LOWER_ARM * math.sin(la2_angle)

        # Right arm
        ra_angle = shoulder_angle_base + math.radians(pose["r_shoulder"] * self.facing)
        r_elbow_x = nx + self.UPPER_ARM * math.cos(ra_angle)
        r_elbow_y = ny + self.UPPER_ARM * math.sin(ra_angle)
        ra2_angle = ra_angle + math.radians(pose["r_elbow"] * self.facing)
        r_hand_x = r_elbow_x + self.LOWER_ARM * math.cos(ra2_angle)
        r_hand_y = r_elbow_y + self.LOWER_ARM * math.sin(ra2_angle)

        # Legs: from hip, angle 0 = straight down (+90 degrees from horizontal)
        leg_base = math.pi / 2  # straight down

        # Left leg
        ll_angle = leg_base + math.radians(pose["l_hip"] * self.facing)
        l_knee_x = hx + self.UPPER_LEG * math.cos(ll_angle)
        l_knee_y = hy + self.UPPER_LEG * math.sin(ll_angle)
        ll2_angle = ll_angle + math.radians(pose["l_knee"] * self.facing)
        l_foot_x = l_knee_x + self.LOWER_LEG * math.cos(ll2_angle)
        l_foot_y = l_knee_y + self.LOWER_LEG * math.sin(ll2_angle)

        # Right leg
        rl_angle = leg_base + math.radians(pose["r_hip"] * self.facing)
        r_knee_x = hx + self.UPPER_LEG * math.cos(rl_angle)
        r_knee_y = hy + self.UPPER_LEG * math.sin(rl_angle)
        rl2_angle = rl_angle + math.radians(pose["r_knee"] * self.facing)
        r_foot_x = r_knee_x + self.LOWER_LEG * math.cos(rl2_angle)
        r_foot_y = r_knee_y + self.LOWER_LEG * math.sin(rl2_angle)

        return {
            "hip": (hx, hy),
            "neck": (nx, ny),
            "head": (head_cx, head_cy),
            "l_elbow": (l_elbow_x, l_elbow_y),
            "l_hand": (l_hand_x, l_hand_y),
            "r_elbow": (r_elbow_x, r_elbow_y),
            "r_hand": (r_hand_x, r_hand_y),
            "l_knee": (l_knee_x, l_knee_y),
            "l_foot": (l_foot_x, l_foot_y),
            "r_knee": (r_knee_x, r_knee_y),
            "r_foot": (r_foot_x, r_foot_y),
        }

    def tick(self):
        # Interpolate current step
        t = self.frames_in_step / self.frames_per_step if self.frames_per_step > 0 else 1.0
        # Smooth step
        t = t * t * (3 - 2 * t)
        self._lerp_pose(t)

        joints = self._fk(self.pose)
        color_map = {}
        body_color = "\x1b[38;5;46m"   # bright green
        joint_color = "\x1b[38;5;82m"   # lighter green
        head_color = "\x1b[38;5;226m"   # yellow

        # Draw skeleton segments
        j = joints
        # Torso
        stick_draw_line(j["hip"][0], j["hip"][1], j["neck"][0], j["neck"][1], color_map, body_color)
        # Left arm
        stick_draw_line(j["neck"][0], j["neck"][1], j["l_elbow"][0], j["l_elbow"][1], color_map, body_color)
        stick_draw_line(j["l_elbow"][0], j["l_elbow"][1], j["l_hand"][0], j["l_hand"][1], color_map, body_color)
        # Right arm
        stick_draw_line(j["neck"][0], j["neck"][1], j["r_elbow"][0], j["r_elbow"][1], color_map, body_color)
        stick_draw_line(j["r_elbow"][0], j["r_elbow"][1], j["r_hand"][0], j["r_hand"][1], color_map, body_color)
        # Left leg
        stick_draw_line(j["hip"][0], j["hip"][1], j["l_knee"][0], j["l_knee"][1], color_map, body_color)
        stick_draw_line(j["l_knee"][0], j["l_knee"][1], j["l_foot"][0], j["l_foot"][1], color_map, body_color)
        # Right leg
        stick_draw_line(j["hip"][0], j["hip"][1], j["r_knee"][0], j["r_knee"][1], color_map, body_color)
        stick_draw_line(j["r_knee"][0], j["r_knee"][1], j["r_foot"][0], j["r_foot"][1], color_map, body_color)

        # Neck to head
        stick_draw_line(j["neck"][0], j["neck"][1], j["head"][0], j["head"][1], color_map, body_color)

        # Draw head (filled circle)
        stick_draw_circle(j["head"][0], j["head"][1], self.HEAD_R, color_map, head_color)

        # Draw joints (dots)
        for jname in ["l_elbow", "l_hand", "r_elbow", "r_hand", "l_knee", "r_knee"]:
            stick_draw_dot(j[jname][0], j[jname][1], color_map, joint_color)

        # Draw ground line
        ground_color = "\x1b[38;5;240m"
        for gx in range(0, STICK_W, 2):
            gy = self.GROUND_Y
            if 0 <= gx < STICK_W and 0 <= gy < STICK_H:
                color_map[(gy, gx)] = ground_color

        # Draw action label at top
        self._advance()

        return to_braille_3line_colored(color_map)


# ─── Terminal runner ─────────────────────────────────────────────────

ANIM_DEFS = [
    ("snake",      "Snake 🐍",      SnakeAnimation,      0.120),
    ("breakout",   "Breakout 🧱",   BreakoutAnimation,   0.100),
    ("pacman",     "Pac-Man 👾",    PacManAnimation,     0.140),
    ("equalizer",  "Equalizer 📊",  EqualizerAnimation,  0.150),
    ("cat",        "Cat 🐱",        CatAnimation,        0.160),
    ("heart",      "Heart ❤️",      HeartAnimation,      0.200),
    ("invaders",   "Invaders 🛸",   InvadersAnimation,   0.120),
    ("bloom",      "Bloom 🌸",      BloomAnimation,      0.120),
    ("gif",        "GIF 🏀",        GifAnimation,        0.100),
    ("stickman",   "StickMan 🏃",   StickManAnimation,   0.080),
    # ("racer",      "Racer 🏎️",     RacerAnimation,      0.120),  # TODO: rework
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
