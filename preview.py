#!/usr/bin/env python3
"""
Terminal preview for pi-indicator animations.
Renders Snake, Breakout, and Pac-Man braille animations in the terminal.

Usage:
    python preview.py [snake|breakout|pacman]
    # No argument → cycle through all 3, 10 seconds each
"""

import sys
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

FOOD_COLORS = [
    "\x1b[38;5;196m", "\x1b[38;5;226m", "\x1b[38;5;46m",
    "\x1b[38;5;213m", "\x1b[38;5;214m", "\x1b[38;5;129m", "\x1b[38;5;51m",
]

DIRS = [(0, 1), (0, -1), (1, 0), (-1, 0)]


def chr_braille(val):
    return chr(BRAILLE_OFFSET + val)


def to_braille_colored(grid, colored_dots, color):
    """Render grid with colored highlights. grid and colored_dots are sets of 'r,c' strings."""
    parts = []
    for cx in range(0, W, 2):
        grid_val = 0
        color_val = 0
        has_grid = False
        has_color = False
        for r in range(H):
            for c in range(2):
                gk = f"{r},{cx + c}"
                lk = (r, c)
                if gk in grid:
                    grid_val |= DOT_MAP[lk]
                    has_grid = True
                if gk in colored_dots:
                    color_val |= DOT_MAP[lk]
                    has_color = True
        if has_color and not has_grid:
            parts.append(f"{color}{chr_braille(color_val)}{RESET}")
        elif has_grid or has_color:
            parts.append(chr_braille(grid_val | color_val))
        else:
            parts.append(EMPTY_BRAILLE)
    return "".join(parts)


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
        self.food_color = random.randint(0, len(FOOD_COLORS) - 1)

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
            self.food_color = random.randint(0, len(FOOD_COLORS) - 1)
        else:
            self.snake.pop()
        return to_braille_colored(
            set(self.snake),
            {self.food},
            FOOD_COLORS[self.food_color % len(FOOD_COLORS)],
        )


# ─── 2. Breakout Animation ──────────────────────────────────────────

class BreakoutAnimation:
    def __init__(self):
        self.bricks = set()
        self.reset_bricks()
        self.paddle = 1  # top row of 2-dot paddle at col 15
        self.br = 1.5
        self.bc = 10.0
        self.vr = 0.4
        self.vc = -0.9

    def reset_bricks(self):
        self.bricks.clear()
        for c in range(6):  # columns 0-5
            for r in range(H):
                self.bricks.add(f"{r},{c}")

    def tick(self):
        # Move ball
        self.br += self.vr
        self.bc += self.vc

        # Bounce top/bottom
        if self.br <= 0:
            self.br = 0
            self.vr = abs(self.vr)
        if self.br >= H - 1:
            self.br = H - 1
            self.vr = -abs(self.vr)

        # Bounce off left wall or hit brick
        if self.bc <= 5:
            hit_r = round(self.br)
            hit_c = round(self.bc)
            hit_brick = False
            for dc in range(2):
                for dr in range(-1, 2):
                    cr = hit_r + dr
                    cc = hit_c + dc
                    key = f"{cr},{cc}"
                    if key in self.bricks:
                        self.bricks.discard(key)
                        hit_brick = True
            if hit_brick or self.bc <= 0:
                self.bc = max(self.bc, 0.5)
                self.vc = abs(self.vc)

        # Paddle on right (col W-1)
        if self.bc >= W - 1:
            pr = round(self.br)
            if self.paddle <= pr <= self.paddle + 1:
                self.bc = W - 1.5
                self.vc = -abs(self.vc)
                offset = (self.br - (self.paddle + 0.5)) * 0.25
                self.vr += offset
                self.vr = max(-0.6, min(0.6, self.vr))
            else:
                # Missed – reset
                self.br = 1 + random.random() * 2
                self.bc = 10
                self.vr = (random.random() - 0.5) * 0.4
                self.vc = -0.9
                if not self.bricks:
                    self.reset_bricks()
                return self._build_frame()

        # AI paddle
        if self.vc > 0:
            center = self.paddle + 0.5
            if center < self.br and self.paddle < H - 2:
                self.paddle += 1
            elif center > self.br and self.paddle > 0:
                self.paddle -= 1

        if not self.bricks:
            self.reset_bricks()

        return self._build_frame()

    def _build_frame(self):
        grid = set(self.bricks)
        grid.add(f"{self.paddle},{W - 1}")
        grid.add(f"{self.paddle + 1},{W - 1}")
        ball_r = round(self.br)
        ball_c = round(self.bc)
        ball_key = f"{ball_r},{ball_c}"
        grid.add(ball_key)
        return to_braille_colored(grid, {ball_key}, "\x1b[38;5;51m")


# ─── 3. Pac-Man Animation ──────────────────────────────────────────

class PacManAnimation:
    def __init__(self):
        self.mouth_open = True
        self.mouth_phase = 0
        self.dots = []  # column positions
        self.spawn_timer = 0

    def _get_pac_dots(self):
        s = set()
        # Col 0: rows 1,2 (always)
        s.add("1,0")
        s.add("2,0")
        if self.mouth_open:
            # Col 1,2,3: rows 0,3
            s.add("0,1"); s.add("3,1")
            s.add("0,2"); s.add("3,2")
            s.add("0,3"); s.add("3,3")
        else:
            # Col 1,2: all 4 rows
            s.add("0,1"); s.add("1,1"); s.add("2,1"); s.add("3,1")
            s.add("0,2"); s.add("1,2"); s.add("2,2"); s.add("3,2")
            # Col 3: rows 1,2
            s.add("1,3"); s.add("2,3")
        return s

    def tick(self):
        self.mouth_phase += 1
        if self.mouth_phase % 3 == 0:
            self.mouth_open = not self.mouth_open
        self.spawn_timer += 1

        if self.spawn_timer >= 6:
            self.spawn_timer = 0
            self.dots.append(W - 1)

        # Move dots left
        self.dots = [d - 1 for d in self.dots]

        # Remove dots eaten or past
        self.dots = [d for d in self.dots if d > 4]

        grid = set()
        pac_dots = self._get_pac_dots()

        for key in pac_dots:
            grid.add(key)
        for d in self.dots:
            grid.add(f"2,{d}")

        PAC_COLOR = "\x1b[38;5;226m"
        DOT_COLOR = "\x1b[38;5;51m"

        parts = []
        for cx in range(0, W, 2):
            val = 0
            pac_val = 0
            dot_val = 0
            has_pac = False
            has_dot = False
            for r in range(H):
                for c in range(2):
                    gk = f"{r},{cx + c}"
                    lk = (r, c)
                    if gk in grid:
                        val |= DOT_MAP[lk]
                    if gk in pac_dots:
                        pac_val |= DOT_MAP[lk]
                        has_pac = True
                    if gk in grid and gk not in pac_dots:
                        dot_val |= DOT_MAP[lk]
                        has_dot = True
            ch = chr_braille(val)
            if has_pac and not has_dot:
                parts.append(f"{PAC_COLOR}{ch}{RESET}")
            elif has_dot and not has_pac:
                parts.append(f"{DOT_COLOR}{ch}{RESET}")
            else:
                parts.append(ch)
        return "".join(parts)


# ─── Terminal runner ─────────────────────────────────────────────────

ANIM_DEFS = [
    ("snake",    "Snake 🐍",    SnakeAnimation,    0.120),
    ("breakout", "Breakout 🧱", BreakoutAnimation, 0.100),
    ("pacman",   "Pac-Man 👾",  PacManAnimation,   0.140),
]


def run_single(anim_id):
    for aid, label, cls, interval in ANIM_DEFS:
        if aid == anim_id:
            _run_loop([(aid, label, cls, interval)], label_only=label)
            return
    print(f"Unknown animation: {anim_id}")
    print("Choose from: snake, breakout, pacman")
    sys.exit(1)


def run_all():
    """Show all 3 animations simultaneously, stacked vertically."""
    _run_loop(ANIM_DEFS, label_only=None)


def run_cycle():
    """Cycle through each animation one at a time."""
    while True:
        for aid, label, cls, interval in ANIM_DEFS:
            _run_loop([(aid, label, cls, interval)], label_only=label, duration=10.0)


def _run_loop(anims, label_only=None, duration=None):
    # anims: list of (id, label, class, interval)
    instances = []
    for aid, label, cls, interval in anims:
        instances.append((label, cls(), interval))

    start = time.time()
    n = len(instances)

    # Print initial blank lines for frames
    for _ in range(n):
        sys.stdout.write("\n")
    sys.stdout.flush()

    try:
        while True:
            if duration is not None and (time.time() - start) >= duration:
                break

            # Build all frames
            frames = []
            for i, (label, anim, interval) in enumerate(instances):
                frame = anim.tick()
                if label_only:
                    frames.append(frame)
                else:
                    # Strip ANSI for length calc, emoji counts as 2
                    import re as _re
                    plain = _re.sub(r'\x1b\[[^m]*m', '', label)
                    # wcwidth-like: emoji = 2, ascii = 1
                    visual_len = sum(2 if ord(ch) > 0x1F00 else 1 for ch in plain)
                    pad = 16 - visual_len
                    frames.append(f"\x1b[1m{label}{' ' * max(0, pad)}\x1b[0m{frame}")

            # Move cursor up N lines, clear and rewrite each
            sys.stdout.write(f"\x1b[{n}A")
            for frame in frames:
                sys.stdout.write(f"{CLEAR_LINE}\r{frame}\n")
            sys.stdout.flush()

            # Use the slowest interval
            time.sleep(max(iv for _, _, iv in instances))

    except KeyboardInterrupt:
        sys.stdout.write(f"\n{RESET}Stopped.\n")
        sys.stdout.flush()
        sys.exit(0)


def main():
    if len(sys.argv) > 1:
        arg = sys.argv[1].strip().lower()
        if arg in ("--help", "-h"):
            print("Usage: python preview.py [snake|breakout|pacman|--all]")
            print("  No argument → cycle through all 3, 10s each")
            print("  --all       → show all 3 simultaneously")
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
