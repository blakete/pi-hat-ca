#!/usr/bin/env python3
"""Conway's Game of Life on the Sense HAT 8x8 LED matrix.

The grid is a torus (edges wrap around). Runs forever: when the board
dies out or settles into a repeating cycle, it reseeds with a random
soup. Ctrl-C to quit.

Joystick (inverted for how the Pi is physically mounted):
    down / up     brighter / dimmer
    left / right  faster / slower
    center press  reseed with a fresh random soup

Usage:
    life.py [--color R,G,B] [--speed GENERATIONS_PER_SEC] [--brightness 0..1]
"""

import argparse
import random
import time

from sense_hat import SenseHat

SIZE = 8
HISTORY_LEN = 12           # generations remembered for cycle detection
DEFAULT_COLOR = (237, 100, 228)
DEFAULT_SPEED = 2.0        # generations per second
DEFAULT_BRIGHTNESS = 0.3   # roughly matches the old low_light look
DEAD = (0, 0, 0)

POLL_DELAY = 0.05          # joystick poll interval between generations
BRIGHTNESS_STEP = 1.3      # multiplier per up/down press
SPEED_STEP = 1.5           # multiplier per right/left press
MIN_BRIGHTNESS = 0.02      # below this the whole matrix rounds to black
MIN_SPEED, MAX_SPEED = 0.05, 20.0


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
    parser.add_argument(
        "--brightness",
        type=float,
        default=DEFAULT_BRIGHTNESS,
        metavar="0..1",
        help="LED brightness from 0.0 (off) to 1.0 (full), "
             "default: %(default)s",
    )
    args = parser.parse_args()
    if args.speed <= 0:
        parser.error("--speed must be > 0")
    if not 0.0 <= args.brightness <= 1.0:
        parser.error("--brightness must be between 0.0 and 1.0")
    return args


def parse_color(text):
    parts = text.split(",")
    if len(parts) != 3:
        raise argparse.ArgumentTypeError("expected R,G,B")
    rgb = tuple(int(p) for p in parts)
    if not all(0 <= v <= 255 for v in rgb):
        raise argparse.ArgumentTypeError("values must be 0-255")
    return rgb


def set_brightness(sense, brightness):
    """Scale the LED matrix gamma table for continuous brightness control."""
    sense.gamma_reset()
    sense.gamma = [min(31, round(v * brightness)) for v in sense.gamma]


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


class Controls:
    """Joystick-adjustable runtime state."""

    def __init__(self, sense, brightness, speed):
        self.sense = sense
        self.brightness = brightness
        self.speed = speed
        self.reseed = False

    def handle_events(self):
        for event in self.sense.stick.get_events():
            if event.action not in ("pressed", "held"):
                continue
            # Directions are inverted: the Pi is mounted upside down.
            if event.direction == "down":
                self.brightness = min(1.0, self.brightness * BRIGHTNESS_STEP)
                set_brightness(self.sense, self.brightness)
            elif event.direction == "up":
                self.brightness = max(
                    MIN_BRIGHTNESS, self.brightness / BRIGHTNESS_STEP
                )
                set_brightness(self.sense, self.brightness)
            elif event.direction == "left":
                self.speed = min(MAX_SPEED, self.speed * SPEED_STEP)
            elif event.direction == "right":
                self.speed = max(MIN_SPEED, self.speed / SPEED_STEP)
            elif event.direction == "middle":
                self.reseed = True


def main():
    args = parse_args()
    alive_color = args.color
    newborn_color = lighten(args.color)

    sense = SenseHat()
    controls = Controls(sense, args.brightness, args.speed)
    set_brightness(sense, controls.brightness)
    grid = random_soup()
    history = [key(grid)]
    next_step = time.monotonic()

    try:
        while True:
            controls.handle_events()
            now = time.monotonic()
            if controls.reseed or now >= next_step:
                prev = grid
                grid = step(grid)

                alive = any(any(row) for row in grid)
                if controls.reseed or not alive or key(grid) in history:
                    grid = random_soup()
                    prev = [[False] * SIZE for _ in range(SIZE)]
                    history.clear()
                    controls.reseed = False

                draw(sense, grid, prev, alive_color, newborn_color)
                history.append(key(grid))
                del history[:-HISTORY_LEN]
                next_step = now + 1.0 / controls.speed
            # Speed increases apply immediately, not after the old delay.
            next_step = min(next_step, now + 1.0 / controls.speed)
            time.sleep(POLL_DELAY)
    except KeyboardInterrupt:
        pass
    finally:
        sense.clear()


if __name__ == "__main__":
    main()
