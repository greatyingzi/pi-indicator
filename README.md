# pi-snake

Animated working indicators for `Pi` — tiny braille-dot games on an 8×4 grid.

## Animations

| Name | Description |
|------|-------------|
| 🐍 Snake | BFS pathfinding snake hunts colored food |
| 🧱 Breakout | Horizontal breakout — bricks on left, paddle on right |
| 👾 Pac-Man | Side-scrolling pac-man eating dots, ghosts chase behind |

## Install

```bash
pi install https://github.com/greatyingzi/pi-snake
```

## Switch Animation

```bash
/snake              # Pick from menu
/snake snake        # Switch to Snake
/snake breakout     # Switch to Breakout
/snake pacman       # Switch to Pac-Man
```

## Uninstall

```bash
pi remove npm:pi-snake
```

No font installation needed — works on any Unicode terminal.

Inspired by [pi-runcat](https://github.com/FredySandoval/pi-runcat)
