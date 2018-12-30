import random
from math import log

from shapes import Shape

SHAPES = {
    4: {
        'I': Shape(((-1, 0),  (0, 0),  (1, 0),  (2, 0)),   'I'),
        'J': Shape(((-1, 0),  (0, 0),  (1, 0),  (1, -1)),  'J'),
        'L': Shape(((-1, 0),  (0, 0),  (1, 0),  (-1, -1)), 'L'),
        'O': Shape(((0, 0),   (1, 0),  (0, 1),  (1, 1)),   'O'),
        'S': Shape(((-1, -1), (0, -1), (0, 0),  (1, 0)),   'S'),
        'T': Shape(((-1, 0),  (0, 0),  (1, 0),  (0, -1)),  'T'),
        'Z': Shape(((-1, 0),  (0, 0),  (0, -1), (1, -1)),  'Z')
    }
}
SHAPE_QUEUE_SIZE = 20


def get_random_shape(shape_size: int, queue: list):
    """
    takes a list of shapes
    """
    weights = {}
    for key in SHAPES[shape_size].keys():
        weights[key] = queue.count(key) + 1
    queue_size = 0
    for weight in weights.values():
        queue_size += weight

    for key in weights.keys():
        weights[key] = queue_size / weights.get(key)
    #  print(weights)
    total_weight = 0
    for weight in weights.values():
        total_weight += weight

    choice = random.uniform(0, total_weight)
    for key in SHAPES[shape_size].keys():
        if choice < weights[key]:
            return SHAPES[shape_size][key]
        else:
            choice -= weights[key]
    assert False


CELL_EMPTY_KEY = ' '
CELL_WALL_KEY = 'wall'

"""
All sizes must have a 
color scheme with key='default'
"""
COLOR_SCHEMES = {
    4: {
        'default': {
            'bg': 'gray20',
            'key': 'white',
            CELL_EMPTY_KEY: 'black',
            'I': 'cyan',
            'J': 'blue',
            'L': 'orange',
            'O': 'yellow',
            'S': 'green',
            'T': 'purple',
            'Z': 'red'
        },
        'black & white': {
            'bg': 'gray20',
            'key': 'white',
            CELL_EMPTY_KEY: 'black',
            'I': 'white',
            'J': 'white',
            'L': 'white',
            'O': 'white',
            'S': 'white',
            'T': 'white',
            'Z': 'white'
        },
        'pastel': {
            'bg': '#FFFFFF',
            'key': '#F4F4F4',
            CELL_EMPTY_KEY: '#F4F4F4',
            'I': '#76F7E4',
            'J': '#FFBE63',
            'L': '#FFAE44',
            'O': '#F7EE4A',
            'S': '#B9F466',
            'T': '#FFB2EA',
            'Z': '#F76565'
        }
    }
}


def get_color_scheme(shape_size: int, key: str):
    """
    returns the dictionary corresponding to key
    and that corresponding to 'default' if key
    does not exist
    """
    try:
        return COLOR_SCHEMES[shape_size][key]
    except KeyError:
        return COLOR_SCHEMES[shape_size]['default']


RCC = 0
RCW = 1
TSD = 2
TSH = 3
TSL = 4
TSR = 5
THL = 6
THR = 7
DEFAULT_BINDINGS = {
    RCC: 'q',
    RCW: 'e',
    TSD: 's',
    TSH: 'S',
    TSL: 'a',
    TSR: 'd',
    THL: 'A',
    THR: 'D'
}


def get_default_bindings():
    return DEFAULT_BINDINGS.copy()


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
    return num_cells * (GUI_CELL_WID + GUI_CELL_PAD) + 2 * GUI_CELL_PAD


STOCKPILE_CAPACITY = 4

"""Courtesy of Wikipedia"""
facts = {
    "Tetris was created in 1984 by Russian Game designer Alexey Pajitnov",
    "The name Tetris partly comes from the Greek prefix for the number 4, 'tetra-'"
    "The name Tetris partly comes from 'tennis', Alexey Pajitnov's favorite sport"
}
