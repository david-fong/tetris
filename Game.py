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
            row = filter(lambda t: t.x == x, self.tiles)  # vertical slice
            bound_000 += Tile(x, min(map(Tile.y0, row)))
            bound_180 += Tile(x, max(map(Tile.y0, row)))
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

    def clear(self):
        self.key = None

    def is_empty(self):
        return self.key is None


class Game:
    """
    Representation Invariant:
    any entry in the tuple 'grid' must be a list
    of length num_cols- an initializing parameter.
    """
    shape_size: int             # determines many of the following qualities
    grid: tuple                 # tuple of lists of shape keys (Cells)
    score: tuple                # tuple of ints: each from a unique line(s)-clearing
    period: float               # 2 / SCALAR_1 / ((score / SCALAR_2 + 1) ** 2 - 1)

    next_shape: Shape = None    # to display for the player (helpful to them)
    curr_shape: Shape = None    # current shape falling & being controlled by the player
    save_shape: list            # TODO: length should not exceed SAVE_LEN
    position: Tile        # position of the current shape's pivot
    rotation: int               # {0:down=south, 1:down=east, 2:down=north, 3:down=west}

    def __init__(self, shape_size: int = 4,
                 num_rows: int = None,
                 num_cols: int = None):
        self.shape_size = shape_size
        self.score = 0

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
            row = ()
            for c in range(num_cols):
                row += Cell()  # TODO: decide if this should be null
            grid += row

        self.next_shape = Data.get_random_shape(shape_size)
        self.curr_shape = Data.get_random_shape(shape_size)

        self.position = num_cols / 2
        self.rotation = 0

    def translate_allowed(self, direction: int = 0):
        la_x = (0, 1, 0, -1)  # horizontal lookahead offsets
        la_y = (-1, 0, 1, 0)  # vertical lookahead offsets
        angle = (self.rotation + direction) % 4
        bounds: tuple = self.curr_shape.bounds[angle]
        for t in bounds:
            x = self.position.x0() + t.x[self.rotation] + la_x[direction]
            y = self.position.y0() + t.y[self.rotation] + la_y[direction]

            if not self.grid[y][x].is_empty():
                return False
        return True

    def rotate_clockwise(self):
        self.rotation += 1
        self.rotation %= 4

    def rotate_counterclockwise(self):
        self.rotation += 3
        self.rotation %= 4

    def set_curr_shape(self):
        """
        actions performed when a shape
        contacts something underneath itself
        """

        # set the current shape
        score: int = 0

        self.curr_shape = self.next_shape
        self.next_shape = Data.get_random_shape(self.shape_size)

        # TODO: calculate spawn position
        self.rotation = 0

        return score
