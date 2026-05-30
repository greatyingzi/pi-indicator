import type {
  ExtensionAPI,
  ExtensionContext,
  WorkingIndicatorOptions,
} from "@earendil-works/pi-coding-agent";

const TETRIS_INDICATOR: WorkingIndicatorOptions = {
  frames: [
    // Pieces land (each jump = a different piece)
    "░░░░░░░░░█",
    "░░░░░░░███",
    "░░░░░░████",
    "░░░░██████",
    "░░████████",
    "██████████",
    // Row complete! Flash & clear
    "▓▓▓▓▓▓▓▓▓▓",
    "██████████",
    "▓▓▓▓▓▓▓▓▓▓",
    "░░░░░░░░░░",
  ],
  intervalMs: 130,
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
