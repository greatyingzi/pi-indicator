import type {
  ExtensionAPI,
  ExtensionContext,
  ExtensionUIContext,
} from "@earendil-works/pi-coding-agent";

// ─── Braille primitives ─────────────────────────────────────────────
// 8 braille chars side-by-side → 16 cols × 4 rows

const DOT_MAP: Record<string, number> = {
  "0,0": 0x01, "1,0": 0x02, "2,0": 0x04, "3,0": 0x40,
  "0,1": 0x08, "1,1": 0x10, "2,1": 0x20, "3,1": 0x80,
};

const W = 16, H = 4;
const BRAILLE_OFFSET = 0x2800;
const EMPTY_BRAILLE = "\u2800";
const RESET = "\x1b[0m";

const FOOD_COLORS = [
  "\x1b[38;5;196m", "\x1b[38;5;226m", "\x1b[38;5;46m",
  "\x1b[38;5;213m", "\x1b[38;5;214m", "\x1b[38;5;129m", "\x1b[38;5;51m",
];

function toBraille(grid: Set<string>): string {
  const parts: string[] = [];
  for (let cx = 0; cx < W; cx += 2) {
    let val = 0;
    for (let r = 0; r < H; r++) {
      for (let c = 0; c < 2; c++) {
        if (grid.has(`${r},${cx + c}`)) val |= DOT_MAP[`${r},${c}`];
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
  const parts: string[] = [];
  for (let cx = 0; cx < W; cx += 2) {
    let gridVal = 0, colorVal = 0;
    let hasGrid = false, hasColor = false;
    for (let r = 0; r < H; r++) {
      for (let c = 0; c < 2; c++) {
        const gk = `${r},${cx + c}`, lk = `${r},${c}`;
        if (grid.has(gk)) { gridVal |= DOT_MAP[lk]; hasGrid = true; }
        if (coloredDots.has(gk)) { colorVal |= DOT_MAP[lk]; hasColor = true; }
      }
    }
    if (hasColor && !hasGrid) {
      parts.push(`${color}${String.fromCharCode(BRAILLE_OFFSET + colorVal)}${RESET}`);
    } else if (hasGrid || hasColor) {
      parts.push(String.fromCharCode(BRAILLE_OFFSET + (gridVal | colorVal)));
    } else {
      parts.push(EMPTY_BRAILLE);
    }
  }
  return parts.join("");
}

// ─── 1. Snake Animation ─────────────────────────────────────────────

const DIRS = [[0, 1], [0, -1], [1, 0], [-1, 0]];

function randomFood(snake: string[]): string {
  const occupied = new Set(snake);
  const candidates: string[] = [];
  for (let r = 0; r < H; r++)
    for (let c = 0; c < W; c++) {
      const key = `${r},${c}`;
      if (!occupied.has(key)) candidates.push(key);
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
  private snake = ["1,10", "1,9", "1,8", "1,7"];
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
    return toBrailleColored(
      new Set(this.snake),
      new Set([this.food]),
      FOOD_COLORS[this.foodColor % FOOD_COLORS.length],
    );
  }
}

// ─── 2. Breakout Animation (horizontal) ─────────────────────────────
// Bricks on the LEFT wall, paddle on the RIGHT, ball bounces horizontally

class BreakoutAnimation {
  // Bricks: stored as Set, left-side columns 0-5
  private bricks: Set<string>;
  // Paddle: right side, vertical 2-dot paddle at col 15
  private paddle: number = 1; // top row of paddle (rows paddle, paddle+1)
  // Ball: floating point position
  private br: number = 1.5;
  private bc: number = 10;
  private vr: number = 0.4;
  private vc: number = -0.9;

  constructor() {
    this.bricks = new Set<string>();
    this.resetBricks();
  }

  private resetBricks() {
    this.bricks.clear();
    // Fill columns 0-5, all 4 rows
    for (let c = 0; c <= 5; c++)
      for (let r = 0; r < H; r++)
        this.bricks.add(`${r},${c}`);
  }

  tick(): string {
    // Move ball
    this.br += this.vr;
    this.bc += this.vc;

    // Bounce top/bottom
    if (this.br <= 0) { this.br = 0; this.vr = Math.abs(this.vr); }
    if (this.br >= H - 1) { this.br = H - 1; this.vr = -Math.abs(this.vr); }

    // Bounce off left wall (or hit brick)
    if (this.bc <= 5) {
      const hitR = Math.round(this.br);
      const hitC = Math.round(this.bc);
      // Check brick at hit position and neighbors
      let hitBrick = false;
      for (let dc = 0; dc <= 1; dc++) {
        for (let dr = -1; dr <= 1; dr++) {
          const cr = hitR + dr, cc = hitC + dc;
          const key = `${cr},${cc}`;
          if (this.bricks.has(key)) {
            this.bricks.delete(key);
            hitBrick = true;
          }
        }
      }
      if (hitBrick || this.bc <= 0) {
        this.bc = Math.max(this.bc, 0.5);
        this.vc = Math.abs(this.vc);
      }
    }

    // Paddle on right (col W-1)
    if (this.bc >= W - 1) {
      const pr = Math.round(this.br);
      if (pr >= this.paddle && pr <= this.paddle + 1) {
        this.bc = W - 1.5;
        this.vc = -Math.abs(this.vc);
        // Angle based on where it hit the paddle
        const offset = (this.br - (this.paddle + 0.5)) * 0.25;
        this.vr += offset;
        // Clamp vr
        this.vr = Math.max(-0.6, Math.min(0.6, this.vr));
      } else {
        // Missed! Reset
        this.br = 1 + Math.random() * 2;
        this.bc = 10;
        this.vr = (Math.random() - 0.5) * 0.4;
        this.vc = -0.9;
        // If all bricks gone, regenerate
        if (this.bricks.size === 0) this.resetBricks();
        return this.buildFrame();
      }
    }

    // AI paddle: track ball when it's heading right
    if (this.vc > 0) {
      const center = this.paddle + 0.5;
      if (center < this.br && this.paddle < H - 2) this.paddle++;
      else if (center > this.br && this.paddle > 0) this.paddle--;
    }

    // If all bricks gone, regenerate
    if (this.bricks.size === 0) this.resetBricks();

    return this.buildFrame();
  }

  private buildFrame(): string {
    const grid = new Set<string>(this.bricks);
    // Paddle
    grid.add(`${this.paddle},${W - 1}`);
    grid.add(`${this.paddle + 1},${W - 1}`);
    // Ball
    const ballR = Math.round(this.br);
    const ballC = Math.round(this.bc);
    const ballKey = `${ballR},${ballC}`;
    grid.add(ballKey);

    return toBrailleColored(grid, new Set([ballKey]), "\x1b[38;5;51m");
  }
}

// ─── 3. Pac-Man Animation ──────────────────────────────────────────
// Pac-Man sits at col 3, opens/closes mouth. Dots float in from the right.
// When a dot reaches pac-man, it gets eaten.

class PacManAnimation {
  private mouthOpen: boolean = true;
  private dots: number[] = []; // each dot is just a column position
  private spawnTimer: number = 0;

  tick(): string {
    this.mouthOpen = !this.mouthOpen;
    this.spawnTimer++;

    // Spawn a dot from the right every 3-4 ticks
    if (this.spawnTimer >= 3) {
      this.spawnTimer = 0;
      this.dots.push(W - 1);
    }

    // Move all dots left
    for (let i = 0; i < this.dots.length; i++) {
      this.dots[i]--;
    }

    // Remove dots that reached pac-man (col 3) or went past
    this.dots = this.dots.filter(d => d > 3);

    // Render
    const grid = new Set<string>();
    const pacColored = new Set<string>();

    // Pac-Man at row 2, col 3 (always)
    // When mouth open: show pac-man + nothing to its right
    // When mouth closed: just pac-man
    const pacKey = "2,3";
    grid.add(pacKey);
    pacColored.add(pacKey);

    // Dots at row 2
    for (const d of this.dots) {
      grid.add(`2,${d}`);
    }

    // Build with pac-man yellow
    const PAC_COLOR = "\x1b[38;5;226m";
    const DOT_COLOR = "\x1b[38;5;51m"; // cyan dots

    const parts: string[] = [];
    for (let cx = 0; cx < W; cx += 2) {
      let val = 0;
      let hasPac = false;
      let hasDot = false;

      for (let r = 0; r < H; r++) {
        for (let c = 0; c < 2; c++) {
          const gk = `${r},${cx + c}`;
          if (grid.has(gk)) val |= DOT_MAP[`${r},${c}`];
          if (pacColored.has(gk)) hasPac = true;
          // Check if this cell is a dot (not pac)
          if (grid.has(gk) && !pacColored.has(gk)) hasDot = true;
        }
      }

      const ch = String.fromCharCode(BRAILLE_OFFSET + val);
      if (hasPac && !hasDot) {
        parts.push(`${PAC_COLOR}${ch}${RESET}`);
      } else if (hasDot && !hasPac) {
        parts.push(`${DOT_COLOR}${ch}${RESET}`);
      } else {
        parts.push(ch);
      }
    }

    return parts.join("");
  }
}

// ─── Animation Engine ───────────────────────────────────────────────

type AnimType = "snake" | "breakout" | "pacman";

const ANIM_LIST: { id: AnimType; label: string }[] = [
  { id: "snake", label: "Snake 🐍" },
  { id: "breakout", label: "Breakout 🧱" },
  { id: "pacman", label: "Pac-Man 👾" },
];

const ANIM_INTERVALS: Record<AnimType, number> = {
  snake: 120,
  breakout: 100,
  pacman: 140,
};

interface AnimationState {
  intervalId: ReturnType<typeof setInterval> | null;
  ctx: ExtensionContext;
  current: AnimType;
}

let globalState: AnimationState | null = null;

function createAnimation(type: AnimType): { tick: () => string } {
  switch (type) {
    case "snake": return new SnakeAnimation();
    case "breakout": return new BreakoutAnimation();
    case "pacman": return new PacManAnimation();
  }
}

function startAnimation(type: AnimType, ctx: ExtensionContext) {
  stopAnimation();
  const state: AnimationState = { intervalId: null, ctx, current: type };
  globalState = state;

  const anim = createAnimation(type);
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

function stopAnimation() {
  if (globalState?.intervalId) {
    clearInterval(globalState.intervalId);
    globalState.intervalId = null;
  }
  globalState = null;
}

// ─── Extension Entry ────────────────────────────────────────────────

export default function (pi: ExtensionAPI) {
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

  pi.registerCommand("snake", {
    description: "Switch animation: /snake <snake|breakout|pacman> or /snake to pick",
    handler: async (ctx: any) => {
      const ui: ExtensionUIContext | null = ctx.ui ?? uiCtx;
      if (!ui) return;

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
