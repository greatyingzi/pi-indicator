import type {
  ExtensionAPI,
  ExtensionContext,
  WorkingIndicatorOptions,
} from "@earendil-works/pi-coding-agent";

const TETRIS_INDICATOR: WorkingIndicatorOptions = {
  frames: [
    // Pieces land and fill the row
    "⬜⬜⬜⬜⬜⬜⬜🟦",
    "⬜⬜⬜⬜⬜⬜🟦🟦",
    "⬜⬜⬜⬜⬜🟦🟦🟦",
    "⬜⬜⬜⬜🟦🟦🟦🟦",
    "⬜⬜⬜⬜🟦🟦🟨🟨",
    "⬜⬜⬜🟩🟦🟦🟨🟨",
    "⬜⬜🟩🟩🟦🟦🟨🟨",
    "⬜🟧🟩🟩🟦🟦🟨🟨",
    "🟧🟧🟩🟩🟦🟦🟨🟨",
    // Row complete! Flash
    "🟧🟧🟩🟩🟦🟦🟨🟨",
    "⬜⬜⬜⬜⬜⬜⬜⬜",
    "🟧🟧🟩🟩🟦🟦🟨🟨",
    "⬜⬜⬜⬜⬜⬜⬜⬜",
    // Clear!
    "💥💥💥💥💥💥💥💥",
    "🔥🔥🔥🔥🔥🔥🔥🔥",
    "✨✨✨✨✨✨✨✨",
    // Empty pause before next loop
    "⬜⬜⬜⬜⬜⬜⬜⬜",
  ],
  intervalMs: 150,
};

function applyRunCatIndicator(ctx: ExtensionContext) {
  if (!ctx.hasUI) return;
  ctx.ui.setWorkingIndicator(TETRIS_INDICATOR);
}

export default function(pi: ExtensionAPI) {
  pi.on("session_start", async (_event, ctx) => {
    applyRunCatIndicator(ctx);
  });
}
