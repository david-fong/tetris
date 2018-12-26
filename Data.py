from Game import Shape
import random


SHAPES = {
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


def get_random_shape(shape_size):
    return random.choice(SHAPES[shape_size])


NUM_ROWS = {
    4: 20
}

NUM_COLS = {
    4: 10
}

"""Courtesy of Wikipedia"""
facts = {
    "Tetris was created in 1984 by Russian Game designer Alexey Pajitnov",
    "The name Tetris partly comes from the Greek prefix for the number 4, 'tetra-'"
    "The name Tetris partly comes from 'tennis', Alexey Pajitnov's favorite sport"
}
