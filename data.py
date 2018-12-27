from game import Shape, Game
import random


SHAPES = {
    0: (
        Shape((), None)
    ),
    4: (
        Shape(((-1, 0), (0, 0), (1, 0), (2, 0)), 'I'),
        Shape(((-1, 0), (0, 0), (1, 0), (1, -1)), 'J'),
        Shape(((-1, 0), (0, 0), (1, 0), (-1, -1)), 'L'),
        Shape(((0, 0), (1, 0), (0, 1), (1, 1)), 'O'),
        Shape(((-1, -1), (0, -1), (0, 1), (1, 1)), 'S'),
        Shape(((-1, 0), (0, 0), (0, 1), (0, -1)), 'T'),
        Shape(((-1, 0), (0, 0), (0, -1), (1, -1)), 'Z')
    )
}

COLOR_SCHEMES = {
    4: {
        'default': {
            'bg': 'black',
            None: 'black',
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


SCORE_SCALAR = 2.0      # must be > 0
SCORE_BASE = 2.0        # must be > 1
SCORE_OFFSET = 16.0     # must be > 0


NUM_ROWS = {
    4: 20
}

NUM_COLS = {
    4: 10
}

GUI_WAIT_TIMEOUT = 0.001

GUI_CELL_WID = 10

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
