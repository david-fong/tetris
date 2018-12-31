import random
from math import log

from shapes import Shape

DEFAULT_SHAPE_SIZE = 4
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
    takes a list of shape name fields
    """
    weights = {}
    for key in SHAPES[shape_size].keys():
        weights[key] = 1.0 / (2 ** queue.count(key))
    #  print(weights)
    total_weight = 0.0
    for weight in weights.values():
        total_weight += weight

    choice = random.uniform(0, total_weight)
    for key in SHAPES[shape_size].keys():
        if choice < weights[key]:
            return SHAPES[shape_size][key]
        else:
            choice -= weights[key]
    assert False  # should never reach this statement


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


RCC = 'rotate counter-clockwise'
RCW = 'rotate clockwise'
TSD = 'soft drop'
THD = 'hard drop'
TSL = 'move left'
THL = 'hard left'
TSR = 'move right'
THR = 'hard right'
PAUSE = 'pause game'
"""
all players should have the same pause keys
"""
DEFAULT_BINDINGS = {
    1: {
        0: {
            RCC: ('q', ),
            RCW: ('e', ),
            TSD: ('s', ),
            THD: ('S', 'w', 'space'),
            TSL: ('a', 'Left'),
            THL: ('A', ),
            TSR: ('d', 'Right'),
            THR: ('D', ),
            PAUSE: ('Caps_Lock', )
        }
    },
    2: {
        0: {
            RCC: ('q', ),
            RCW: ('e', ),
            TSD: ('s', ),
            THD: ('w', ),
            TSL: ('a', ),
            THL: tuple(),
            TSR: ('d', ),
            THR: tuple(),
            PAUSE: ('Caps_Lock', 'Space')
        },
        1: {
            RCC: ('o', ),
            RCW: ('[', ),
            TSD: (';', ),
            THD: ('p', ),
            TSL: ('l', ),
            THL: tuple(),
            TSR: ('\'', ),
            THR: tuple(),
            PAUSE: ('Caps_Lock', 'Space')
        }
    }
}


def get_default_bindings(num_players: int, player_num: int):
    assert player_num < num_players
    return DEFAULT_BINDINGS[num_players][player_num].copy()


def calculate_score(num_lines):
    if num_lines is 0:
        return 0
    return 2 * calculate_score(num_lines - 1) + 1


FREQ_SCALAR = 2.0       # must be > 0
FREQ_BASE = 2.0         # must be > 1
FREQ_OFFSET = 16.0      # must be > 0
PERIOD_SOFT_DROP = 0.5  # 0.0 < this < 1.0
PERIOD_GRANULARITY = 2


def get_period(num_lines: int):
    freq = (num_lines + FREQ_OFFSET + 1) / (FREQ_OFFSET + 1)
    freq = FREQ_SCALAR * log(freq, FREQ_BASE) + 1
    return 1000 / freq


DEFAULT_NUM_ROWS = {
    4: 20
}

DEFAULT_NUM_COLS = {
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
