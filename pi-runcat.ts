import type {
  ExtensionAPI,
  ExtensionContext,
  WorkingIndicatorOptions,
} from "@earendil-works/pi-coding-agent";

// Braille Tetris: 8x4 dot grid (4 braille chars), single text-line height
// Pieces (T→L→O→S→I) drop from top, fill bottom row, flash, clear!
const TETRIS_INDICATOR: WorkingIndicatorOptions = {
  frames: [
    "⠈⠋⠀⠀", // T-piece falls
    "⠐⠖⠀⠀", // T falling
    "⠠⡤⠁⠀", // T lands, L-piece appears
    "⠠⡤⠂⠀", // L falls
    "⠩⡤⣄⠀", // O-piece drops
    "⠲⡤⣌⠁", // S-piece drops
    "⠻⡭⣴⠆", // I-piece fills gaps
    "⣲⣤⣴⣆", // Row full!
    "⠀⠀⠀⠀", // Flash
    "⣲⣤⣴⣆",
    "⠀⠀⠀⠀", // Flash
    "⣲⣤⣴⣆",
    "⠀⠀⠀⠀", // Cleared!
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
