#!/usr/bin/env python3
"""Conway's Game of Life on the Sense HAT 8x8 LED matrix.

The grid is a torus (edges wrap around). Runs forever: when the board
dies out or settles into a repeating cycle, it reseeds with a random
soup. Pressing the joystick reseeds immediately. Ctrl-C to quit.
"""

import random
import time

from sense_hat import SenseHat

SIZE = 8
STEP_DELAY = 0.25          # seconds between generations
HISTORY_LEN = 12           # generations remembered for cycle detection
ALIVE = (0, 180, 40)       # green
NEWBORN = (120, 220, 120)  # lighter green for cells born this step
DEAD = (0, 0, 0)


def random_soup(fill=0.35):
    return [[random.random() < fill for _ in range(SIZE)] for _ in range(SIZE)]


def step(grid):
    new = [[False] * SIZE for _ in range(SIZE)]
    for y in range(SIZE):
        for x in range(SIZE):
            neighbors = sum(
                grid[(y + dy) % SIZE][(x + dx) % SIZE]
                for dy in (-1, 0, 1)
                for dx in (-1, 0, 1)
                if (dy, dx) != (0, 0)
            )
            new[y][x] = neighbors == 3 or (grid[y][x] and neighbors == 2)
    return new


def draw(sense, grid, prev):
    pixels = []
    for y in range(SIZE):
        for x in range(SIZE):
            if grid[y][x]:
                pixels.append(NEWBORN if not prev[y][x] else ALIVE)
            else:
                pixels.append(DEAD)
    sense.set_pixels(pixels)


def key(grid):
    return tuple(tuple(row) for row in grid)


def main():
    sense = SenseHat()
    sense.low_light = True
    grid = random_soup()
    history = [key(grid)]

    try:
        while True:
            # Joystick press -> reseed on demand.
            reseed = any(
                e.action == "pressed" for e in sense.stick.get_events()
            )

            prev = grid
            grid = step(grid)

            alive = any(any(row) for row in grid)
            if reseed or not alive or key(grid) in history:
                grid = random_soup()
                prev = [[False] * SIZE for _ in range(SIZE)]
                history.clear()

            draw(sense, grid, prev)
            history.append(key(grid))
            del history[:-HISTORY_LEN]
            time.sleep(STEP_DELAY)
    except KeyboardInterrupt:
        pass
    finally:
        sense.clear()


if __name__ == "__main__":
    main()
