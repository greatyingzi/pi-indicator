# pi-snake

Animated working indicators for your `Pi` loading indicator — 6 built-in braille-dot animations on an 8×4 grid.

No font installation needed, works on any terminal that supports Unicode braille characters.

## Animations

| # | Name | Description |
|---|------|-------------|
| 🐍 | **Snake** | BFS pathfinding snake hunts colored food |
| 🏓 | **Pong** | AI-controlled paddles bounce a ball |
| 🧱 | **Tetris** | Pre-rendered tetris pieces fall and clear rows |
| ⚫ | **Bouncing Ball** | A ball bounces inside the grid with a motion trail |
| 🌊 | **Sine Wave** | Multiple overlapping sine waves flow smoothly |
| ✨ | **Fireflies** | Softly drifting dots fade in and out |

## Install

```bash
pi install https://github.com/greatyingzi/pi-snake
```

## Switch Animation

Use the `/snake` command to open a selection menu and switch animations at any time:

```
/snake
```

The default animation is Snake (backward compatible).

## Uninstall

```bash
pi remove npm:pi-snake
```

Inspired by [pi-runcat](https://github.com/FredySandoval/pi-runcat)
