import type {
  ExtensionAPI,
  ExtensionContext,
  WorkingIndicatorOptions,
} from "@earendil-works/pi-coding-agent";

// Braille Tetris: 4 braille chars = 8x4 dot grid, single text-line height
// Recognizable Tetris pieces (T, L, O, Z) drop, stack, fill rows, clear!
const TETRIS_INDICATOR: WorkingIndicatorOptions = {
  frames: [
    "⢀⣄⠀⠀", // T-piece falls
    "⠠⠦⠀⠀", // T falling
    "⠐⠓⠀⠀", // T lands
    "⠐⠓⡀⠀", // L-piece falls
    "⠐⠓⠄⠀", // L falling
    "⠐⠓⠂⠀", // L lands
    "⠐⠓⠋⠀", // O-piece falls
    "⣐⠓⠋⠀", // O lands
    "⠛⠓⠋⠀", // Z-piece falls
    "⠛⠓⢋⡀", // Z falling
    "⠛⠓⠫⠄", // Z lands
    "⠛⠓⠛⠋", // dot fills gap
    "⠛⢓⠛⠋", // dot lands
    "⠛⠛⠛⠋", // dot2 fills gap
    "⠛⠛⠛⢋", // dot2 lands
    "⠛⠛⠛⠛", // ROWS FULL!
    "⠀⠀⠀⠀", // flash
    "⠛⠛⠛⠛", // flash
    "⠀⠀⠀⠀", // flash
    "⠛⠛⠛⠛", // flash
    "⠀⠀⠀⠀", // cleared - loop
  ],
  intervalMs: 120,
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
