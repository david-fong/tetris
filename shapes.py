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
        return '(% d, % d)' % (self.x[0], self.y[0])

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
    tiles: (int, int, int, int)
    bounds: (tuple, tuple, tuple, tuple)

    def __init__(self, pairs: tuple, name: str = '?'):
        self.name = name

        self.tiles = []
        base = max(map(lambda px: px[0], pairs)) - min(map(lambda px: px[0], pairs))
        height = max(map(lambda py: py[1], pairs)) - min(map(lambda py: py[1], pairs))
        even_base = base % 2 == 0
        xor_encl_parity = even_base ^ (height % 2 == 0)
        tiles = []
        for p in pairs:
            tiles.append(Tile(p[0], p[1], xor_encl_parity, even_base))
        self.tiles = tuple(tiles)

        bound_000 = []
        bound_180 = []
        for x in set(map(Tile.x0, self.tiles)):
            # get extremities of each vertical slice
            col = list(filter(lambda t: t.x[0] == x, self.tiles))
            bound_000.append(Tile(x, min(map(Tile.y0, col))))
            bound_180.append(Tile(x, max(map(Tile.y0, col))))

        bound_270 = []
        bound_090 = []
        for y in set(map(Tile.y0, self.tiles)):
            # get extremities of each horizontal slice
            row = list(filter(lambda t: t.y[0] == y, self.tiles))
            bound_270.append(Tile(min(map(Tile.x0, row)), y))
            bound_090.append(Tile(max(map(Tile.x0, row)), y))

        self.bounds = (tuple(bound_000), tuple(bound_090),
                       tuple(bound_180), tuple(bound_270))

    def __eq__(self, other):
        if not isinstance(other, Shape):
            return False
        if len(self.tiles) != len(other.tiles):
            return False
        for t in self.tiles:
            if t not in other.tiles:
                return False
        return True
