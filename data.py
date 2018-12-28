
import random

from game import Game
from shapes import Shape

SHAPES = {
    4: (
        Shape(((-1, 0), (0, 0), (1, 0), (2, 0)), 'I'),
        Shape(((-1, 0), (0, 0), (1, 0), (1, -1)), 'J'),
        Shape(((-1, 0), (0, 0), (1, 0), (-1, -1)), 'L'),
        Shape(((0, 0), (1, 0), (0, 1), (1, 1)), 'O'),
        Shape(((-1, -1), (0, -1), (0, 0), (1, 0)), 'S'),
        Shape(((-1, 0), (0, 0), (1, 0), (0, -1)), 'T'),
        Shape(((-1, 0), (0, 0), (0, -1), (1, -1)), 'Z')
    )
}

COLOR_SCHEMES = {
    4: {
        'default': {
            'bg': 'black',
            ' ': 'black',
            'I': 'cyan',
            'J': 'blue',
            'L': 'orange',
            'O': 'yellow',
            'S': 'green',
            'T': 'purple',
            'Z': 'red'
        }
    }
}


def get_random_shape(shape_size):
    return random.choice(SHAPES[shape_size])


def calculate_score(num_lines):
    if num_lines is 0:
        return 0
    return 2 * calculate_score(num_lines - 1) + 1


PERIOD_SCALAR = 2.0      # must be > 0
PERIOD_BASE = 2.0        # must be > 1
PERIOD_OFFSET = 16.0     # must be > 0

NUM_ROWS = {
    4: 20
}

NUM_COLS = {
    4: 10
}

GUI_CELL_WID = 10
GUI_CELL_PAD = 0


def canvas_dmn(num_cells: int):
    result = GUI_CELL_WID + GUI_CELL_PAD
    result *= num_cells
    return result + GUI_CELL_PAD


KBD_EVENTS = {
    '<w>': Game.hard_drop
}

STOCKPILE_CAPACITY = 4

"""Courtesy of Wikipedia"""
facts = {
    "Tetris was created in 1984 by Russian Game designer Alexey Pajitnov",
    "The name Tetris partly comes from the Greek prefix for the number 4, 'tetra-'"
    "The name Tetris partly comes from 'tennis', Alexey Pajitnov's favorite sport"
}
