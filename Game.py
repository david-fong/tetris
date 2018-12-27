from threading import Thread, Lock, Condition

import Data


class Tile:
    """
    Represents a coordinate pair, which
    represents the horizontal and vertical
    offsets of a single tile in a shape
    from the shape's pivot.
    """

    x: (int, int, int, int) = (0, 0, 0, 0)
    y: (int, int, int, int) = (0, 0, 0, 0)

    def __init__(self, x: int, y: int, xor_encl_parity=False, even_base=False):
        x_tmp = [x, y, -x, -y]
        y_tmp = [y, -x, -y, x]
        if even_base:
            y_tmp[1] += 1
            y_tmp[2] += 1
            x_tmp[2] += 1
            x_tmp[3] += 1
        if xor_encl_parity:  # not even-sided square enclosure
            y_tmp[2] -= 1
        self.x = tuple(x_tmp)
        self.y = tuple(y_tmp)

    def __eq__(self, other):
        if not isinstance(other, Tile):
            return False
        return self.x[0] == other.x[0] and self.y[0] == other.y[0]

    def __lt__(self, other):
        if not isinstance(other, Tile):
            return True
        lt = (self.y[0] < other.y[0])
        lt |= self.y[0] == other.y[0] and self.x[0] < other.y[0]

    def __repr__(self):
        return '({}, {})'.format(self.x[0], self.y[0])

    def x0(self):
        return self.x[0]

    def y0(self):
        return self.y[0]


class Shape:
    """
    A collection of uniquely positioned
    tiles with a shared pivot point.

    Orient the default position following
    rule: height <= base.
    """

    name: str
    tiles: tuple
    bounds: (tuple, tuple, tuple, tuple)

    def __init__(self, tiles: tuple, name: str = '?'):
        self.name = name

        self.tiles = ()
        base = max(map(lambda px: px[0], tiles)) - min(map(lambda px: px[0], tiles))
        height = max(map(lambda py: py[1], tiles)) - min(map(lambda py: py[1], tiles))
        even_base = base % 2 == 0
        xor_encl_parity = even_base ^ (height % 2 == 0)
        for p in tiles:
            self.tiles += Tile(p[0], p[1], xor_encl_parity, even_base)

        self.bounds = ((), (), (), ())
        bound_000 = ()
        bound_180 = ()
        for x in set(map(Tile.x0, self.tiles)):
            col = filter(lambda t: t.x == x, self.tiles)  # vertical slice
            bound_000 += Tile(x, min(map(Tile.y0, col)))
            bound_180 += Tile(x, max(map(Tile.y0, col)))
        bound_270 = ()
        bound_090 = ()
        for y in set(map(Tile.y0, self.tiles)):
            row = filter(lambda t: t.y == y, self.tiles)  # horizontal slice
            bound_270 += Tile(min(map(Tile.x0, row)), y)
            bound_090 += Tile(max(map(Tile.x0, row)), y)
        self.bounds = (bound_000, bound_090, bound_180, bound_270)

    def __eq__(self, other):
        if not isinstance(other, Shape):
            return False
        if len(self.tiles) != len(other.tiles):
            return False
        for t in self.tiles:
            if t not in other.tiles:
                return False
        return True


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
    period: float  # 2 / SCALAR_1 / ((score / SCALAR_2 + 1) ** 2 - 1)
    soft_drop: bool
    cv = None

    def __init__(self, game, cv: Condition):
        super(Gravity, self).__init__(daemon=True)
        self.game = game
        self.calculate_period(0)
        self.soft_drop = False
        self.cv = cv

    def run(self):
        fall_counter = 0
        with self.cv:
            while True:
                if not self.cv.wait(self.period):
                    continue  # there was a timeout (from a hard drop)
                fall_counter += 1
                if fall_counter is 2:
                    fall_counter = 0
                    self.game.translate(0)
                elif self.soft_drop:
                    self.game.translate(0)

    def calculate_period(self, score: int):
        self.period = 2 / Data.SCALAR_1 / ((score / Data.SCALAR_2 + 1) ** 2)
        # Data.SCALAR_3 * (math.log(score + 1, Data.BASE) + 1)


class Game:
    """
    Representation Invariant:
    any entry in the tuple 'grid' must be a list
    of length num_cols- an initializing parameter.
    """
    shape_size: int             # > 0. determines many of the following qualities
    grid: tuple                 # tuple of lists of shape keys (Cells)
    ceil_len: int = 0           # RI: must be < len(self.grid)
    score: int = 0              # tuple of ints: each from a unique line(s)-clearing
    combo_streak: int = 0

    next_shape: Shape = None    # to display for the player (helpful to them)
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

        if num_rows is None:
            num_rows = Data.NUM_ROWS[shape_size]
        elif num_rows < shape_size * 4:
            num_rows = shape_size * 4
        if num_cols is None:
            num_cols = Data.NUM_COLS[shape_size]
        elif num_cols < shape_size * 2:
            num_cols = shape_size * 2

        grid = ()
        for r in range(num_rows):
            grid += Game.new_grid_row(num_cols)

        self.next_shape = Data.get_random_shape(shape_size)
        self.curr_shape = Data.get_random_shape(shape_size)
        self.stockpile = []
        for i in range(Data.STOCKPILE_CAPACITY):
            self.stockpile.append(None)

        self.position = num_cols / 2
        self.rotation = 0

        self.gravity = Gravity(self, Condition())
        self.gravity.start()

    def stockpile_access(self, slot: int = 0):
        if slot < 0:
            slot = 0
        elif slot >= Data.STOCKPILE_CAPACITY:
            slot = Data.STOCKPILE_CAPACITY - 1

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
        new period based on the new score, and
        resets the timer.
        """
        lines_cleared = 0
        for y in range(len(self.grid) - self.ceil_len):
            if not any(map(Cell.is_empty, self.grid[y])):
                lines_cleared += 1
                self.grid -= self.grid[y]  # TODO: Not sure if this is legit
                self.grid += Game.new_grid_row(len(self.grid[0]))

        if lines_cleared is not self.shape_size:
            self.combo_streak = 0

        self.score += Game.calculate_score(lines_cleared + self.combo_streak)
        self.gravity.calculate_period(self.score)

        if lines_cleared is self.shape_size:
            self.combo_streak += 1

    def set_curr_shape(self):
        """
        actions performed when a shape
        contacts something underneath itself
        """

        for c in self.curr_shape.tiles:
            x = self.position.x0() + c.x[self.rotation]
            y = self.position.y0() + c.y[self.rotation]
            self.grid[y][x].set(self.curr_shape.name)

        self.handle_clears()  # check if lines were cleared, handle if so

        self.curr_shape = self.next_shape
        self.next_shape = Data.get_random_shape(self.shape_size)

        shape_ceil = max(map(Tile.y0, self.curr_shape.bounds[2]))
        spawn_y = len(self.grid) - self.ceil_len - 1 - shape_ceil
        self.position = Tile(len(self.grid[0]), spawn_y)
        self.rotation = 0

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
                    self.set_curr_shape()  # the shape has something under itself
                    return False

        self.position.x[0] += la_x[direction]
        self.position.y[0] += la_y[direction]
        return True

    def hard_drop(self):
        not_done = self.translate(0)
        while not_done:
            not_done = self.translate(0)
        self.gravity.cv.notify()  # wake up the wait() in self.gravity

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
