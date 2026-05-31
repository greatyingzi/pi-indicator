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
// Pac-Man drawn as dot-art shape (5×4), mouth opens/closes.
// Dots float in from the right, one at a time, spaced out.

class PacManAnimation {
  private mouthOpen: boolean = true;
  private mouthPhase: number = 0;
  private dots: number[] = []; // column positions of dots
  private spawnTimer: number = 0;

  // Pac-Man side view facing right, col 0-3
  // Open mouth:  ··██████ / ████···· / ████···· / ··██████
  // Closed:      ··██···· / ████··██ / ████··██ / ··████··
  private getPacDots(): Set<string> {
    const s = new Set<string>();
    // Col 0: rows 1,2 (always)
    s.add("1,0"); s.add("2,0");

    if (this.mouthOpen) {
      // Col 1,2,3: rows 0,3 only (top and bottom jaw edges)
      s.add("0,1"); s.add("3,1");
      s.add("0,2"); s.add("3,2");
      s.add("0,3"); s.add("3,3");
    } else {
      // Col 1,2: all 4 rows (full body)
      s.add("0,1"); s.add("1,1"); s.add("2,1"); s.add("3,1");
      s.add("0,2"); s.add("1,2"); s.add("2,2"); s.add("3,2");
      // Col 3: rows 1,2
      s.add("1,3"); s.add("2,3");
    }
    return s;
  }

  tick(): string {
    this.mouthPhase++;
    if (this.mouthPhase % 3 === 0) this.mouthOpen = !this.mouthOpen;
    this.spawnTimer++;

    // Spawn a dot every 6 ticks — sparse
    if (this.spawnTimer >= 6) {
      this.spawnTimer = 0;
      this.dots.push(W - 1);
    }

    // Move dots left
    for (let i = 0; i < this.dots.length; i++) {
      this.dots[i]--;
    }

    // Remove dots eaten (col 4 = pac-man front) or past
    this.dots = this.dots.filter(d => d > 4);

    // Render
    const grid = new Set<string>();
    const pacDots = this.getPacDots();

    // Pac-Man
    for (const key of pacDots) grid.add(key);

    // Dots at row 2 (middle)
    for (const d of this.dots) {
      grid.add(`2,${d}`);
    }

    // Color rendering
    const PAC_COLOR = "\x1b[38;5;226m"; // yellow
    const DOT_COLOR = "\x1b[38;5;51m";  // cyan

    const parts: string[] = [];
    for (let cx = 0; cx < W; cx += 2) {
      let val = 0, pacVal = 0, dotVal = 0;
      let hasPac = false, hasDot = false;

      for (let r = 0; r < H; r++) {
        for (let c = 0; c < 2; c++) {
          const gk = `${r},${cx + c}`;
          const lk = `${r},${c}`;
          if (grid.has(gk)) val |= DOT_MAP[lk];
          if (pacDots.has(gk)) { pacVal |= DOT_MAP[lk]; hasPac = true; }
          if (grid.has(gk) && !pacDots.has(gk)) { dotVal |= DOT_MAP[lk]; hasDot = true; }
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

// ─── 4. Equalizer Animation ───────────────────────────────────────

class EqualizerAnimation {
  private heights: number[] = new Array(8).fill(0);
  private targets: number[];
  private targetTimer: number = 0;

  constructor() {
    this.targets = Array.from({ length: 8 }, () => Math.floor(Math.random() * 5));
  }

  tick(): string {
    this.targetTimer++;
    if (this.targetTimer >= 8) {
      this.targetTimer = 0;
      for (let i = 0; i < 8; i++) {
        this.targets[i] = Math.floor(Math.random() * 5);
      }
    }

    // Smooth interpolation toward targets
    for (let i = 0; i < 8; i++) {
      const diff = this.targets[i] - this.heights[i];
      this.heights[i] += diff * 0.25;
    }

    // Render
    const grid = new Set<string>();
    for (let i = 0; i < 8; i++) {
      const h = Math.round(this.heights[i]);
      for (let row = 0; row < H; row++) {
        // Fill from bottom: row 3 is bottom, row 0 is top
        if (row >= H - h) {
          grid.add(`${row},${i * 2}`);
          grid.add(`${row},${i * 2 + 1}`);
        }
      }
    }

    return toBraille(grid);
  }
}

// ─── 5. Invaders Animation (horizontal) ───────────────────────────
// Ship on LEFT (col 0-1), aliens invade from RIGHT
// Ship moves up/down, bullets shoot RIGHT, aliens approach LEFT

class InvadersAnimation {
  private shipRow: number = 2;
  private shipDir: number = 1;
  private aliens: Set<string> = new Set();
  private alienDir: number = -1;
  private alienTimer: number = 0;
  private bullets: number[][] = []; // [row, col]
  private shootTimer: number = 0;

  constructor() {
    this.spawnAliens();
  }

  private spawnAliens() {
    this.aliens.clear();
    for (let r = 0; r < 4; r++) {
      this.aliens.add(`${r},${W - 1}`);
      this.aliens.add(`${r},${W - 2}`);
      this.aliens.add(`${r},${W - 4}`);
      this.aliens.add(`${r},${W - 5}`);
    }
  }

  tick(): string {
    this.alienTimer++;
    this.shootTimer++;

    // Ship moves up/down
    this.shipRow += this.shipDir;
    if (this.shipRow >= H - 1) this.shipDir = -1;
    else if (this.shipRow <= 0) this.shipDir = 1;

    // Auto-shoot right
    if (this.shootTimer >= 3) {
      this.shootTimer = 0;
      this.bullets.push([this.shipRow, 2]);
    }

    // Move bullets right
    const newBullets: number[][] = [];
    for (const b of this.bullets) {
      b[1]++;
      if (b[1] < W) {
        const key = `${b[0]},${b[1]}`;
        if (this.aliens.has(key)) {
          this.aliens.delete(key);
        } else {
          newBullets.push(b);
        }
      }
    }
    this.bullets = newBullets;

    // Move aliens
    if (this.alienTimer >= 6) {
      this.alienTimer = 0;
      if (this.aliens.size > 0) {
        let minC = W, maxC = 0;
        for (const key of this.aliens) {
          const c = parseInt(key.split(",")[1], 10);
          if (c < minC) minC = c;
          if (c > maxC) maxC = c;
        }

        const newAliens = new Set<string>();
        let shiftV = false;

        if (this.alienDir < 0 && minC <= 4) {
          this.alienDir = 1;
          shiftV = true;
        } else if (this.alienDir > 0 && maxC >= W - 1) {
          this.alienDir = -1;
          shiftV = true;
        }

        for (const key of this.aliens) {
          const parts = key.split(",");
          let r = parseInt(parts[0], 10);
          let c = parseInt(parts[1], 10);
          if (shiftV) r++;
          else c += this.alienDir;
          if (r >= 0 && r < H && c >= 0 && c < W) {
            newAliens.add(`${r},${c}`);
          }
        }
        this.aliens = newAliens;
      }

      if (this.aliens.size === 0 || [...this.aliens].some(k => parseInt(k.split(",")[0], 10) >= H)) {
        this.spawnAliens();
      }
    }

    // Render
    const SHIP_COLOR = "\x1b[38;5;46m";
    const ALIEN_COLOR = "\x1b[38;5;196m";
    const BULLET_COLOR = "\x1b[38;5;226m";

    const shipDots = new Set<string>([`${this.shipRow},0`, `${this.shipRow},1`]);
    const alienDots = new Set<string>(this.aliens);
    const bulletDots = new Set<string>();
    for (const b of this.bullets) {
      if (b[1] >= 0 && b[1] < W) bulletDots.add(`${b[0]},${b[1]}`);
    }

    const parts: string[] = [];
    for (let cx = 0; cx < W; cx += 2) {
      let val = 0;
      let hasShip = false, hasAlien = false, hasBullet = false;
      for (let r = 0; r < H; r++) {
        for (let c = 0; c < 2; c++) {
          const gk = `${r},${cx + c}`;
          if (shipDots.has(gk) || alienDots.has(gk) || bulletDots.has(gk)) {
            val |= DOT_MAP[`${r},${c}`];
          }
          if (shipDots.has(gk)) hasShip = true;
          if (alienDots.has(gk)) hasAlien = true;
          if (bulletDots.has(gk)) hasBullet = true;
        }
      }
      const ch = String.fromCharCode(BRAILLE_OFFSET + val);
      if (val === 0) {
        parts.push(EMPTY_BRAILLE);
      } else if (hasAlien && !hasShip && !hasBullet) {
        parts.push(`${ALIEN_COLOR}${ch}${RESET}`);
      } else if (hasBullet && !hasShip && !hasAlien) {
        parts.push(`${BULLET_COLOR}${ch}${RESET}`);
      } else if (hasShip) {
        parts.push(`${SHIP_COLOR}${ch}${RESET}`);
      } else {
        parts.push(ch);
      }
    }
    return parts.join("");
  }
}

// ─── 5. Cat Animation (SVG-converted 5-frame pixel, three-color) ──

const CAT_YELLOW = "\x1b[38;5;226m";
const CAT_CYAN   = "\x1b[38;5;51m";
const CAT_PINK   = "\x1b[38;5;213m";

interface CatFrame {
  body: Set<string>;
  eye: Set<string>;
  nose: Set<string>;
}

// SVG-converted 5-frame running cat — yellow body, cyan eye, pink nose
const CAT_FRAMES: CatFrame[] = [
  // Frame 1
  { body: new Set([
    "0,2","0,3","0,4","0,9","0,10","0,12","0,13",
    "1,1","1,2","1,3","1,8","1,9","1,10","1,11","1,12","1,13","1,14",
    "2,1","2,2","2,3","2,4","2,5","2,6","2,7","2,8","2,9","2,10","2,11","2,13","2,14",
    "3,1","3,2","3,3","3,4","3,5","3,6","3,7","3,8","3,9","3,10","3,12",
    "4,1","4,2","4,3","4,4","4,5","4,6","4,7","4,9","4,10","4,11",
    "5,1","5,2","5,3","5,4","5,5","5,6","5,9"]),
    eye: new Set(["2,12"]),
    nose: new Set(["3,11"]) },
  // Frame 2
  { body: new Set([
    "0,9","0,10","0,12","0,13",
    "1,1","1,2","1,8","1,9","1,10","1,11","1,12","1,13","1,14",
    "2,1","2,2","2,3","2,4","2,5","2,6","2,7","2,8","2,9","2,10","2,11","2,13","2,14",
    "3,2","3,3","3,4","3,5","3,6","3,7","3,8","3,9","3,10","3,12","3,13",
    "4,1","4,2","4,3","4,4","4,5","4,6","4,7","4,8","4,9","4,12","4,13","4,14",
    "5,4","5,5"]),
    eye: new Set(["2,12"]),
    nose: new Set(["3,11"]) },
  // Frame 3
  { body: new Set([
    "0,1","0,9","0,10","0,12","0,13",
    "1,1","1,2","1,9","1,10","1,11","1,12","1,13","1,14",
    "2,2","2,3","2,4","2,5","2,6","2,7","2,8","2,9","2,10","2,11","2,13","2,14",
    "3,1","3,2","3,3","3,4","3,5","3,6","3,7","3,8","3,9","3,10","3,12","3,13","3,14",
    "4,1","4,2","4,3","4,4","4,5","4,6","4,7","4,8","4,9","4,10","4,11","4,12","4,13",
    "5,2","5,3","5,4","5,11","5,12","5,13","5,14"]),
    eye: new Set(["2,12"]),
    nose: new Set(["3,11"]) },
  // Frame 4
  { body: new Set([
    "0,1","0,2",
    "1,2","1,3","1,9","1,10","1,11","1,12","1,13","1,14",
    "2,2","2,3","2,4","2,5","2,6","2,7","2,8","2,9","2,10","2,11","2,13","2,14",
    "3,1","3,2","3,3","3,4","3,5","3,6","3,7","3,8","3,9","3,10","3,12","3,13","3,14",
    "4,1","4,2","4,3","4,4","4,5","4,6","4,7","4,8","4,9","4,10","4,11","4,12","4,13",
    "5,2","5,3","5,11","5,12","5,13"]),
    eye: new Set(["2,12"]),
    nose: new Set(["3,11"]) },
  // Frame 5
  { body: new Set([
    "0,1","0,2",
    "1,1","1,2","1,4","1,5","1,6","1,10","1,11","1,12","1,13","1,14",
    "2,1","2,2","2,3","2,4","2,5","2,6","2,7","2,8","2,9","2,10","2,11","2,13","2,14",
    "3,1","3,2","3,3","3,4","3,5","3,6","3,7","3,8","3,9","3,10","3,12","3,13","3,14",
    "4,2","4,3","4,4","4,5","4,6","4,7","4,8","4,9","4,10","4,11","4,12",
    "5,5","5,6","5,10","5,11"]),
    eye: new Set(["2,12"]),
    nose: new Set(["3,11"]) },
];

class CatAnimation {
  private frameIdx = 0;

  tick(): string {
    this.frameIdx = (this.frameIdx + 1) % CAT_FRAMES.length;
    const { body, eye, nose } = CAT_FRAMES[this.frameIdx];

    const lines: string[] = [];
    for (let half = 0; half < 2; half++) {
      const parts: string[] = [];
      for (let cx = 0; cx < W; cx += 2) {
        let val = 0;
        let hasEye = false;
        let hasNose = false;
        for (let r = 0; r < 4; r++) {
          for (let c = 0; c < 2; c++) {
            const gk = `${r + half * 4},${cx + c}`;
            if (body.has(gk) || eye.has(gk) || nose.has(gk)) {
              val |= DOT_MAP[`${r},${c}`];
            }
            if (eye.has(gk)) hasEye = true;
            if (nose.has(gk)) hasNose = true;
          }
        }
        const ch = String.fromCharCode(BRAILLE_OFFSET + val);
        if (val === 0) parts.push(EMPTY_BRAILLE);
        else if (hasEye) parts.push(`${CAT_CYAN}${ch}${RESET}`);
        else if (hasNose) parts.push(`${CAT_PINK}${ch}${RESET}`);
        else parts.push(`${CAT_YELLOW}${ch}${RESET}`);
      }
      lines.push(parts.join(""));
    }
    return lines.join("\n");
  }
}

// ─── Animation Engine ───────────────────────────────────────────────

type AnimType = "snake" | "breakout" | "pacman" | "equalizer" | "invaders" | "cat";

const ANIM_LIST: { id: AnimType; label: string }[] = [
  { id: "snake", label: "Snake 🐍" },
  { id: "breakout", label: "Breakout 🧱" },
  { id: "pacman", label: "Pac-Man 👾" },
  { id: "equalizer", label: "Equalizer 📊" },
  { id: "invaders", label: "Invaders 🛸" },
  { id: "cat", label: "Cat 🐱" },
];

const ANIM_INTERVALS: Record<AnimType, number> = {
  snake: 120,
  breakout: 100,
  pacman: 140,
  equalizer: 150,
  invaders: 120,
  cat: 160,
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
    case "equalizer": return new EqualizerAnimation();
    case "invaders": return new InvadersAnimation();
    case "cat": return new CatAnimation();
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

// ─── Persistence ────────────────────────────────────────────────────
// Save/load the user's preferred animation to ~/.pi/snake-anim

import { readFileSync, writeFileSync, mkdirSync } from "fs";
import { join } from "path";
import { homedir } from "os";

const PREF_DIR = join(homedir(), ".pi");
const PREF_FILE = join(PREF_DIR, "snake-anim");

function loadPref(): AnimType {
  try {
    const val = readFileSync(PREF_FILE, "utf8").trim();
    if ((ANIM_LIST as { id: string }[]).some(a => a.id === val)) return val as AnimType;
  } catch {}
  return "snake";
}

function savePref(type: AnimType) {
  try {
    mkdirSync(PREF_DIR, { recursive: true });
    writeFileSync(PREF_FILE, type);
  } catch {}
}

// ─── Extension Entry ────────────────────────────────────────────────

export default function (pi: ExtensionAPI) {
  let uiCtx: ExtensionUIContext | null = null;

  pi.on("session_start", async (_event, ctx) => {
    if (!ctx.hasUI) return;
    uiCtx = ctx.ui;
    startAnimation(loadPref(), ctx);
  });

  pi.on("session_shutdown", async () => {
    stopAnimation();
    uiCtx = null;
  });

  const cmdHandler = async (ctx: any) => {
    const ui: ExtensionUIContext | null = ctx.ui ?? uiCtx;
    if (!ui) return;

    const args: string | undefined = ctx.args;
    if (args) {
      const target = args.trim().toLowerCase();
      const found = ANIM_LIST.find(a => a.id === target);
      if (found) {
        stopAnimation();
        startAnimation(found.id, { ui, hasUI: true, signal: undefined } as any);
        savePref(found.id);
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
      savePref(selected.id);
    }
  };

  const cmdDesc = "Switch animation: /indicator <snake|breakout|pacman|equalizer|invaders> or /anim to pick";
  pi.registerCommand("indicator", { description: cmdDesc, handler: cmdHandler });
  pi.registerCommand("anim", { description: cmdDesc, handler: cmdHandler });
}
