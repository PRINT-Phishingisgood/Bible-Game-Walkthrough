# Bible Quest 🐑

A Python/Pygame Bible-based game portal.

## How to Run

```bash
pip install pygame
python main.py
```

## Project Structure

```
bible_game/
├── main.py        # The Portal — hub screen with doors
├── sheep_maze.py  # Game 1: The Lost Sheep (Luke 15:3–7)
└── README.md      # This file
```

## Controls

| Key | Action |
|-----|--------|
| WASD / Arrow Keys | Move the shepherd |
| ESC | Return to the Portal |

## Games

### 🚪 Door 1 & 2 — The Lost Sheep
Find all 5 sheep hidden in a bush-filled maze.
The maze is covered in fog — you can only see a small circle around your shepherd.

Based on **Luke 15:4**:
> *"What man of you, having a hundred sheep, if he has lost one of them,
> does not leave the ninety-nine in the open country, and go after the one
> that is lost, until he finds it?"*

## How to Add More Games

1. Create a new Python file, e.g. `david_goliath.py`, with a `run()` function.
2. Add a new door entry to the `DOORS` list in `main.py`.
3. Add an `elif result == "david_goliath":` branch in `main()`.

## Technical Notes

- **Maze algorithm**: Recursive Backtracker (Depth-First Search)
- **Fog of war**: SRCALPHA surface with gradient alpha circles
- **No external assets**: all graphics drawn with pygame primitives
- **Collision**: 4-corner AABB against the maze grid
