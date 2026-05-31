# pi-indicator

Animated working indicators for `Pi` — tiny braille-dot games on a 16×4 grid.

## Animations

| Name | Description |
|------|-------------|
| 🐍 Snake | BFS pathfinding snake hunts colored food |
| 🧱 Breakout | Horizontal breakout — bricks on left, paddle on right |
| 👾 Pac-Man | Side-view pac-man eating dots floating in from right |
| 📊 Equalizer | 8-bar audio equalizer with smooth interpolation |
| 🛸 Invaders | Horizontal space invaders — ship vs aliens |

## Install

```bash
pi install https://github.com/greatyingzi/pi-indicator
```

## Switch Animation

```bash
/indicator           # Pick from menu
/indicator snake     # Switch to Snake
/indicator breakout  # Switch to Breakout
/indicator pacman    # Switch to Pac-Man
/indicator equalizer # Switch to Equalizer
/indicator invaders  # Switch to Invaders
/anim snake          # /anim also works as shorthand
```

Choice is persisted — your selection is remembered across sessions.

## Uninstall

```bash
pi remove npm:pi-indicator
```

No font installation needed — works on any Unicode terminal.

Inspired by [pi-runcat](https://github.com/FredySandoval/pi-runcat)
