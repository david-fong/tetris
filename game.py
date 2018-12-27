from math import log
from threading import Thread, Condition

import data
from shapes import *


class Cell:
    """
    An entry in a Game's grid field.
    Represents a shape's key, which
    can be used to get a color value.
    """
    key: str

    def __init__(self):
        self.key = None

    def set(self, key: str):
        self.key = key

    def clear(self):
        self.key = None

    def is_empty(self):
        return self.key is None


class Gravity(Thread):
    """
    Calls soft drops and regular falling
    """

    game = None
    period: float
    soft_drop: bool = False
    cv: Condition
    stop: bool = False

    def __init__(self, game, cv: Condition):
        super(Gravity, self).__init__(daemon=True)
        self.game = game
        self.calculate_period()
        self.cv = cv

    def run(self):
        fall_counter = 0
        with self.cv:
            while not self.stop:
                if not self.cv.wait(self.period):
                    # there was a timeout (from a hard drop)
                    continue
                fall_counter += 1
                if fall_counter is 2:
                    fall_counter = 0
                    self.game.translate(0)
                elif self.soft_drop:
                    self.game.translate(0)

    def calculate_period(self):
        """
        hey! this is pretty neat:
        with scalar = 1, base = 2, and offset = 16,
        the inverse of this function is 16 times
        a number from the period function
        """
        x = self.game.lines
        self.period = (x + data.SCORE_OFFSET + 1) / (data.SCORE_OFFSET + 1)
        self.period = data.SCORE_SCALAR * log(self.period, data.SCORE_BASE) + 1


class Game:
    """
    Representation Invariant:
    any entry in the tuple 'grid' must be a list
    of length num_cols- an initializing parameter.
    """
    shape_size: int             # > 0. determines many of the following qualities
    grid: tuple                 # tuple of lists of shape keys (Cells)
    ceil_len: int = 0           # RI: must be < len(self.grid)

    lines: int = 0              # number of lines cleared in total
    score: int = 0              # for player (indicates skill?)
    combo: int = 0              # streak of clearing <shape_size> lines with one shape

    next_shape: Shape = None    # for player (helpful to them)
    curr_shape: Shape = None    # current shape falling & being controlled by the player
    stockpile: list             # RI: length should not exceed Data.STOCKPILE_CAPACITY
    position: Tile              # position of the current shape's pivot
    rotation: int               # {0:down=south, 1:down=east, 2:down=north, 3:down=west}

    gravity: Gravity

    @staticmethod
    def new_grid_row(num_cols: int):
        row = ()
        for c in range(num_cols):
            row += Cell()
        return row

    def __init__(self, shape_size: int = 4,
                 num_rows: int = None,
                 num_cols: int = None):
        self.shape_size = shape_size

        # use defaults or floor choices
        # to make sure user doesn't give
        # themselves a bad time
        if num_rows is None:
            num_rows = data.NUM_ROWS[shape_size]
        elif num_rows < shape_size * 4:
            num_rows = shape_size * 4
        if num_cols is None:
            num_cols = data.NUM_COLS[shape_size]
        elif num_cols < shape_size * 2:
            num_cols = shape_size * 2

        grid = ()
        for r in range(num_rows):
            grid += Game.new_grid_row(num_cols)

        self.next_shape = data.get_random_shape(shape_size)
        self.curr_shape = data.get_random_shape(0)
        self.set_curr_shape()

        self.stockpile = []
        for i in range(data.STOCKPILE_CAPACITY):
            self.stockpile.append(None)

        self.position = num_cols / 2
        self.rotation = 0

        self.gravity = Gravity(self, Condition())
        self.gravity.start()

    def stockpile_access(self, slot: int = 0):
        if slot < 0:
            slot = 0
        elif slot >= data.STOCKPILE_CAPACITY:
            slot = data.STOCKPILE_CAPACITY - 1

        tmp: Shape = self.stockpile[slot]
        if tmp is not None:
            # check if the stock shape has room to be swapped-in:
            for t in tmp.tiles:
                x = self.position.x0() + t.x0()
                y = self.position.y0() + t.y0()
                if not self.grid[y][x].is_empty():
                    return

            self.stockpile[slot] = self.curr_shape
            self.curr_shape = tmp
            self.rotation = 0

    @staticmethod
    def calculate_score(num_lines):
        if num_lines is 0:
            return 0
        return 2 * Game.calculate_score(num_lines - 1) + 1

    def handle_clears(self):
        """
        shifts all lines above those cleared down.
        updates the player's score, calculates the
        new period based on the new self.lines, and
        resets the timer.
        """
        lines_cleared = 0
        for y in range(len(self.grid) - self.ceil_len):
            if not any(map(Cell.is_empty, self.grid[y])):
                lines_cleared += 1
                self.grid -= self.grid[y]  # TODO: Not sure if this is legit
                self.grid += Game.new_grid_row(len(self.grid[0]))
        self.lines += lines_cleared

        if lines_cleared is not self.shape_size:
            self.combo = 0

        self.score += Game.calculate_score(lines_cleared + self.combo)
        self.gravity.calculate_period()

        if lines_cleared is self.shape_size:
            self.combo += 1

    def set_curr_shape(self):
        """
        actions performed when a shape
        contacts something underneath itself
        """

        # set the tile data for the shape in self.grid
        for c in self.curr_shape.tiles:
            x = self.position.x0() + c.x[self.rotation]
            y = self.position.y0() + c.y[self.rotation]
            self.grid[y][x].set(self.curr_shape.name)

        # check if lines were cleared, handle if so
        self.handle_clears()

        # get the pivot position for the next tile to spawn in
        shape_ceil = max(map(Tile.y0, self.next_shape.bounds[2]))
        spawn_y = len(self.grid) - self.ceil_len - 1 - shape_ceil
        self.position = Tile(len(self.grid[0]), spawn_y)
        self.rotation = 0

        # check if the next tile has room to spawn
        for t in self.next_shape.tiles:
            x = self.position.x0() + t.x0()
            y = self.position.y0() + t.y0()
            if not self.grid[y][x].is_empty():
                self.gravity.stop = True
                self.gravity.cv.notify()
                # TODO: END THE GAME HERE
                return

        # didn't lose; pass on next shape to current shape
        self.curr_shape = self.next_shape
        self.next_shape = data.get_random_shape(self.shape_size)

    def translate(self, direction: int = 0):
        """
        Automatically calls self.set_curr_shape()
        if at bottom. Returns True if a downward
        translation could not be done: ie. the
        current shape was set.
        """
        la_x = (0, 1, 0, -1)  # horizontal lookahead offsets
        la_y = (-1, 0, 1, 0)  # vertical lookahead offsets
        angle = (self.rotation + direction) % 4
        bounds: tuple = self.curr_shape.bounds[angle]

        for t in bounds:
            x = self.position.x0() + t.x[self.rotation] + la_x[direction]
            y = self.position.y0() + t.y[self.rotation] + la_y[direction]
            if not self.grid[y][x].is_empty():
                if direction == 0:
                    # the shape has something under itself:
                    self.set_curr_shape()
                    return False
                return True  # do not go through a wall

        # translation is valid; execute it
        self.position.x[0] += la_x[direction]
        self.position.y[0] += la_y[direction]
        return True

    def hard_drop(self):
        # translate down until hit bottom or another shape
        not_done = self.translate(0)
        while not_done:
            not_done = self.translate(0)

        # wake up the wait() in self.gravity
        self.gravity.cv.notify()

    def rotate_clockwise(self):
        self.rotation += 1
        self.rotation %= 4

    def rotate_counterclockwise(self):
        self.rotation += 3
        self.rotation %= 4


class GUI:
    """

    """
    game: Game

    def __init__(self):
        game = Game()
