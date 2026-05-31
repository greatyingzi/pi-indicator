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


# ─── 5. Cat Animation (cute cat face, 16x8 two-line) ────────────────

class CatAnimation:
    # States: eyes_center, look_left, eyes_center, look_right,
    #         blink, eyes_center, sleepy, yawn, eyes_center, ear_twitch, blink
    CYCLE = [
        ("center", 12),
        ("left",   6),
        ("center", 10),
        ("right",  6),
        ("center", 8),
        ("blink",  2),
        ("center", 12),
        ("sleepy", 8),
        ("yawn",   6),
        ("center", 10),
        ("twitch", 6),
        ("center", 8),
        ("blink",  2),
    ]

    def __init__(self):
        self.timer = 0
        self.idx = 0

    def tick(self):
        state, dur = self.CYCLE[self.idx]
        self.timer += 1
        if self.timer >= dur:
            self.timer = 0
            self.idx = (self.idx + 1) % len(self.CYCLE)

        cat = set()
        # Ears
        cat.update([(0,3),(0,4),(0,11),(0,12)])
        cat.update([(1,2),(1,3),(1,4),(1,5),(1,10),(1,11),(1,12),(1,13)])
        for c in range(2,14): cat.add((2,c))
        for c in range(1,15): cat.add((3,c))
        for c in range(1,15): cat.add((4,c))
        for c in range(2,14): cat.add((5,c))
        for c in range(3,13): cat.add((6,c))
        for c in range(4,12): cat.add((7,c))

        # Eyes (2x2 each, default = center = full gap)
        le = {(3,5),(3,6),(4,5),(4,6)}
        re = {(3,9),(3,10),(4,9),(4,10)}
        nose = {(5,7),(5,8)}
        cat -= nose
        cat.discard((6,7)); cat.discard((6,8))

        eyes = set()

        if state == "center":
            cat -= le; cat -= re
            eyes = le | re
        elif state == "left":
            cat -= {(3,5),(4,5)}; cat -= {(3,9),(4,9)}
            eyes = {(3,5),(4,5),(3,9),(4,9)}
        elif state == "right":
            cat -= {(3,6),(4,6)}; cat -= {(3,10),(4,10)}
            eyes = {(3,6),(4,6),(3,10),(4,10)}
        elif state == "blink":
            pass  # eyes stay filled
        elif state == "sleepy":
            cat -= {(3,5),(3,6),(3,9),(3,10)}  # only top half gap
            eyes = {(3,5),(3,6),(3,9),(3,10)}
        elif state == "yawn":
            cat -= le; cat -= re
            eyes = le | re
            # Wide mouth
            for c in range(5,11): cat.discard((6,c))
        elif state == "twitch":
            cat -= le; cat -= re
            eyes = le | re
            # Right ear flat
            cat.discard((0,11)); cat.discard((1,12)); cat.discard((1,13))
            cat.add((1,14))

        YELLOW = "\x1b[38;5;226m"
        CYAN = "\x1b[38;5;51m"
        PINK = "\x1b[38;5;213m"

        lines = []
        for half in range(2):
            parts = []
            for cx in range(0, W, 2):
                val = 0
                has_eye = has_nose = has_body = False
                for r in range(4):
                    for c in range(2):
                        gk = (r + half * 4, cx + c)
                        if gk in cat or gk in eyes or gk in nose:
                            val |= DOT_MAP[(r, c)]
                        if gk in eyes: has_eye = True
                        if gk in nose: has_nose = True
                        if gk in cat: has_body = True
                ch = chr_braille(val)
                if val == 0: parts.append(EMPTY_BRAILLE)
                elif has_eye and not has_body and not has_nose:
                    parts.append(f"{CYAN}{ch}{RESET}")
                elif has_nose and not has_body and not has_eye:
                    parts.append(f"{PINK}{ch}{RESET}")
                elif has_body:
                    parts.append(f"{YELLOW}{ch}{RESET}")
                else: parts.append(ch)
            lines.append("".join(parts))
        return "\n".join(lines)


# ─── 6. Invaders Animation (horizontal) ─────────────────────────────
# Ship on LEFT (col 0-1), aliens invade from RIGHT
# Ship moves up/down, bullets shoot RIGHT, aliens approach LEFT

class InvadersAnimation:
    def __init__(self):
        self.ship_row = 2
        self.ship_dir = 1
        self.aliens = set()
        self.alien_dir = -1
        self.alien_timer = 0
        self.bullets = []
        self.shoot_timer = 0
        self._spawn_aliens()

    def _spawn_aliens(self):
        self.aliens.clear()
        for r in range(4):
            self.aliens.add(f"{r},{W-1}")
            self.aliens.add(f"{r},{W-2}")
            self.aliens.add(f"{r},{W-4}")
            self.aliens.add(f"{r},{W-5}")

    def tick(self):
        self.alien_timer += 1
        self.shoot_timer += 1

        # Ship moves up/down
        self.ship_row += self.ship_dir
        if self.ship_row >= H - 1: self.ship_dir = -1
        elif self.ship_row <= 0: self.ship_dir = 1

        # Auto-shoot right
        if self.shoot_timer >= 3:
            self.shoot_timer = 0
            self.bullets.append([self.ship_row, 2])

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
        if self.alien_timer >= 6:
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
        SHIP = "\x1b[38;5;46m"
        ALIEN = "\x1b[38;5;196m"
        BULLET = "\x1b[38;5;226m"
        ship_dots = {f"{self.ship_row},0", f"{self.ship_row},1"}
        alien_dots = set(self.aliens)
        bullet_dots = set(f"{b[0]},{b[1]}" for b in self.bullets if 0 <= b[1] < W)

        parts = []
        for cx in range(0, W, 2):
            val = 0
            has_ship = has_alien = has_bullet = False
            for r in range(H):
                for c in range(2):
                    gk = f"{r},{cx + c}"
                    if gk in ship_dots or gk in alien_dots or gk in bullet_dots:
                        val |= DOT_MAP[(r, c)]
                    if gk in ship_dots: has_ship = True
                    if gk in alien_dots: has_alien = True
                    if gk in bullet_dots: has_bullet = True
            ch = chr_braille(val)
            if val == 0:
                parts.append(EMPTY_BRAILLE)
            elif has_alien and not has_ship and not has_bullet:
                parts.append(f"{ALIEN}{ch}{RESET}")
            elif has_bullet and not has_ship and not has_alien:
                parts.append(f"{BULLET}{ch}{RESET}")
            elif has_ship:
                parts.append(f"{SHIP}{ch}{RESET}")
            else:
                parts.append(ch)
        return "".join(parts)


# ─── Terminal runner ─────────────────────────────────────────────────

ANIM_DEFS = [
    ("snake",      "Snake 🐍",      SnakeAnimation,      0.120),
    ("breakout",   "Breakout 🧱",   BreakoutAnimation,   0.100),
    ("pacman",     "Pac-Man 👾",    PacManAnimation,     0.140),
    ("equalizer",  "Equalizer 📊",  EqualizerAnimation,  0.150),
    ("cat",        "Cat 🐱",        CatAnimation,        0.160),
    ("invaders",   "Invaders 🛸",   InvadersAnimation,   0.120),
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
