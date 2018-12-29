import random
from math import log

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


def get_random_shape(shape_size):
    return random.choice(SHAPES[shape_size])


"""
All sizes must have a 
color scheme with key='default'
"""
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


def get_color_scheme(shape_size: int, key: str):
    """
    returns the dictionary corresponding to key
    and that corresponding to 'default' if key
    does not exist
    :rtype: dict
    """
    try:
        return COLOR_SCHEMES[shape_size][key]
    except KeyError:
        return COLOR_SCHEMES[shape_size]['default']


def calculate_score(num_lines):
    if num_lines is 0:
        return 0
    return 2 * calculate_score(num_lines - 1) + 1


FREQ_SCALAR = 2.0       # must be > 0
FREQ_BASE = 2.0         # must be > 1
FREQ_OFFSET = 16.0      # must be > 0
PERIOD_SOFT_DROP = 0.5  # 0.0 < this < 1.0
PERIOD_GRANULARITY = 2


def get_period(num_lines: int = 0):
    freq = (num_lines + FREQ_OFFSET + 1) / (FREQ_OFFSET + 1)
    freq = FREQ_SCALAR * log(freq, FREQ_BASE) + 1
    return 1000 / freq


NUM_ROWS = {
    4: 20
}

NUM_COLS = {
    4: 10
}

GUI_CELL_WID: int = 20
GUI_CELL_PAD: int = 2


def canvas_dmn(num_cells: int):
    assert isinstance(num_cells, int)
    result: int = GUI_CELL_WID + GUI_CELL_PAD
    result *= num_cells
    return result + GUI_CELL_PAD


STOCKPILE_CAPACITY = 4

"""Courtesy of Wikipedia"""
facts = {
    "Tetris was created in 1984 by Russian Game designer Alexey Pajitnov",
    "The name Tetris partly comes from the Greek prefix for the number 4, 'tetra-'"
    "The name Tetris partly comes from 'tennis', Alexey Pajitnov's favorite sport"
}
