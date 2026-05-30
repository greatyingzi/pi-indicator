import type {
  ExtensionAPI,
  ExtensionContext,
  WorkingIndicatorOptions,
} from "@earendil-works/pi-coding-agent";

// Single braille char (2x4 dot grid) Tetris animation
// ⢀⢠⢰⢸⣼⣾⣿ = pieces stack up row by row
// ⠀⣿ flashing = row clear
const TETRIS_INDICATOR: WorkingIndicatorOptions = {
  frames: [
    "\u2880", // ⢀  piece drops
    "\u28A0", // ⢠  stacks
    "\u28B0", // ⢰  stacks
    "\u28B8", // ⢸  right column full
    "\u28FC", // ⣼  left fills
    "\u28FE", // ⣾  left fills
    "\u28FF", // ⣿  FULL!
    "\u2800", // ⠀  flash
    "\u28FF", // ⣿
    "\u2800", // ⠀  flash
    "\u28FF", // ⣿
    "\u2800", // ⠀  cleared
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
