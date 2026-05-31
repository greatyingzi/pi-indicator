#!/usr/bin/env python3
"""GIF to braille — v5: configurable resolution (1-4 lines).
  1 line = 16x4  (64 dots)
  2 lines = 16x8  (128 dots)
  3 lines = 16x12 (192 dots)
  4 lines = 16x16 (256 dots)

Usage:
    python3 gif_to_braille.py <gif> [lines] [threshold]         # play in terminal
    python3 gif_to_braille.py <gif> --export output.json [lines] [threshold]  # export frames
"""
import sys, time, json
from PIL import Image
from collections import Counter

DOT_MAP = {
    (0, 0): 0x01, (1, 0): 0x02, (2, 0): 0x04, (3, 0): 0x40,
    (0, 1): 0x08, (1, 1): 0x10, (2, 1): 0x20, (3, 1): 0x80,
}
BRAILLE_OFFSET = 0x2800
RESET = "\x1b[0m"
W = 16

def rgb_to_ansi256(r, g, b):
    cr = max(0, min(5, round(r / 51)))
    cg = max(0, min(5, round(g / 51)))
    cb = max(0, min(5, round(b / 51)))
    cube = 16 + 36 * cr + 6 * cg + cb
    gray = max(232, min(255, round((r + g + b) / 3 / 10.38) + 232))
    cr2, cg2, cb2 = cr * 51, cg * 51, cb * 51
    gv = (gray - 232) * 10.38
    d_cube = (r-cr2)**2 + (g-cg2)**2 + (b-cb2)**2
    d_gray = (r-gv)**2 + (g-gv)**2 + (b-gv)**2
    return cube if d_cube <= d_gray else gray

def load_gif(path):
    img = Image.open(path)
    frames = []
    try:
        while True:
            frames.append((img.copy().convert("RGBA"), img.info.get('duration', 100) / 1000.0))
            img.seek(img.tell() + 1)
    except EOFError:
        pass
    return frames

def detect_bg(frames, W, H):
    f0 = frames[0][0].resize((W, H), Image.LANCZOS).convert("RGB")
    return Counter(list(f0.getdata())).most_common(1)[0][0]

def frame_to_braille(img, W, H, bg, thresh):
    small = img.resize((W, H), Image.LANCZOS).convert("RGBA")
    px = small.load()
    color_map = {}
    for y in range(H):
        for x in range(W):
            r, g, b, a = px[x, y]
            if bg is not None:
                diff = abs(r - bg[0]) + abs(g - bg[1]) + abs(b - bg[2])
                if diff <= thresh:
                    continue
            else:
                if a < 30:
                    continue
            color_map[(y, x)] = f"\x1b[38;5;{rgb_to_ansi256(r, g, b)}m"

    lines = []
    n_halves = H // 4
    for half in range(n_halves):
        row_off = half * 4
        parts = []
        for cx in range(0, W, 2):
            val = 0
            best = None
            for row in range(4):
                for col in range(2):
                    key = (row_off + row, cx + col)
                    if key in color_map:
                        val |= DOT_MAP[(row, col)]
                        if best is None:
                            best = color_map[key]
            if val == 0:
                parts.append(" ")
            else:
                ch = chr(BRAILLE_OFFSET + val)
                parts.append(f"{best}{ch}{RESET}" if best else ch)
        lines.append("".join(parts))
    return "\n".join(lines)

def export_frames(gif, output_path, n_lines, thresh):
    """Convert GIF frames to braille and export as JSON."""
    H = n_lines * 4
    frames = load_gif(gif)
    print(f"{len(frames)} frames, {W}x{H}, exporting to {output_path}", file=sys.stderr)

    f0 = frames[0][0].resize((W, H), Image.LANCZOS)
    opaque = sum(1 for _,_,_,a in f0.convert("RGBA").getdata() if a > 128)
    bg = None
    if opaque / (W * H) > 0.85:
        bg = detect_bg(frames, W, H)
        print(f"bgremove bg={bg}", file=sys.stderr)
    else:
        print("alpha mode", file=sys.stderr)

    braille_frames = []
    for i, (frame, dur) in enumerate(frames):
        s = frame_to_braille(frame, W, H, bg, thresh)
        braille_frames.append(s)

    data = {"frames": braille_frames}
    with open(output_path, 'w') as f:
        json.dump(data, f)

    print(f"Exported {len(braille_frames)} frames to {output_path}", file=sys.stderr)

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] in ("--help", "-h"):
        print("Usage:")
        print("  python3 gif_to_braille.py <gif> [lines] [threshold]         # play in terminal")
        print("  python3 gif_to_braille.py <gif> --export output.json [lines] [threshold]  # export frames")
        sys.exit(0 if len(sys.argv) >= 2 else 1)

    # Parse --export mode
    export_path = None
    args = sys.argv[1:]
    gif = args[0]

    if "--export" in args:
        idx = args.index("--export")
        if idx + 1 >= len(args):
            print("Error: --export requires an output file path", file=sys.stderr)
            sys.exit(1)
        export_path = args[idx + 1]
        # Remove --export and output_path from args, keep remaining positional args
        args = args[:idx] + args[idx + 2:]

    n_lines = int(args[1]) if len(args) > 1 else 3
    thresh = int(args[2]) if len(args) > 2 else 60

    if export_path:
        export_frames(gif, export_path, n_lines, thresh)
    else:
        H = n_lines * 4
        frames = load_gif(gif)
        f0 = frames[0][0].resize((W, H), Image.LANCZOS)
        opaque = sum(1 for _,_,_,a in f0.convert("RGBA").getdata() if a > 128)
        bg = None
        if opaque / (W * H) > 0.85:
            bg = detect_bg(frames, W, H)
            print(f"{len(frames)} frames, {W}x{H}, bgremove bg={bg}", file=sys.stderr)
        else:
            print(f"{len(frames)} frames, {W}x{H}, alpha mode", file=sys.stderr)

        try:
            while True:
                for frame, dur in frames:
                    s = frame_to_braille(frame, W, H, bg, thresh)
                    sys.stdout.write(f"\x1b[{n_lines}A\r")
                    for line in s.split("\n"):
                        sys.stdout.write(f"\x1b[K{line}\n")
                    sys.stdout.flush()
                    time.sleep(max(0.04, min(dur, 0.5)))
        except KeyboardInterrupt:
            print("\nDone")
