import type {
  ExtensionAPI,
  ExtensionContext,
  WorkingIndicatorOptions,
} from "@earendil-works/pi-coding-agent";

// Real-time Snake game on 8x4 braille grid with colored food
// Only the food dot is colored, snake body stays default

const DOT_MAP: Record<string, number> = {
  "0,0": 0x01, "1,0": 0x02, "2,0": 0x04, "3,0": 0x40,
  "0,1": 0x08, "1,1": 0x10, "2,1": 0x20, "3,1": 0x80,
};

const W = 8, H = 4;
const DIRS = [[0,1],[0,-1],[1,0],[-1,0]];

const FOOD_COLORS = [
  "\x1b[38;5;196m", // red 🍎
  "\x1b[38;5;226m", // yellow 🍋
  "\x1b[38;5;46m",  // green 🍏
  "\x1b[38;5;213m", // pink 🍑
  "\x1b[38;5;214m", // orange 🍊
  "\x1b[38;5;129m", // purple 🍇
  "\x1b[38;5;51m",  // cyan 🫐
];
const RESET = "\x1b[0m";

function renderFrame(snake: Set<string>, food: string, foodColor: number): string {
  const [foodR, foodC] = food.split(",").map(Number);

  // Build per-char: split into 4 braille chars (each covers 2 cols)
  const parts: string[] = [];
  for (let cx = 0; cx < W; cx += 2) {
    const charIdx = Math.floor(cx / 2);

    // Check if food is in this braille char's 2-col range
    const foodInThisChar = (foodC >= cx && foodC < cx + 2);

    let snakeVal = 0;
    let hasSnake = false;
    for (let r = 0; r < H; r++) {
      for (let c = 0; c < 2; c++) {
        if (snake.has(`${r},${cx + c}`)) {
          snakeVal |= DOT_MAP[`${r},${c}`];
          hasSnake = true;
        }
      }
    }

    if (foodInThisChar) {
      // Food dot only (without snake body in this char)
      let foodVal = DOT_MAP[`${foodR},${foodC - cx}`];

      if (hasSnake) {
        // Both food and snake in this char — render separately
        // Snake char (no food dot) then food char (colored)
        // But we can only show one char here... so overlay: food on top
        // Render as: colored food dot merged into the char
        const merged = snakeVal | foodVal;
        const color = FOOD_COLORS[foodColor % FOOD_COLORS.length];
        parts.push(`${color}${String.fromCharCode(0x2800 + merged)}${RESET}`);
      } else {
        // Only food in this char
        const color = FOOD_COLORS[foodColor % FOOD_COLORS.length];
        parts.push(`${color}${String.fromCharCode(0x2800 + foodVal)}${RESET}`);
      }
    } else if (hasSnake) {
      // Only snake in this char
      parts.push(String.fromCharCode(0x2800 + snakeVal));
    } else {
      // Empty
      parts.push("\u2800");
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

  let snake = ["1,6", "1,5", "1,4", "1,3"];
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

    // Snake body only (no food)
    const snakeGrid = new Set(snake);
    const frame = renderFrame(snakeGrid, food, foodColor);
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
