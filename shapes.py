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

    def x_(self, rot: int):
        return self.x[rot]

    def y_(self, rot: int):
        return self.y[rot]


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
