#!/usr/bin/env python3
"""
Terminal preview for pi-indicator animations.
Renders braille-dot animations in the terminal.

Usage:
    python preview.py [snake|breakout|pacman|wave|equalizer|fireworks|heartbeat|starfield]
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

FOOD_COLORS = [
    "\x1b[38;5;196m", "\x1b[38;5;226m", "\x1b[38;5;46m",
    "\x1b[38;5;213m", "\x1b[38;5;214m", "\x1b[38;5;129m", "\x1b[38;5;51m",
]

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


def to_braille_colored(grid, colored_dots, color):
    """Render grid with colored highlights."""
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
        ball_key = f"{round(self.br)},{round(self.bc)}"
        grid.add(ball_key)
        return to_braille_colored(grid, {ball_key}, "\x1b[38;5;51m")


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
        pac_dots = self._get_pac_dots()
        grid.update(pac_dots)
        for d in self.dots:
            grid.add(f"2,{d}")

        PAC = "\x1b[38;5;226m"
        DOT = "\x1b[38;5;51m"
        parts = []
        for cx in range(0, W, 2):
            val = pac_val = dot_val = 0
            has_pac = has_dot = False
            for r in range(H):
                for c in range(2):
                    gk = f"{r},{cx + c}"
                    if gk in grid: val |= DOT_MAP[(r, c)]
                    if gk in pac_dots: pac_val |= DOT_MAP[(r, c)]; has_pac = True
                    elif gk in grid: dot_val |= DOT_MAP[(r, c)]; has_dot = True
            ch = chr_braille(val)
            if has_pac and not has_dot: parts.append(f"{PAC}{ch}{RESET}")
            elif has_dot and not has_pac: parts.append(f"{DOT}{ch}{RESET}")
            else: parts.append(ch)
        return "".join(parts)


# ─── 4. Wave Animation ──────────────────────────────────────────────

class WaveAnimation:
    def __init__(self):
        self.t = 0

    def tick(self):
        grid = set()
        colored = set()
        # 3 waves with different colors
        waves = [
            (0.9, 1.2, 2.0, "\x1b[38;5;51m"),   # cyan
            (0.5, 0.8, 1.5, "\x1b[38;5;213m"),   # pink
            (1.3, 0.5, 2.5, "\x1b[38;5;226m"),   # yellow
        ]
        for freq, amp, offset, color in waves:
            for c in range(W):
                y = math.sin((c + self.t) * freq) * amp + offset
                r = round(y)
                if 0 <= r < H:
                    grid.add(f"{r},{c}")
                    colored.add(f"{r},{c}")

        self.t += 0.4
        # All dots are colored — use the last wave color per char
        # Simpler: just render as plain braille
        return to_braille(grid)


# ─── 5. Equalizer Animation ─────────────────────────────────────────

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


# ─── 6. Fireworks Animation ─────────────────────────────────────────

class FireworksAnimation:
    def __init__(self):
        self.phase = "charge"  # charge -> burst -> fade -> charge
        self.phase_timer = 0
        self.charge_y = H - 1  # rising from bottom
        self.cx = random.randint(3, W - 4)  # center x
        self.particles = []  # (r, c, vr, vc, life)

    def tick(self):
        self.phase_timer += 1

        if self.phase == "charge":
            self.charge_y -= 0.15
            if self.charge_y <= 1.5:
                self.phase = "burst"
                self.phase_timer = 0
                # Spawn particles
                for _ in range(12):
                    angle = random.uniform(0, math.pi * 2)
                    speed = random.uniform(0.15, 0.5)
                    self.particles.append([
                        self.charge_y, float(self.cx),
                        math.sin(angle) * speed,
                        -math.cos(angle) * speed,
                        random.randint(8, 14),
                    ])

        elif self.phase == "burst":
            for p in self.particles:
                p[0] += p[2]  # r += vr
                p[1] += p[3]  # c += vc
                p[2] += 0.02  # gravity
                p[4] -= 1     # life
            self.particles = [p for p in self.particles if p[4] > 0]
            if not self.particles:
                self.phase = "fade"
                self.phase_timer = 0

        elif self.phase == "fade":
            if self.phase_timer > 8:
                self.phase = "charge"
                self.charge_y = H - 1
                self.cx = random.randint(3, W - 4)

        # Render
        grid = set()
        colored = set()
        if self.phase == "charge":
            r = round(self.charge_y)
            if 0 <= r < H:
                grid.add(f"{r},{self.cx}")
                colored.add(f"{r},{self.cx}")

        for p in self.particles:
            r, c = round(p[0]), round(p[1])
            if 0 <= r < H and 0 <= c < W:
                grid.add(f"{r},{c}")
                colored.add(f"{r},{c}")

        return to_braille_colored(grid, colored, "\x1b[38;5;226m")


# ─── 7. Heartbeat Animation ─────────────────────────────────────────

class HeartbeatAnimation:
    def __init__(self):
        # ECG waveform: flat=0, small bump=1, big spike=2
        # One cycle: 20 samples
        self.waveform = (
            [0] * 4 +           # flat
            [0, 1, 0] +         # P wave
            [0] * 2 +           # flat
            [-1, -2, 3, -1] +   # QRS complex (big spike)
            [0] * 2 +           # flat
            [0, 1, 0] +         # T wave
            [0] * 3             # flat
        )  # total = 20
        self.offset = 0.0

    def tick(self):
        self.offset += 0.3
        grid = set()
        colored = set()
        for c in range(W):
            idx = int(self.offset + c) % len(self.waveform)
            val = self.waveform[idx]
            # Map val to row: 0->row2(baseline), positive->row1, big positive->row0, negative->row3
            if val == 0:
                r = 2
            elif val == 1:
                r = 1
            elif val == 2:
                r = 0
            elif val == 3:
                r = 0
            elif val == -1:
                r = 3
            elif val == -2:
                r = 3
            else:
                r = 2
            grid.add(f"{r},{c}")
            colored.add(f"{r},{c}")

        return to_braille_colored(grid, colored, "\x1b[38;5;196m")


# ─── 8. Starfield Animation ─────────────────────────────────────────

class StarfieldAnimation:
    def __init__(self):
        self.stars = []
        for _ in range(7):
            self.stars.append({
                "r": random.random() * (H - 1),
                "c": random.random() * (W - 1),
                "vr": (random.random() - 0.5) * 0.08,
                "vc": (random.random() - 0.5) * 0.08,
                "phase": random.random() * math.pi * 2,
                "speed": 0.05 + random.random() * 0.08,
            })

    def tick(self):
        grid = set()
        for s in self.stars:
            s["r"] += s["vr"]
            s["c"] += s["vc"]
            s["phase"] += s["speed"]

            # Soft bounds
            if s["r"] < 0: s["r"] = 0; s["vr"] = abs(s["vr"])
            if s["r"] > H - 1: s["r"] = H - 1; s["vr"] = -abs(s["vr"])
            if s["c"] < 0: s["c"] = 0; s["vc"] = abs(s["vc"])
            if s["c"] > W - 1: s["c"] = W - 1; s["vc"] = -abs(s["vc"])

            # Occasional direction change
            if random.random() < 0.03:
                s["vr"] = (random.random() - 0.5) * 0.08
                s["vc"] = (random.random() - 0.5) * 0.08

            brightness = math.sin(s["phase"])
            if brightness > 0.2:
                r, c = round(s["r"]), round(s["c"])
                if 0 <= r < H and 0 <= c < W:
                    grid.add(f"{r},{c}")

        return to_braille(grid)


# ─── Terminal runner ─────────────────────────────────────────────────

ANIM_DEFS = [
    ("snake",      "Snake 🐍",      SnakeAnimation,      0.120),
    ("breakout",   "Breakout 🧱",   BreakoutAnimation,   0.100),
    ("pacman",     "Pac-Man 👾",    PacManAnimation,     0.140),
    ("wave",       "Wave 🌊",       WaveAnimation,       0.100),
    ("equalizer",  "Equalizer 📊",  EqualizerAnimation,  0.150),
    ("fireworks",  "Fireworks 🎆",  FireworksAnimation,  0.080),
    ("heartbeat",  "Heartbeat ❤️",  HeartbeatAnimation,  0.100),
    ("starfield",  "Starfield ✨",  StarfieldAnimation,  0.200),
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

    for i in range(n):
        sys.stdout.write("\n")
        if i < n - 1:
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
                    frames.append(f"{frame}  \x1b[1m{label}\x1b[0m")

            total_lines = n + (n - 1)
            sys.stdout.write(f"\x1b[{total_lines}A")
            for i, frame in enumerate(frames):
                sys.stdout.write(f"{CLEAR_LINE}\r{frame}\n")
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
