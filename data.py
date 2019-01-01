import random
from math import log

from shapes import Shape

DEFAULT_SHAPE_SIZE = 4
SHAPE_EMPTY_NAME = ' '
SHAPES = {
    4: {
        'default': {
            'I': Shape(((0, 0), (1, 0), (2, 0), (3, 0)), 'I'),
            'J': Shape(((0, 1), (1, 1), (2, 1), (2, 0)), 'J'),
            'L': Shape(((0, 1), (1, 1), (2, 1), (0, 0)), 'L'),
            'O': Shape(((0, 0), (1, 0), (0, 1), (1, 1)), 'O'),
            'S': Shape(((0, 0), (1, 0), (1, 1), (2, 1)), 'S'),
            'T': Shape(((0, 1), (1, 1), (2, 1), (1, 0)), 'T'),
            'Z': Shape(((0, 1), (1, 1), (1, 0), (2, 0)), 'Z')
        },
        'mr stark I don\'t feel so good': {
            'I': Shape(((0, 0), (1, 0), (3, 0)), 'I'),
            'J': Shape(((0, 0), (0, 1), (2, 0)), 'J'),
            'L': Shape(((0, 0), (2, 1), (2, 0)), 'L'),
            'O': Shape(((0, 0), (2, 0), (0, 2)), 'O'),
            'S': Shape(((0, 0), (1, 0), (2, 1)), 'S'),
            'T': Shape(((0, 2), (2, 1), (1, 0)), 'T'),
            'Z': Shape(((0, 1), (1, 0)), 'Z')
        },
        'thonk': {
            'I': Shape(((0, 0), (1, 0), (2, 0), (3, 0)), 'I'),
            'O': Shape(((0, 0), (1, 0), (2, 0), (3, 0)), 'O')
        }
    }
}
SHAPE_QUEUE_SIZE = 20


def get_random_shape(shape_size: int, shape_set: str, queue: list):
    """
    takes a list of shape name fields
    """
    weights = {}
    for key in SHAPES[shape_size][shape_set].keys():
        weights[key] = 1.0 / (2 ** queue.count(key))
    #  print(weights)
    total_weight = 0.0
    for weight in weights.values():
        total_weight += weight

    choice = random.uniform(0, total_weight)
    for key in SHAPES[shape_size][shape_set].keys():
        if choice < weights[key]:
            return SHAPES[shape_size][shape_set][key]
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
            'bg': 'black',
            'grid-lines': 'gray20',
            CELL_EMPTY_KEY: 'black',
            'text': 'white',
            'I': 'cyan',
            'J': 'blue',
            'L': 'orange',
            'O': 'yellow',
            'S': 'green',
            'T': 'purple',
            'Z': 'red'
        },
        'black & white': {
            'bg': 'black',
            'grid-lines': 'gray20',
            CELL_EMPTY_KEY: 'black',
            'text': 'white',
            'I': 'white',
            'J': 'white',
            'L': 'white',
            'O': 'white',
            'S': 'white',
            'T': 'white',
            'Z': 'white'
        },
        'pastel': {
            'bg': '#F4F4F4',
            'grid-lines': '#FFFFFF',
            CELL_EMPTY_KEY: '#F4F4F4',
            'text': '#000000',
            'I': '#76F7E4',
            'J': '#FFBE63',
            'L': '#FFAE44',
            'O': '#F7EE4A',
            'S': '#B9F466',
            'T': '#FFB2EA',
            'Z': '#F76565'
        },
        'old-school': {
            'bg': '#CACC92',
            'grid-lines': '#CACC92',
            CELL_EMPTY_KEY: '#DCDDAA',
            'text': '#65663C',
            'I': '#A4A56F',
            'J': '#A4A56F',
            'L': '#A4A56F',
            'O': '#A4A56F',
            'S': '#A4A56F',
            'T': '#A4A56F',
            'Z': '#A4A56F'
        },
        'winter': {
            'bg': '#80B9BC',
            'grid-lines': '#9ED5D8',
            CELL_EMPTY_KEY: '#BAECEF',
            'text': 'white',
            'I': 'white',
            'J': 'white',
            'L': 'white',
            'O': 'white',
            'S': 'white',
            'T': 'white',
            'Z': 'white'
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
STOCKPILE = 'access stockpile'
PAUSE = 'pause game'
RESTART = 'restart the player\'s game'
"""
all players should have the same pause keys
"""
DEFAULT_NUM_PLAYERS = 1
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
            STOCKPILE: (('1', 'z'), ('2', 'x'), ('3', 'c'), ('4', 'v'), ('5', ), ('6', )),
            PAUSE: ('Caps_Lock', ),
            RESTART: ('Escape', )
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
            STOCKPILE: (('1', 'z'), ('2', 'x'), ('3', 'c'), ('4', 'v')),
            PAUSE: ('Caps_Lock', 'Space'),
            RESTART: ('F', )
        },
        1: {
            RCC: ('u', ),
            RCW: ('o', ),
            TSD: ('k', ),
            THD: ('i', ),
            TSL: ('j', ),
            THL: tuple(),
            TSR: ('l', ),
            THR: tuple(),
            STOCKPILE: (('7', 'b'), ('8', 'n'), ('9', 'm'), ('0', 'comma')),
            PAUSE: ('Caps_Lock', 'Space'),
            RESTART: ('H', )
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


FREQ_SCALAR_KEYS = {
    '0.50x': 0,
    '0.75x': 1,
    '1.00x': 2,
    '1.25x': 3,
    '1.50x': 4
}
FREQ_SCALARS = (0.5, 0.75, 1.0, 1.25, 1.5)
FREQ_BASE = 2.0         # must be > 1
FREQ_OFFSET = 16.0      # must be > 0
PERIOD_SOFT_DROP = 0.5  # 0.0 < this < 1.0
PERIOD_GRANULARITY = 2


def get_period(num_lines: int, freq_scalar_index: int):
    freq = (num_lines + FREQ_OFFSET + 1) / (FREQ_OFFSET + 1)
    freq = 1.5 * log(freq, FREQ_BASE) + 1
    freq *= FREQ_SCALARS[freq_scalar_index]
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
