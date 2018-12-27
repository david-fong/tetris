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
    __EMPTY = None
    key: str
    upstairs_neighbor = None  # Another Cell object

    def __init__(self, upstairs_neighbor=None):
        self.key = Cell.__EMPTY
        assert isinstance(upstairs_neighbor, Cell)
        self.upstairs_neighbor = upstairs_neighbor

    def set(self, key: str):
        self.key = key

    def catch_falling(self):
        if self.upstairs_neighbor is None:
            self.key = None
        else:
            self.key = self.upstairs_neighbor.key

    def is_empty(self):
        return self.key is Cell.__EMPTY


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
        self.period = (x + data.PERIOD_OFFSET + 1) / (data.PERIOD_OFFSET + 1)
        self.period = data.PERIOD_SCALAR * log(self.period, data.PERIOD_BASE) + 1


class Game:
    """
    Representation Invariant:
    any entry in the tuple 'grid' must be a list
    of length num_cols- an initializing parameter.

    Start the game by calling self.start()
    """
    shape_size: int             # > 0. determines many of the following qualities
    dimensions: Tile            # stores the number of rows in y and cols in x
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

        self.dimensions = Tile(num_cols, num_rows)
        grid = ()
        for row in range(num_rows):
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

    def start(self):
        """
        Used to make gravity start applying
        """
        self.gravity.start()

    def stockpile_access(self, slot: int = 0):
        """
        switches the current shape with another
        being stored away. select by index, <slot>
        """
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

    def handle_clears(self):
        """
        shifts all lines above those cleared down.
        updates the player's score, calculates the
        new period based on the new self.lines, and
        resets the timer.
        """
        lines_cleared = 0
        for y in range(self.dimensions.y0() - self.ceil_len):
            if not any(map(Cell.is_empty, self.grid[y])):
                lines_cleared += 1
                for line in self.grid[y:-1]:
                    for cell in line:
                        cell.catch_falling()
        self.lines += lines_cleared

        if lines_cleared is not self.shape_size:
            self.combo = 0

        self.score += data.calculate_score(lines_cleared + self.combo)
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
        spawn_y = self.dimensions.y0() - 1 - self.ceil_len - shape_ceil
        self.position = Tile(self.dimensions.x0(), spawn_y)
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
