#!/usr/bin/env python3
"""Conway's Game of Life on the Sense HAT 8x8 LED matrix.

The grid is a torus (edges wrap around). Runs forever: when the board
dies out or settles into a repeating cycle, it reseeds with a random
soup. Pressing the joystick reseeds immediately. Ctrl-C to quit.

Usage:
    life.py [--color R,G,B] [--speed GENERATIONS_PER_SEC]
"""

import argparse
import random
import time

from sense_hat import SenseHat

SIZE = 8
HISTORY_LEN = 12           # generations remembered for cycle detection
DEFAULT_COLOR = (237, 100, 228)
DEFAULT_SPEED = 2.0        # generations per second
DEAD = (0, 0, 0)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Conway's Game of Life on the Sense HAT LED matrix."
    )
    parser.add_argument(
        "--color",
        type=parse_color,
        default=DEFAULT_COLOR,
        metavar="R,G,B",
        help="cell color as three 0-255 values, e.g. 237,100,228 "
             "(default: %(default)s)",
    )
    parser.add_argument(
        "--speed",
        type=float,
        default=DEFAULT_SPEED,
        metavar="GEN_PER_SEC",
        help="generations per second (default: %(default)s)",
    )
    args = parser.parse_args()
    if args.speed <= 0:
        parser.error("--speed must be > 0")
    return args


def parse_color(text):
    parts = text.split(",")
    if len(parts) != 3:
        raise argparse.ArgumentTypeError("expected R,G,B")
    rgb = tuple(int(p) for p in parts)
    if not all(0 <= v <= 255 for v in rgb):
        raise argparse.ArgumentTypeError("values must be 0-255")
    return rgb


def lighten(rgb, amount=0.5):
    """Blend a color toward white to mark newborn cells."""
    return tuple(int(v + (255 - v) * amount) for v in rgb)


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


def draw(sense, grid, prev, alive_color, newborn_color):
    pixels = []
    for y in range(SIZE):
        for x in range(SIZE):
            if grid[y][x]:
                pixels.append(alive_color if prev[y][x] else newborn_color)
            else:
                pixels.append(DEAD)
    sense.set_pixels(pixels)


def key(grid):
    return tuple(tuple(row) for row in grid)


def main():
    args = parse_args()
    alive_color = args.color
    newborn_color = lighten(args.color)
    step_delay = 1.0 / args.speed

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

            draw(sense, grid, prev, alive_color, newborn_color)
            history.append(key(grid))
            del history[:-HISTORY_LEN]
            time.sleep(step_delay)
    except KeyboardInterrupt:
        pass
    finally:
        sense.clear()


if __name__ == "__main__":
    main()
