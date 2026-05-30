import type {
  ExtensionAPI,
  ExtensionContext,
  WorkingIndicatorOptions,
} from "@earendil-works/pi-coding-agent";

// Braille Tetris: 4 braille chars (8x4 dot grid), single text line height
// Pieces drop, rows fill up, flash, clear, loop
const TETRIS_INDICATOR: WorkingIndicatorOptions = {
  frames: [
    "⠀⣀⣀⠀", // I-piece drops
    "⠀⠤⠤⠀", // falling
    "⠀⠒⠒⠀", // falling
    "⠀⠉⠉⠀", // landed center
    "⠉⠉⠉⠀", // fill left gap
    "⠉⠉⠉⠉", // row 0 full!
    "⠒⠒⠀⠀", // row 1 half
    "⠒⠒⠒⠒", // row 1 full!
    "⠀⠀⠀⠀", // flash off (clear rows 0-1)
    "⠛⠛⠛⠛", // rows keep stacking
    "⠤⠤⠤⠤", // row 2-3 fill
    "⣤⣤⣤⣤", // almost full
    "⣿⣿⣿⣿", // ALL FULL!
    "⠀⠀⠀⠀", // grand clear
    "⣿⣿⣿⣿",
    "⠀⠀⠀⠀",
    "⣿⣿⣿⣿",
    "⠀⠀⠀⠀", // loop
  ],
  intervalMs: 110,
};

function applyTetrisIndicator(ctx: ExtensionContext) {
  if (!ctx.hasUI) return;
  ctx.ui.setWorkingIndicator(TETRIS_INDICATOR);
}

export default function(pi: ExtensionAPI) {
  pi.on("session_start", async (_event, ctx) => {
    applyTetrisIndicator(ctx);
  });
}
