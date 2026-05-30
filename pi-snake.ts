import type {
  ExtensionAPI,
  ExtensionContext,
} from "@earendil-works/pi-coding-agent";

// ─── Braille primitives ─────────────────────────────────────────────
// Each braille character covers a 4-row × 2-col sub-grid.
// 4 braille chars side-by-side → 8 cols × 4 rows.

const DOT_MAP: Record<string, number> = {
  "0,0": 0x01, "1,0": 0x02, "2,0": 0x04, "3,0": 0x40,
  "0,1": 0x08, "1,1": 0x10, "2,1": 0x20, "3,1": 0x80,
};

const W = 8, H = 4;
const BRAILLE_OFFSET = 0x2800;
const EMPTY_BRAILLE = "\u2800";

function toBraille(grid: Set<string>): string {
  const parts: string[] = [];
  for (let cx = 0; cx < W; cx += 2) {
    let val = 0;
    for (let r = 0; r < H; r++) {
      for (let c = 0; c < 2; c++) {
        if (grid.has(`${r},${cx + c}`)) {
          val |= DOT_MAP[`${r},${c}`];
        }
      }
    }
    parts.push(String.fromCharCode(BRAILLE_OFFSET + val));
  }
  return parts.join("");
}

function toBrailleColored(
  grid: Set<string>,
  coloredDots: Set<string>,
  color: string,
): string {
  const RESET = "\x1b[0m";
  const parts: string[] = [];
  for (let cx = 0; cx < W; cx += 2) {
    let snakeVal = 0;
    let colorVal = 0;
    let hasSnake = false;
    let hasColor = false;

    for (let r = 0; r < H; r++) {
      for (let c = 0; c < 2; c++) {
        const globalKey = `${r},${cx + c}`;
        const localKey = `${r},${c}`;
        if (grid.has(globalKey)) {
          snakeVal |= DOT_MAP[localKey];
          hasSnake = true;
        }
        if (coloredDots.has(globalKey)) {
          colorVal |= DOT_MAP[localKey];
          hasColor = true;
        }
      }
    }

    if (hasColor && !hasSnake) {
      // Only colored dots in this char — safe to color
      parts.push(`${color}${String.fromCharCode(BRAILLE_OFFSET + colorVal)}${RESET}`);
    } else if (hasSnake || hasColor) {
      // Mixed — no color
      parts.push(String.fromCharCode(BRAILLE_OFFSET + (snakeVal | colorVal)));
    } else {
      parts.push(EMPTY_BRAILLE);
    }
  }
  return parts.join("");
}

// ─── 1. Snake Animation ─────────────────────────────────────────────

const FOOD_COLORS = [
  "\x1b[38;5;196m", // red
  "\x1b[38;5;226m", // yellow
  "\x1b[38;5;46m",  // green
  "\x1b[38;5;213m", // pink
  "\x1b[38;5;214m", // orange
  "\x1b[38;5;129m", // purple
  "\x1b[38;5;51m",  // cyan
];
const DIRS = [[0, 1], [0, -1], [1, 0], [-1, 0]];

function randomFood(snake: string[]): string {
  const occupied = new Set(snake);
  const candidates: string[] = [];
  for (let r = 0; r < H; r++) {
    for (let c = 0; c < W; c++) {
      const key = `${r},${c}`;
      if (!occupied.has(key)) candidates.push(key);
    }
  }
  return candidates[Math.floor(Math.random() * candidates.length)] || "0,0";
}

function bfsNext(head: string, food: string, occupied: Set<string>): string | null {
  const queue: [string, string[]][] = [[head, []]];
  const visited = new Set<string>([head]);
  while (queue.length > 0) {
    const [pos, path] = queue.shift()!;
    const [cr, cc] = pos.split(",").map(Number);
    for (const [dr, dc] of DIRS) {
      const nr = cr + dr, nc = cc + dc;
      if (nr < 0 || nr >= H || nc < 0 || nc >= W) continue;
      const next = `${nr},${nc}`;
      if (visited.has(next) || occupied.has(next)) continue;
      const newPath = [...path, next];
      if (next === food) return newPath[0];
      visited.add(next);
      queue.push([next, newPath]);
    }
  }
  return null;
}

class SnakeAnimation {
  private snake: string[] = ["1,6", "1,5", "1,4", "1,3"];
  private food: string;
  private foodColor: number;

  constructor() {
    this.food = randomFood(this.snake);
    this.foodColor = Math.floor(Math.random() * FOOD_COLORS.length);
  }

  tick(): string {
    const head = this.snake[0];
    const occupied = new Set(this.snake.slice(0, -1));
    let next = bfsNext(head, this.food, occupied);

    if (!next) {
      const [hr, hc] = head.split(",").map(Number);
      const options: string[] = [];
      for (const [dr, dc] of DIRS) {
        const nr = hr + dr, nc = hc + dc;
        if (nr >= 0 && nr < H && nc >= 0 && nc < W) {
          const candidate = `${nr},${nc}`;
          if (!occupied.has(candidate)) options.push(candidate);
        }
      }
      next = options[Math.floor(Math.random() * options.length)] || head;
    }

    this.snake.unshift(next);
    if (next === this.food) {
      this.snake.pop();
      this.food = randomFood(this.snake);
      this.foodColor = Math.floor(Math.random() * FOOD_COLORS.length);
    } else {
      this.snake.pop();
    }

    const snakeGrid = new Set(this.snake);
    return toBrailleColored(
      snakeGrid,
      new Set([this.food]),
      FOOD_COLORS[this.foodColor % FOOD_COLORS.length],
    );
  }
}

// ─── 2. Pong Animation ──────────────────────────────────────────────

class PongAnimation {
  private ballR = 2;
  private ballC = 4;
  private vr = 1;
  private vc = 1;
  private leftPaddle = 1;   // top row of 2-high paddle
  private rightPaddle = 1;

  tick(): string {
    // Move ball
    this.ballR += this.vr;
    this.ballC += this.vc;

    // Bounce off top/bottom
    if (this.ballR <= 0) { this.ballR = 0; this.vr = 1; }
    if (this.ballR >= H - 1) { this.ballR = H - 1; this.vr = -1; }

    // Left paddle check (column 0)
    if (this.ballC <= 0) {
      if (this.ballR >= this.leftPaddle && this.ballR <= this.leftPaddle + 1) {
        this.ballC = 1;
        this.vc = 1;
      } else {
        this.reset();
        return this.buildFrame();
      }
    }

    // Right paddle check (column W-1)
    if (this.ballC >= W - 1) {
      if (this.ballR >= this.rightPaddle && this.ballR <= this.rightPaddle + 1) {
        this.ballC = W - 2;
        this.vc = -1;
      } else {
        this.reset();
        return this.buildFrame();
      }
    }

    // AI: move paddles toward ball
    this.movePaddle("left");
    this.movePaddle("right");

    return this.buildFrame();
  }

  private movePaddle(side: "left" | "right") {
    const paddle = side === "left" ? this.leftPaddle : this.rightPaddle;
    const center = paddle + 0.5;
    if (center < this.ballR && paddle < H - 2) {
      if (side === "left") this.leftPaddle++; else this.rightPaddle++;
    } else if (center > this.ballR && paddle > 0) {
      if (side === "left") this.leftPaddle--; else this.rightPaddle--;
    }
  }

  private reset() {
    this.ballR = Math.floor(Math.random() * (H - 2)) + 1;
    this.ballC = Math.floor(W / 2);
    this.vr = Math.random() < 0.5 ? 1 : -1;
    this.vc = Math.random() < 0.5 ? 1 : -1;
  }

  private buildFrame(): string {
    const grid = new Set<string>();

    // Left paddle
    grid.add(`${this.leftPaddle},0`);
    grid.add(`${this.leftPaddle + 1},0`);

    // Right paddle
    grid.add(`${this.rightPaddle},${W - 1}`);
    grid.add(`${this.rightPaddle + 1},${W - 1}`);

    // Ball (colored cyan)
    const ballKey = `${this.ballR},${this.ballC}`;
    const coloredDots = new Set([ballKey]);
    grid.add(ballKey);

    return toBrailleColored(grid, coloredDots, "\x1b[38;5;51m");
  }
}

// ─── 3. Tetris Animation ────────────────────────────────────────────
// Pre-generated frame sequence of a tetris game

function generateTetrisFrames(): string[] {
  // We simulate a simple tetris game on 8×4 grid
  // Pieces fall, stack, and full rows clear
  const frames: string[] = [];
  const grid: boolean[][] = Array.from({ length: H }, () => Array(W).fill(false));

  type Piece = { cells: number[][]; col: number };

  // Simple pieces that fit in 8×4
  const pieces: Piece[] = [
    { cells: [[0, 0], [0, 1]], col: 0 },           // horizontal 2
    { cells: [[0, 0], [0, 1]], col: 2 },
    { cells: [[0, 0], [0, 1]], col: 4 },
    { cells: [[0, 0], [0, 1]], col: 6 },
    { cells: [[0, 0], [1, 0]], col: 0 },             // vertical 2
    { cells: [[0, 0], [1, 0], [1, 1]], col: 0 },    // L shape
    { cells: [[0, 0], [0, 1], [1, 0]], col: 2 },    // reverse L
    { cells: [[0, 0], [0, 1], [0, 2]], col: 3 },    // horizontal 3
    { cells: [[0, 0]], col: 3 },                      // single
    { cells: [[0, 0], [0, 1], [1, 0], [1, 1]], col: 0 }, // square
  ];

  function cloneGrid(): boolean[][] {
    return grid.map(row => [...row]);
  }

  function gridToFrame(g: boolean[][]): string {
    const s = new Set<string>();
    for (let r = 0; r < H; r++) {
      for (let c = 0; c < W; c++) {
        if (g[r][c]) s.add(`${r},${c}`);
      }
    }
    return toBraille(s);
  }

  function clearFullRows() {
    for (let r = H - 1; r >= 0; r--) {
      if (grid[r].every(v => v)) {
        grid.splice(r, 1);
        grid.unshift(Array(W).fill(false));
        r++; // re-check this row
      }
    }
  }

  for (const piece of pieces) {
    // Drop the piece from top to bottom
    const cells = piece.cells;
    const baseCol = piece.col;

    let dropRow = 0;
    let landed = false;

    while (!landed) {
      // Check if piece can be at dropRow
      const nextRow = dropRow + 1;
      let canDrop = true;
      for (const [dr, dc] of cells) {
        const r = nextRow + dr;
        const c = baseCol + dc;
        if (r >= H || (r >= 0 && c >= 0 && c < W && grid[r][c])) {
          canDrop = false;
          break;
        }
      }

      if (!canDrop) {
        // Land at dropRow
        for (const [dr, dc] of cells) {
          const r = dropRow + dr;
          const c = baseCol + dc;
          if (r >= 0 && r < H && c >= 0 && c < W) {
            grid[r][c] = true;
          }
        }
        landed = true;
      }

      // Show frame with falling piece
      const tempGrid = cloneGrid();
      for (const [dr, dc] of cells) {
        const r = dropRow + dr;
        const c = baseCol + dc;
        if (r >= 0 && r < H && c >= 0 && c < W) {
          tempGrid[r][c] = true;
        }
      }
      frames.push(gridToFrame(tempGrid));

      if (landed) {
        clearFullRows();
        // Show a couple frames after clearing
        frames.push(gridToFrame(grid));
      } else {
        dropRow = nextRow;
      }
    }
  }

  // Add a few empty frames at the end to loop nicely
  for (let i = 0; i < 5; i++) {
    frames.push(gridToFrame(grid));
  }

  // Clear everything and restart — add fade-out frames
  for (let r = H - 1; r >= 0; r--) {
    for (let c = 0; c < W; c++) {
      if (grid[r][c]) {
        grid[r][c] = false;
        frames.push(gridToFrame(grid));
      }
    }
  }

  return frames.length > 0 ? frames : [EMPTY_BRAILLE.repeat(4)];
}

// ─── 4. Bouncing Ball Animation ─────────────────────────────────────

class BounceAnimation {
  private r = 1.5;
  private c = 3.5;
  private vr = 0.35;
  private vc = 0.55;
  private trail: string[] = [];

  tick(): string {
    // Physics step
    this.r += this.vr;
    this.c += this.vc;

    if (this.r <= 0) { this.r = 0; this.vr = Math.abs(this.vr); }
    if (this.r >= H - 1) { this.r = H - 1; this.vr = -Math.abs(this.vr); }
    if (this.c <= 0) { this.c = 0; this.vc = Math.abs(this.vc); }
    if (this.c >= W - 1) { this.c = W - 1; this.vc = -Math.abs(this.vc); }

    const key = `${Math.round(this.r)},${Math.round(this.c)}`;
    this.trail.unshift(key);
    if (this.trail.length > 3) this.trail.pop();

    const grid = new Set<string>();
    for (const t of this.trail) grid.add(t);

    return toBraille(grid);
  }
}

// ─── 5. Sine Wave Animation ─────────────────────────────────────────

class WaveAnimation {
  private t = 0;

  tick(): string {
    const grid = new Set<string>();

    // 3 overlapping sine waves with different phases
    for (let c = 0; c < W; c++) {
      const y1 = Math.sin((c + this.t) * 0.9) * 1.2 + 2;
      const y2 = Math.sin((c + this.t) * 0.5 + 1.5) * 0.8 + 1.5;
      const y3 = Math.sin((c + this.t) * 1.3 + 3.0) * 0.5 + 2.5;

      for (const y of [y1, y2, y3]) {
        const r = Math.round(y);
        if (r >= 0 && r < H) {
          grid.add(`${r},${c}`);
        }
      }
    }

    this.t += 0.4;
    return toBraille(grid);
  }
}

// ─── 6. Fireflies Animation ─────────────────────────────────────────

class FireflyAnimation {
  private flies: { r: number; c: number; vr: number; vc: number; phase: number; speed: number }[];

  constructor() {
    this.flies = Array.from({ length: 4 }, () => ({
      r: Math.random() * (H - 1),
      c: Math.random() * (W - 1),
      vr: (Math.random() - 0.5) * 0.15,
      vc: (Math.random() - 0.5) * 0.2,
      phase: Math.random() * Math.PI * 2,
      speed: 0.05 + Math.random() * 0.08,
    }));
  }

  tick(): string {
    const grid = new Set<string>();

    for (const f of this.flies) {
      // Drift
      f.r += f.vr;
      f.c += f.vc;

      // Soft boundary bounce
      if (f.r < 0) { f.r = 0; f.vr = Math.abs(f.vr); }
      if (f.r > H - 1) { f.r = H - 1; f.vr = -Math.abs(f.vr); }
      if (f.c < 0) { f.c = 0; f.vc = Math.abs(f.vc); }
      if (f.c > W - 1) { f.c = W - 1; f.vc = -Math.abs(f.vc); }

      // Occasionally change direction
      if (Math.random() < 0.05) {
        f.vr = (Math.random() - 0.5) * 0.15;
        f.vc = (Math.random() - 0.5) * 0.2;
      }

      // Brightness cycle
      f.phase += f.speed;
      const brightness = Math.sin(f.phase);
      if (brightness > 0.2) {
        // Visible
        const pr = Math.round(f.r);
        const pc = Math.round(f.c);
        if (pr >= 0 && pr < H && pc >= 0 && pc < W) {
          grid.add(`${pr},${pc}`);
        }
      }
    }

    return toBraille(grid);
  }
}

// ─── Animation Engine ───────────────────────────────────────────────

type AnimType = "snake" | "pong" | "tetris" | "bounce" | "wave" | "firefly";

const ANIM_LIST: { id: AnimType; label: string }[] = [
  { id: "snake", label: "Snake 🐍" },
  { id: "pong", label: "Pong 🏓" },
  { id: "tetris", label: "Tetris 🧱" },
  { id: "bounce", label: "Bouncing Ball ⚫" },
  { id: "wave", label: "Sine Wave 🌊" },
  { id: "firefly", label: "Fireflies ✨" },
];

const ANIM_INTERVALS: Record<AnimType, number> = {
  snake: 120,
  pong: 200,
  tetris: 180,
  bounce: 120,
  wave: 100,
  firefly: 160,
};

interface AnimationState {
  intervalId: ReturnType<typeof setInterval> | null;
  ctx: ExtensionContext;
  current: AnimType;
}

let globalState: AnimationState | null = null;

function createAnimation(type: AnimType): { tick: () => string } | { frames: string[]; intervalMs: number } {
  switch (type) {
    case "snake":
      return new SnakeAnimation();
    case "pong":
      return new PongAnimation();
    case "tetris": {
      const frames = generateTetrisFrames();
      return { frames, intervalMs: ANIM_INTERVALS.tetris };
    }
    case "bounce":
      return new BounceAnimation();
    case "wave":
      return new WaveAnimation();
    case "firefly":
      return new FireflyAnimation();
  }
}

function startAnimation(type: AnimType, ctx: ExtensionContext) {
  stopAnimation();

  const state: AnimationState = { intervalId: null, ctx, current: type };
  globalState = state;

  const anim = createAnimation(type);

  if ("frames" in anim) {
    // Pre-generated frames — set once
    ctx.ui.setWorkingIndicator({ frames: anim.frames, intervalMs: anim.intervalMs });
  } else {
    // Real-time animation
    const firstFrame = anim.tick();
    ctx.ui.setWorkingIndicator({ frames: [firstFrame], intervalMs: ANIM_INTERVALS[type] });

    const id = setInterval(() => {
      const frame = anim.tick();
      ctx.ui.setWorkingIndicator({ frames: [frame], intervalMs: ANIM_INTERVALS[type] });
    }, ANIM_INTERVALS[type]);

    state.intervalId = id;
    ctx.signal?.addEventListener("abort", () => {
      clearInterval(id);
      state.intervalId = null;
    });
  }
}

function stopAnimation() {
  if (globalState?.intervalId) {
    clearInterval(globalState.intervalId);
    globalState.intervalId = null;
  }
  globalState = null;
}

// ─── Extension Entry ────────────────────────────────────────────────

export default function (pi: ExtensionAPI) {
  // Keep a reference to the UI context from session_start
  let uiCtx: ExtensionUIContext | null = null;

  pi.on("session_start", async (_event, ctx) => {
    if (!ctx.hasUI) return;
    uiCtx = ctx.ui;
    startAnimation("snake", ctx);
  });

  pi.on("session_shutdown", async () => {
    stopAnimation();
    uiCtx = null;
  });

  // Register /snake with subcommand args, or /snake as selector
  pi.registerCommand("snake", {
    description: "Switch animation: /snake <snake|pong|tetris|bounce|wave|firefly> or /snake to pick",
    handler: async (ctx: any) => {
      // Use the saved UI context if command ctx doesn't have ui
      const ui = ctx.ui ?? uiCtx;
      if (!ui) return;

      // Check if args were passed as subcommand
      const args: string | undefined = ctx.args;
      if (args) {
        const target = args.trim().toLowerCase();
        const found = ANIM_LIST.find(a => a.id === target);
        if (found) {
          stopAnimation();
          startAnimation(found.id, { ui, hasUI: true, signal: undefined } as any);
          ui.notify(`Switched to ${found.label}`);
          return;
        }
      }

      // No valid subcommand — show select menu
      const currentLabel = ANIM_LIST.find(a => a.id === globalState?.current)?.label ?? "Snake 🐍";

      const options = ANIM_LIST.map(a =>
        a.id === globalState?.current ? `→ ${a.label} (current)` : `  ${a.label}`
      );

      const choice = await ui.select(
        `Current: ${currentLabel} — Pick an animation:`,
        options,
      );

      if (!choice) return;

      const idx = options.indexOf(choice);
      if (idx < 0) return;

      const selected = ANIM_LIST[idx];
      if (selected) {
        stopAnimation();
        startAnimation(selected.id, { ui, hasUI: true, signal: undefined } as any);
      }
    },
  });
}
