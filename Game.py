import Data


class Coordinate:
    """
    Represents a set of coordinate pairs.
    Each coordinate pair represents the
    horizontal and vertical offsets of a
    single tile in a shape from a pivot.
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
        if not isinstance(other, Coordinate):
            return False
        return self.x[0] == other.x[0] and self.y[0] == other.y[0]

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
    height <= base.
    """

    name: str
    tiles: tuple
    bounds: (tuple, tuple, tuple, tuple)

    def __init__(self, tiles: tuple, name: str = '?'):
        self.name = name

        self.tiles = ()
        base = max(map(lambda c: c[0], tiles)) - min(map(lambda c: c[0], tiles))
        height = max(map(lambda c: c[1], tiles)) - min(map(lambda c: c[1], tiles))
        even_base = base % 2 == 0
        xor_encl_parity = even_base ^ (height % 2 == 0)
        for t in tiles:
            self.tiles += Coordinate(t[0], t[1], xor_encl_parity, even_base)

        self.bounds = ((), (), (), ())
        bound_000 = ()
        bound_180 = ()
        for x in set(map(Coordinate.x0, self.tiles)):
            row = filter(lambda c: c.x == x, self.tiles)  # vertical slice
            bound_000 += Coordinate(x, min(map(Coordinate.y0, row)))
            bound_180 += Coordinate(x, max(map(Coordinate.y0, row)))
        bound_270 = ()
        bound_090 = ()
        for y in set(map(Coordinate.y0, self.tiles)):
            row = filter(lambda c: c.y == y, self.tiles)  # horizontal slice
            bound_270 += Coordinate(min(map(Coordinate.x0, row)), y)
            bound_090 += Coordinate(max(map(Coordinate.x0, row)), y)
        self.bounds = (bound_000, bound_090, bound_180, bound_270)


class Game:
    """

    """

    grid: tuple
    next_shape: Shape = None
    curr_shape: Shape = None

    def __init__(self, shape_size: int = 4,
                 num_rows: int = None,
                 num_cols: int = None):
        if num_rows is None:
            num_rows = Data.NUM_ROWS[shape_size]
        if num_cols is None:
            num_cols = Data.NUM_COLS[shape_size]

        grid = ()
        for r in range(num_rows):
            row = []
            for c in range(num_cols):
                row.append('')
            grid += row
