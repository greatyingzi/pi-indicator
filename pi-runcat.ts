import type {
  ExtensionAPI,
  ExtensionContext,
  WorkingIndicatorOptions,
} from "@earendil-works/pi-coding-agent";

const RUNCAT_INDICATOR: WorkingIndicatorOptions = {
  frames: ["🐱 ", "😺 ", "😸 ", "😻 ", "😼 "],
  intervalMs: 167,
};
function applyRunCatIndicator(ctx: ExtensionContext) {
  if (!ctx.hasUI) return;
  ctx.ui.setWorkingIndicator(RUNCAT_INDICATOR);
}

export default function(pi: ExtensionAPI) {
  pi.on("session_start", async (_event, ctx) => {
    applyRunCatIndicator(ctx);
  });
}
