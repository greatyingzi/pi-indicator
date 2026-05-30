import type {
  ExtensionAPI,
  ExtensionContext,
  WorkingIndicatorOptions,
} from "@earendil-works/pi-coding-agent";

// Real-time Snake game on 8x4 braille grid with colored food
// Runs dynamically via setInterval — no pre-generated frames

const DOT_MAP: Record<string, number> = {
  "0,0": 0x01, "1,0": 0x02, "2,0": 0x04, "3,0": 0x40,
  "0,1": 0x08, "1,1": 0x10, "2,1": 0x20, "3,1": 0x80,
};

const W = 8, H = 4;
const DIRS = [[0,1],[0,-1],[1,0],[-1,0]];

// ANSI 256-color palette for food (bright, vivid colors)
const FOOD_COLORS = [
  "\x1b[38;5;196m", // bright red 🍎
  "\x1b[38;5;226m", // yellow 🍋
  "\x1b[38;5;46m",  // green 🍏
  "\x1b[38;5;213m", // pink 🍑
  "\x1b[38;5;214m", // orange 🍊
  "\x1b[38;5;129m", // purple 🍇
  "\x1b[38;5;51m",  // cyan 🫐
];
const RESET = "\x1b[0m";

function toBraille(grid: Set<string>): string {
  const chars: string[] = [];
  for (let cx = 0; cx < W; cx += 2) {
    let val = 0;
    for (let r = 0; r < H; r++) {
      for (let c = 0; c < 2; c++) {
        if (grid.has(`${r},${cx + c}`)) {
          val |= DOT_MAP[`${r},${c}`];
        }
      }
    }
    chars.push(String.fromCharCode(0x2800 + val));
  }
  return chars.join("");
}

function toBrailleColored(snakeGrid: Set<string>, food: string, colorIdx: number): string {
  const [foodR, foodC] = food.split(",").map(Number);
  const foodCharIdx = Math.floor(foodC / 2); // which braille char contains the food
  const color = FOOD_COLORS[colorIdx % FOOD_COLORS.length];

  const parts: string[] = [];
  for (let cx = 0; cx < W; cx += 2) {
    let val = 0;
    for (let r = 0; r < H; r++) {
      for (let c = 0; c < 2; c++) {
        if (snakeGrid.has(`${r},${cx + c}`)) {
          val |= DOT_MAP[`${r},${c}`];
        }
      }
    }
    const ch = String.fromCharCode(0x2800 + val);
    const charIdx = Math.floor(cx / 2);
    if (charIdx === foodCharIdx) {
      parts.push(`${color}${ch}${RESET}`);
    } else {
      parts.push(ch);
    }
  }
  return parts.join("");
}

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

function applySnakeIndicator(ctx: ExtensionContext) {
  if (!ctx.hasUI) return;

  // Snake state
  let snake = ["1,6", "1,5", "1,4", "1,3"]; // head first
  let food = randomFood(snake);
  let foodColor = Math.floor(Math.random() * FOOD_COLORS.length);

  const tick = () => {
    const head = snake[0];
    const occupied = new Set(snake.slice(0, -1));
    let next = bfsNext(head, food, occupied);

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

    snake.unshift(next);
    if (next === food) {
      snake.pop();
      food = randomFood(snake);
      foodColor = Math.floor(Math.random() * FOOD_COLORS.length);
    } else {
      snake.pop();
    }

    const grid = new Set([...snake, food]);
    const frame = toBrailleColored(grid, food, foodColor);
    ctx.ui.setWorkingIndicator({ frames: [frame], intervalMs: 120 });
  };

  const id = setInterval(tick, 120);

  ctx.signal?.addEventListener("abort", () => clearInterval(id));
}

export default function(pi: ExtensionAPI) {
  pi.on("session_start", async (_event, ctx) => {
    applySnakeIndicator(ctx);
  });
}
