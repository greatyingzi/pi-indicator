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

function toBraille2Line(grid: Set<string>): string {
  const lines: string[] = [];
  for (let half = 0; half < 2; half++) {
    const parts: string[] = [];
    for (let cx = 0; cx < W; cx += 2) {
      let val = 0;
      for (let r = 0; r < 4; r++) {
        for (let c = 0; c < 2; c++) {
          if (grid.has(`${r + half * 4},${cx + c}`)) val |= DOT_MAP[`${r},${c}`];
        }
      }
      parts.push(String.fromCharCode(BRAILLE_OFFSET + val));
    }
    lines.push(parts.join(""));
  }
  return lines.join("\n");
}

function toBrailleColored(colorMap: Map<string, string>): string {
  const parts: string[] = [];
  for (let cx = 0; cx < W; cx += 2) {
    let val = 0;
    let bestColor: string | null = null;
    for (let r = 0; r < H; r++) {
      for (let c = 0; c < 2; c++) {
        const key = `${r},${cx + c}`;
        if (colorMap.has(key)) {
          val |= DOT_MAP[`${r},${c}`];
          if (bestColor === null) bestColor = colorMap.get(key)!;
        }
      }
    }
    if (val === 0) {
      parts.push(" ");
    } else {
      const ch = String.fromCharCode(BRAILLE_OFFSET + val);
      if (bestColor) parts.push(`${bestColor}${ch}${RESET}`);
      else parts.push(ch);
    }
  }
  return parts.join("");
}

function toBraille2LineColored(colorMap: Map<string, string>): string {
  const lines: string[] = [];
  for (let half = 0; half < 2; half++) {
    const parts: string[] = [];
    for (let cx = 0; cx < W; cx += 2) {
      let val = 0;
      let bestColor: string | null = null;
      for (let r = 0; r < 4; r++) {
        for (let c = 0; c < 2; c++) {
          const key = `${r + half * 4},${cx + c}`;
          if (colorMap.has(key)) {
            val |= DOT_MAP[`${r},${c}`];
            if (bestColor === null) bestColor = colorMap.get(key)!;
          }
        }
      }
      if (val === 0) {
        parts.push(" ");
      } else {
        const ch = String.fromCharCode(BRAILLE_OFFSET + val);
        if (bestColor) parts.push(`${bestColor}${ch}${RESET}`);
        else parts.push(ch);
      }
    }
    lines.push(parts.join(""));
  }
  return lines.join("\n");
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

  constructor() {
    this.food = randomFood(this.snake);
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
    } else {
      this.snake.pop();
    }
    const colorMap = new Map<string, string>();
    // Head (bright green)
    colorMap.set(this.snake[0], "\x1b[38;5;118m");
    // Body (green)
    for (let i = 1; i < this.snake.length; i++) {
      colorMap.set(this.snake[i], "\x1b[38;5;34m");
    }
    // Food (red)
    colorMap.set(this.food, "\x1b[38;5;196m");
    return toBrailleColored(colorMap);
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
    const colorMap = new Map<string, string>();
    const brickColors: Record<number, string> = {
      0: "\x1b[38;5;226m",  // yellow
      1: "\x1b[38;5;214m",  // orange
      2: "\x1b[38;5;196m",  // red
      3: "\x1b[38;5;196m",  // red
    };
    // Bricks
    for (const key of this.bricks) {
      const r = parseInt(key.split(",")[0], 10);
      colorMap.set(key, brickColors[r] || "\x1b[38;5;196m");
    }
    // Paddle (white)
    colorMap.set(`${this.paddle},${W - 1}`, "\x1b[38;5;252m");
    colorMap.set(`${this.paddle + 1},${W - 1}`, "\x1b[38;5;252m");
    // Ball (bright cyan)
    colorMap.set(`${Math.round(this.br)},${Math.round(this.bc)}`, "\x1b[38;5;51m");
    return toBrailleColored(colorMap);
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
    const colorMap = new Map<string, string>();
    // Pac-Man (yellow)
    const pacColor = "\x1b[38;5;226m";
    for (const key of this.getPacDots()) colorMap.set(key, pacColor);
    // Dots (cyan)
    const dotColor = "\x1b[38;5;51m";
    for (const d of this.dots) {
      colorMap.set(`2,${d}`, dotColor);
    }

    return toBrailleColored(colorMap);
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
    const colorMap = new Map<string, string>();
    for (let i = 0; i < 8; i++) {
      const h = Math.round(this.heights[i]);
      // Color by height: low=green, mid=yellow, high=red
      const barColor = h <= 2 ? "\x1b[38;5;46m" : h === 3 ? "\x1b[38;5;226m" : "\x1b[38;5;196m";
      for (let row = 0; row < H; row++) {
        // Fill from bottom: row 3 is bottom, row 0 is top
        if (row >= H - h) {
          colorMap.set(`${row},${i * 2}`, barColor);
          colorMap.set(`${row},${i * 2 + 1}`, barColor);
        }
      }
    }

    return toBrailleColored(colorMap);
  }
}

// ─── 5. Invaders Animation (horizontal) ───────────────────────────
// Ship on LEFT (col 0-1), aliens invade from RIGHT
// Ship moves up/down, bullets shoot RIGHT, aliens approach LEFT

class InvadersAnimation {
  private shipRow: number = 2;
  private shipDir: number = 1;
  private shipPause: number = 0;
  private aliens: Set<string> = new Set();
  private alienDir: number = -1;
  private alienTimer: number = 0;
  private alienSpeed: number = 6;
  private bullets: number[][] = []; // [row, col]
  private shootTimer: number = 0;
  private nextShootAt: number = 3;
  private burstCount: number = 0;

  constructor() {
    this.spawnAliens();
  }

  private spawnAliens() {
    this.aliens.clear();
    const numCols = 2 + Math.floor(Math.random() * 3); // 2-4 columns
    const baseCol = W - 1 - Math.floor(Math.random() * 2);
    for (let i = 0; i < numCols; i++) {
      const c = baseCol - i * 2;
      if (c < 4) continue;
      const numRows = 1 + Math.floor(Math.random() * 3); // 1-3 aliens per column
      const startRow = Math.floor(Math.random() * (H - numRows + 1));
      for (let j = 0; j < numRows; j++) {
        this.aliens.add(`${startRow + j},${c}`);
      }
    }
    this.alienSpeed = 5 + Math.floor(Math.random() * 4); // 5-8
    this.alienDir = -1;
  }

  tick(): string {
    this.alienTimer++;
    this.shootTimer++;

    // Ship movement with random pauses and direction changes
    if (this.shipPause > 0) {
      this.shipPause--;
    } else {
      this.shipRow += this.shipDir;
      if (this.shipRow >= H - 1) {
        this.shipDir = -1;
        this.shipPause = Math.floor(Math.random() * 3);
      } else if (this.shipRow <= 0) {
        this.shipDir = 1;
        this.shipPause = Math.floor(Math.random() * 3);
      }
      // Random direction change
      if (Math.random() < 0.1) {
        this.shipDir *= -1;
        this.shipPause = Math.floor(Math.random() * 2);
      }
    }

    // Auto-shoot with randomized interval and occasional burst
    if (this.burstCount > 0) {
      this.burstCount--;
      this.bullets.push([this.shipRow, 2]);
      if (this.burstCount === 0) this.shootTimer = 0;
    } else if (this.shootTimer >= this.nextShootAt) {
      this.shootTimer = 0;
      this.nextShootAt = 2 + Math.floor(Math.random() * 4); // 2-5
      this.bullets.push([this.shipRow, 2]);
      // Chance of burst fire
      if (Math.random() < 0.2) {
        this.burstCount = 1 + Math.floor(Math.random() * 2);
      }
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
    if (this.alienTimer >= this.alienSpeed) {
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
    const colorMap = new Map<string, string>();
    // Ship (green)
    const shipColor = "\x1b[38;5;46m";
    colorMap.set(`${this.shipRow},0`, shipColor);
    colorMap.set(`${this.shipRow},1`, shipColor);
    // Aliens (red)
    const alienColor = "\x1b[38;5;196m";
    for (const key of this.aliens) colorMap.set(key, alienColor);
    // Bullets (yellow)
    const bulletColor = "\x1b[38;5;226m";
    for (const b of this.bullets) {
      if (b[1] >= 0 && b[1] < W) colorMap.set(`${b[0]},${b[1]}`, bulletColor);
    }

    return toBrailleColored(colorMap);
  }
}

// ─── 6. Heart Animation (lub-dub heartbeat, 16x8 two-line) ─────────

const HEART_SMALL = new Set([
  "2,4","2,5","2,9","2,10",
  "3,3","3,4","3,5","3,6","3,7","3,8","3,9","3,10","3,11",
  "4,4","4,5","4,6","4,7","4,8","4,9","4,10",
  "5,5","5,6","5,7","5,8","5,9",
  "6,6","6,7","6,8",
  "7,7",
]);

const HEART_BIG = new Set([
  "1,3","1,4","1,5","1,9","1,10","1,11",
  "2,2","2,3","2,4","2,5","2,6","2,7",
  "2,8","2,9","2,10","2,11","2,12",
  "3,2","3,3","3,4","3,5","3,6","3,7",
  "3,8","3,9","3,10","3,11","3,12",
  "4,3","4,4","4,5","4,6","4,7","4,8","4,9","4,10","4,11",
  "5,4","5,5","5,6","5,7","5,8","5,9","5,10",
  "6,5","6,6","6,7","6,8","6,9",
  "7,6","7,7","7,8",
]);

// lub-dub pattern: rest, beat, rest, beat(smaller), rest...
const HEART_TIMING = [0, 0, 0, 1, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0];
const HEART_FRAMES = [HEART_SMALL, HEART_BIG];

class HeartAnimation {
  private phase = 0;

  tick(): string {
    this.phase++;
    const frameIdx = HEART_TIMING[this.phase % HEART_TIMING.length];
    const pixels = HEART_FRAMES[frameIdx];

    const colorMap = new Map<string, string>();
    // Bright red when beating, darker red when resting
    const heartColor = frameIdx === 1 ? "\x1b[38;5;203m" : "\x1b[38;5;196m";
    for (const key of pixels) colorMap.set(key, heartColor);
    return toBraille2LineColored(colorMap);
  }
}

// ─── 5. Cat Animation (SVG-converted 5-frame pixel, no color) ──

// SVG-converted 5-frame running cat — pure braille, no color
const CAT_FRAMES: Set<string>[] = [
  // Frame 1
  new Set([
    "0,0","0,9","0,10","0,12","0,13","1,0","1,1","1,9","1,10","1,11","1,12","1,13",
    "2,2","2,3","2,4","2,5","2,6","2,7","2,8","2,9","2,10","2,11","2,12","2,13","2,14",
    "3,0","3,1","3,2","3,3","3,4","3,5","3,6","3,7","3,8","3,9","3,10","3,11","3,12","3,13","3,14",
    "4,0","4,1","4,2","4,3","4,4","4,5","4,6","4,7","4,8","4,9","4,10","4,11","4,12","4,13",
    "5,1","5,2","5,3","5,11","5,12","5,13"]),
  // Frame 2
  new Set([
    "0,0","0,9","0,10","0,12","0,13","1,0","1,1","1,9","1,10","1,11","1,12","1,13",
    "2,2","2,3","2,4","2,5","2,6","2,7","2,8","2,9","2,10","2,11","2,12","2,13","2,14",
    "3,0","3,1","3,2","3,3","3,4","3,5","3,6","3,7","3,8","3,9","3,10","3,11","3,12","3,13","3,14",
    "4,0","4,1","4,2","4,3","4,4","4,5","4,6","4,7","4,8","4,9","4,10","4,11","4,12","4,13",
    "5,3","5,4","5,10","5,11"]),
  // Frame 3
  new Set([
    "0,0","0,9","0,10","0,12","0,13","1,0","1,1","1,9","1,10","1,11","1,12","1,13",
    "2,2","2,3","2,4","2,5","2,6","2,7","2,8","2,9","2,10","2,11","2,12","2,13","2,14",
    "3,0","3,1","3,2","3,3","3,4","3,5","3,6","3,7","3,8","3,9","3,10","3,11","3,12","3,13","3,14",
    "4,0","4,1","4,2","4,3","4,4","4,5","4,6","4,7","4,8","4,9","4,10","4,11","4,12","4,13",
    "5,2","5,3","5,5","5,6","5,7","5,12"]),
  // Frame 4
  new Set([
    "0,0","0,9","0,10","0,12","0,13","1,0","1,1","1,9","1,10","1,11","1,12","1,13",
    "2,2","2,3","2,4","2,5","2,6","2,7","2,8","2,9","2,10","2,11","2,12","2,13","2,14",
    "3,0","3,1","3,2","3,3","3,4","3,5","3,6","3,7","3,8","3,9","3,10","3,11","3,12","3,13","3,14",
    "4,0","4,1","4,2","4,3","4,4","4,5","4,6","4,7","4,8","4,9","4,10","4,11","4,12","4,13",
    "5,4","5,5","5,9","5,10"]),
  // Frame 5
  new Set([
    "0,0","0,9","0,10","0,12","0,13","1,0","1,1","1,9","1,10","1,11","1,12","1,13",
    "2,2","2,3","2,4","2,5","2,6","2,7","2,8","2,9","2,10","2,11","2,12","2,13","2,14",
    "3,0","3,1","3,2","3,3","3,4","3,5","3,6","3,7","3,8","3,9","3,10","3,11","3,12","3,13","3,14",
    "4,0","4,1","4,2","4,3","4,4","4,5","4,6","4,7","4,8","4,9","4,10","4,11","4,12","4,13",
    "5,2","5,3","5,11","5,12"]),
];

class CatAnimation {
  private frameIdx = 0;

  tick(): string {
    this.frameIdx = (this.frameIdx + 1) % CAT_FRAMES.length;
    const pixels = CAT_FRAMES[this.frameIdx];

    const colorMap = new Map<string, string>();
    const catColor = "\x1b[38;5;226m";
    for (const key of pixels) colorMap.set(key, catColor);
    return toBraille2LineColored(colorMap);
  }
}

// ─── 7. Racer Animation (Road Fighter, 2-lane, colored, 16x8) ──────

const RACER_PLAYER_MIN_COL = 1;
const RACER_PLAYER_MAX_COL = 4;
const RACER_MAX_NPCS = 2;
const RACER_PLAYER_COLOR = "\x1b[38;5;82m";

// NPC type definitions: speed, template key, ANSI 256 color
const RACER_NPC_DEFS: Record<string, { speed: number; tmpl: string; color: number }> = {
  gray:   { speed: 0.3, tmpl: "small",    color: 244 },
  blue:   { speed: 0.5, tmpl: "standard", color: 69 },
  yellow: { speed: 0.7, tmpl: "standard", color: 226 },
  red:    { speed: 0.8, tmpl: "standard", color: 196 },
  truck:  { speed: 0.2, tmpl: "truck",    color: 240 },
};

// Spawn weights: [type, weight]
const RACER_SPAWN_EARLY: [string, number][] = [["gray",40],["blue",25],["yellow",15],["red",10],["truck",10]];
const RACER_SPAWN_LATE:  [string, number][] = [["gray",15],["blue",20],["yellow",25],["red",30],["truck",10]];

// Car pixel templates (row,col) — all symmetric so no mirror needed
const RACER_CAR_TEMPLATES: Record<string, ReadonlySet<string>> = {
  small:    new Set(["0,0","0,1","0,2","1,0","1,1","1,2"]),
  standard: new Set(["0,1","0,2","1,0","1,1","1,2","1,3"]),
  truck:    new Set(["0,1","0,2","0,3","0,4","1,0","1,1","1,2","1,3","1,4","1,5"]),
};
const RACER_CAR_WIDTHS: Record<string, number> = { small: 3, standard: 4, truck: 6 };

// Explosion frames: expanding then fading cross pattern
const EXPLODE_FRAMES: ReadonlyArray<ReadonlySet<string>> = [
  new Set(["0,0","0,1","0,2","1,0","1,1","1,2","2,0","2,1","2,2"]),
  new Set(["0,0","0,2","1,1","2,0","2,2"]),
  new Set(["0,0","0,2","1,1","2,0","2,2"]),
  new Set(["1,1"]),
];
const EXPLODE_COLOR = "\x1b[38;5;202m"; // orange-red

function racerLaneOff(lane: number): number {
  return (lane === 0 ? 0 : 4) + 1;
}

interface RacerNPCData {
  lane: number;
  col: number;
  speed: number;
  color: string;
  npcType: string;
  tmplKey: string;
  accumulator: number;
  weaveTimer: number;
  weaveInterval: number;
  chaseCooldown: number;
}

class RacerAnimation {
  private playerLane = 0;
  private playerCol = 2;
  private npcs: RacerNPCData[] = [];
  private spawnTimer = 12; // start near interval so first NPC appears quickly
  private ticks = 0;
  private exploding = 0;   // frames remaining for explosion
  private explodeCol = 0;  // explosion column

  private difficulty(): number {
    return Math.min(this.ticks / 500, 1.0);
  }

  private npcWidth(npc: RacerNPCData): number {
    return RACER_CAR_WIDTHS[npc.tmplKey];
  }

  private canSwitchLane(npc: RacerNPCData, targetLane: number): boolean {
    const colI = Math.round(npc.col);
    const nw = this.npcWidth(npc);
    for (const other of this.npcs) {
      if (other === npc) continue;
      if (other.lane !== targetLane) continue;
      const oc = Math.round(other.col);
      const ow = this.npcWidth(other);
      // need at least 4 cols gap between edges
      if (!(colI + nw + 4 <= oc || oc + ow + 4 <= colI)) return false;
    }
    return true;
  }

  private pickNpcType(): string {
    const diff = this.difficulty();
    const lateDict = new Map<string, number>(RACER_SPAWN_LATE);
    const weights: Record<string, number> = {};
    for (const [name, earlyW] of RACER_SPAWN_EARLY) {
      const lateW = lateDict.get(name)!;
      weights[name] = earlyW + (lateW - earlyW) * diff;
    }
    const total = Object.values(weights).reduce((a, b) => a + b, 0);
    let r = Math.random() * total;
    for (const [name, w] of Object.entries(weights)) {
      r -= w;
      if (r <= 0) return name;
    }
    return "gray";
  }

  private spawnNPC(): void {
    const lane = Math.floor(Math.random() * 2);
    // keep gap in the same lane
    if (this.npcs.some(n => n.lane === lane && n.col >= W - 10)) return;
    const npcType = this.pickNpcType();
    // Also check spacing to avoid spawning on top of same-lane NPCs
    const newW = RACER_CAR_WIDTHS[RACER_NPC_DEFS[npcType].tmpl];
    for (const npc of this.npcs) {
      if (npc.lane !== lane) continue;
      const nw = this.npcWidth(npc);
      const oc = Math.round(npc.col);
      // Ensure new NPC at col W+1 doesn't overlap
      if (!(W + 1 + newW + 2 <= oc || oc + nw + 2 <= W + 1)) return;
    }
    const def = RACER_NPC_DEFS[npcType];
    this.npcs.push({
      lane, col: W + 1,
      speed: def.speed,
      color: `\x1b[38;5;${def.color}m`,
      npcType, tmplKey: def.tmpl,
      accumulator: 0,
      weaveTimer: 0,
      weaveInterval: 3 + Math.floor(Math.random() * 3),
      chaseCooldown: 0,
    });
  }

  tick(): string {
    this.ticks++;

    // ── Explosion phase ──
    if (this.exploding > 0) {
      this.exploding--;
      const colorMap = new Map<string, string>();
      let frameIdx = EXPLODE_FRAMES.length - 1 - this.exploding;
      if (frameIdx < 0) frameIdx = 0;
      if (frameIdx >= EXPLODE_FRAMES.length) frameIdx = EXPLODE_FRAMES.length - 1;
      const pattern = EXPLODE_FRAMES[frameIdx];
      const pOff = racerLaneOff(this.playerLane);
      for (const k of pattern) {
        const [r, c] = k.split(",").map(Number);
        const ac = this.explodeCol + c;
        if (ac >= 0 && ac < W) {
          colorMap.set(`${r + pOff},${ac}`, EXPLODE_COLOR);
        }
      }
      return this.render(colorMap);
    }

    const diff = this.difficulty();
    const pc = this.playerCol;
    const pw = RACER_CAR_WIDTHS["standard"];

    // ── Spawn ──
    this.spawnTimer++;
    const baseInterval = Math.max(12, 22 - Math.floor(diff * 8));
    if (this.spawnTimer >= baseInterval && this.npcs.length < RACER_MAX_NPCS) {
      this.spawnTimer = 0;
      this.spawnNPC();
    }

    // ── Move NPCs (sub-pixel accumulator) ──
    for (const npc of this.npcs) {
      npc.accumulator += npc.speed;
      while (npc.accumulator >= 1.0) {
        npc.col -= 1;
        npc.accumulator -= 1.0;
      }
    }

    // ── NPC AI (per-type behaviour, with lane-switch safety) ──
    for (const npc of this.npcs) {
      let targetLane: number | null = null;

      if (npc.npcType === "blue") {
        // Dodge: player approaching in same lane → switch lane
        const colI = Math.round(npc.col);
        if (npc.lane === this.playerLane) {
          const dist = colI - (pc + pw);
          if (dist >= 0 && dist < 6) {
            targetLane = 1 - npc.lane;
          }
        }
      } else if (npc.npcType === "yellow") {
        // Weaver: periodically auto-switch lanes (S-curve)
        npc.weaveTimer++;
        if (npc.weaveTimer >= npc.weaveInterval) {
          npc.weaveTimer = 0;
          npc.weaveInterval = 3 + Math.floor(Math.random() * 3);
          targetLane = 1 - npc.lane;
        }
      } else if (npc.npcType === "red") {
        // Chaser: actively track the player's lane
        if (npc.chaseCooldown > 0) npc.chaseCooldown--;
        if (npc.lane !== this.playerLane && npc.chaseCooldown === 0) {
          targetLane = this.playerLane;
        }
      }

      // Execute lane switch only if safe
      if (targetLane !== null && this.canSwitchLane(npc, targetLane)) {
        npc.lane = targetLane;
        if (npc.npcType === "red") npc.chaseCooldown = 5;
      }
      // gray & truck: straight line, never change lane
    }

    // ── NPC-NPC proximity: push apart if too close ──
    for (let i = 0; i < this.npcs.length; i++) {
      const npc = this.npcs[i];
      const colI = Math.round(npc.col);
      const nw = this.npcWidth(npc);
      for (let j = 0; j < this.npcs.length; j++) {
        if (i >= j) continue;
        const other = this.npcs[j];
        if (other.lane !== npc.lane) continue;
        const oc = Math.round(other.col);
        const ow = this.npcWidth(other);
        // Check overlap (no gap needed, just direct overlap)
        if (!(colI + nw <= oc || oc + ow <= colI)) {
          // Push the one that's further right to the other lane
          if (npc.col > other.col) {
            const otherLane = 1 - npc.lane;
            if (this.canSwitchLane(npc, otherLane)) npc.lane = otherLane;
          } else {
            const otherLane = 1 - other.lane;
            if (this.canSwitchLane(other, otherLane)) other.lane = otherLane;
          }
        }
      }
    }

    // ── Remove off-screen ──
    this.npcs = this.npcs.filter(n => n.col > -(RACER_CAR_WIDTHS[n.tmplKey] + 2));

    // ── Collision check FIRST (before player AI moves) ──
    const colPOff = racerLaneOff(this.playerLane);
    const colPlayerSet = new Set<string>();
    for (const k of RACER_CAR_TEMPLATES["standard"]) {
      const [r, c] = k.split(",").map(Number);
      colPlayerSet.add(`${r + colPOff},${pc + c}`);
    }

    let colHit: RacerNPCData | null = null;
    for (const npc of this.npcs) {
      const nOff = racerLaneOff(npc.lane);
      const colI = Math.round(npc.col);
      for (const k of RACER_CAR_TEMPLATES[npc.tmplKey]) {
        const [r, c] = k.split(",").map(Number);
        if (colPlayerSet.has(`${r + nOff},${colI + c}`)) { colHit = npc; break; }
      }
      if (colHit) break;
    }

    if (colHit) {
      this.npcs = this.npcs.filter(n => n !== colHit);
      this.exploding = EXPLODE_FRAMES.length; // 4 frames
      this.explodeCol = Math.round(colHit.col);
    }

    // ── Player AI: lane + column positioning via eval_position ──

    const evalPosition = (lane: number, col: number): number => {
      let score = 0;
      for (const npc of this.npcs) {
        const colI = Math.round(npc.col);
        const nw = RACER_CAR_WIDTHS[npc.tmplKey];
        const gap = colI - (col + pw);
        if (gap < 0) {
          const overlapPenalty = Math.abs(gap) + 1;
          if (npc.lane === lane) {
            score -= 50 * overlapPenalty;
          } else {
            score -= 5;
          }
        } else {
          if (npc.lane === lane) {
            score += gap;
            if (npc.npcType === "red") score -= 4;
            else if (npc.npcType === "yellow") score -= 2;
          } else {
            score += 2;
          }
        }
      }
      if (col > 3) score -= 1;
      if (col < 1) score -= 1;
      return score;
    };

    let bestLane = this.playerLane;
    let bestCol = this.playerCol;
    let bestScore = evalPosition(this.playerLane, this.playerCol);

    for (const lane of [0, 1]) {
      for (let col = RACER_PLAYER_MIN_COL; col <= RACER_PLAYER_MAX_COL; col++) {
        let overlap = false;
        for (const npc of this.npcs) {
          if (npc.lane !== lane) continue;
          const ci = Math.round(npc.col);
          const nw = RACER_CAR_WIDTHS[npc.tmplKey];
          if (!(ci + nw <= col || ci >= col + pw)) { overlap = true; break; }
        }
        if (overlap) continue;

        let s = evalPosition(lane, col);
        if (lane === this.playerLane) s += 0.5;
        if (col === this.playerCol) s += 0.3;

        if (s > bestScore) {
          bestScore = s;
          bestLane = lane;
          bestCol = col;
        }
      }
    }

    // Apply: lane switches instantly, col moves 1 step per frame
    this.playerLane = bestLane;
    if (this.playerCol < bestCol) this.playerCol += 1;
    else if (this.playerCol > bestCol) this.playerCol -= 1;

    // ── Render ──
    const colorMap = new Map<string, string>();

    // Player pixels (green)
    const pOff2 = racerLaneOff(this.playerLane);
    for (const k of RACER_CAR_TEMPLATES["standard"]) {
      const [r, c] = k.split(",").map(Number);
      const ac = pc + c;
      if (ac >= 0 && ac < W) colorMap.set(`${r + pOff2},${ac}`, RACER_PLAYER_COLOR);
    }

    // NPC pixels
    for (const npc of this.npcs) {
      const off = racerLaneOff(npc.lane);
      const colI = Math.round(npc.col);
      for (const k of RACER_CAR_TEMPLATES[npc.tmplKey]) {
        const [r, c] = k.split(",").map(Number);
        const ac = colI + c;
        if (ac >= 0 && ac < W) colorMap.set(`${r + off},${ac}`, npc.color);
      }
    }

    return this.render(colorMap);
  }

  private render(colorMap: Map<string, string>): string {
    const lines: string[] = [];
    for (let half = 0; half < 2; half++) {
      const parts: string[] = [];
      for (let cx = 0; cx < W; cx += 2) {
        let val = 0;
        let bestColor: string | null = null;
        for (let r = 0; r < 4; r++) {
          for (let c = 0; c < 2; c++) {
            const key = `${r + half * 4},${cx + c}`;
            if (colorMap.has(key)) {
              val |= DOT_MAP[`${r},${c}`];
              if (bestColor === null) bestColor = colorMap.get(key)!;
            }
          }
        }
        if (val === 0) {
          parts.push(" ");
        } else {
          const ch = String.fromCharCode(BRAILLE_OFFSET + val);
          if (bestColor) parts.push(`${bestColor}${ch}${RESET}`);
          else parts.push(ch);
        }
      }
      lines.push(parts.join(""));
    }
    return lines.join("\n");
  }
}

// ─── Animation Engine ───────────────────────────────────────────────

type AnimType = "snake" | "breakout" | "pacman" | "equalizer" | "invaders" | "heart" | "cat"; // | "racer" TODO rework

const ANIM_LIST: { id: AnimType; label: string }[] = [
  { id: "snake", label: "Snake 🐍" },
  { id: "breakout", label: "Breakout 🧱" },
  { id: "pacman", label: "Pac-Man 👾" },
  { id: "equalizer", label: "Equalizer 📊" },
  { id: "invaders", label: "Invaders 🛸" },
  { id: "heart", label: "Heart ❤️" },
  { id: "cat", label: "Cat 🐱" },
  // { id: "racer", label: "Racer 🏎️" },  // TODO: rework
];

const ANIM_INTERVALS: Record<AnimType, number> = {
  snake: 120,
  breakout: 100,
  pacman: 140,
  equalizer: 150,
  invaders: 120,
  heart: 200,
  cat: 160,
  // racer: 120,
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
    case "heart": return new HeartAnimation();
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
      ui.notify(`Switched to ${selected.label}`);
    }
  };

  pi.registerCommand("indicator", {
    description: "Switch animation: /indicator [snake|breakout|pacman|equalizer|invaders|heart|cat]",
    handler: cmdHandler,
  });
}
