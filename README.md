# pi-indicator

Animated working indicators for `Pi` — tiny braille-dot games on a 16×4 grid.

## Animations

| Name | Description |
|------|-------------|
| 🐍 Snake | BFS pathfinding snake hunts colored food |
| 🧱 Breakout | Horizontal breakout — bricks on left, paddle on right |
| 👾 Pac-Man | Side-view pac-man eating dots floating in from right |

## Install

```bash
pi install https://github.com/greatyingzi/pi-indicator
```

## Switch Animation

```bash
/snake              # Pick from menu
/snake snake        # Switch to Snake
/snake breakout     # Switch to Breakout
/snake pacman       # Switch to Pac-Man
```

Choice is persisted — your selection is remembered across sessions.

## Uninstall

```bash
pi remove npm:pi-indicator
```

No font installation needed — works on any Unicode terminal.

Inspired by [pi-runcat](https://github.com/FredySandoval/pi-runcat)
