class Pair:
    x: int
    y: int

    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y

    def shift(self, direction: int):
        la_x = (0, 1, 0, -1)  # horizontal lookahead offsets
        la_y = (-1, 0, 1, 0)  # vertical lookahead offsets
        return Pair(self.x + la_x[direction], self.y + la_y[direction])


class Tile:
    """
    Represents a coordinate pair, which
    represents the horizontal and vertical
    offsets of a single tile in a shape
    from the shape's pivot.
    """
    p: (Pair, Pair, Pair, Pair)

    def __init__(self, x: int, y: int, xor_encl_parity=False, even_base=False):
        p = [Pair(x, y), Pair(y, -x), Pair(-x, -y), Pair(-y, x)]
        if even_base:
            p[1].y += 1
            p[2].y += 1
            p[2].x += 1
            p[3].x += 1
        if xor_encl_parity:
            p[2].y -= 1
        self.p = tuple(p)

    def __eq__(self, other):
        if not isinstance(other, Tile):
            return False
        return self.p[0].x == other.p[0].x and self.p[0].y == other.p[0].y

    def __lt__(self, other):
        if not isinstance(other, Tile):
            return True
        lt = (self.p[0].y < other.p[0].y)
        lt |= self.p[0].y == other.p[0].y and self.p[0].x < other.p[0].x

    def __repr__(self):
        return '(% d, % d)' % (self.p[0].x, self.p[0].y)

    def x0(self):
        return self.p[0].x

    def y0(self):
        return self.p[0].y

    def x_(self, rot: int):
        return self.p[rot].y

    def y_(self, rot: int):
        return self.p[rot].y


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
            col = list(filter(lambda t: t.p[0].x == x, self.tiles))
            bound_000.append(Tile(x, min(map(Tile.y0, col))))
            bound_180.append(Tile(x, max(map(Tile.y0, col))))

        bound_270 = []
        bound_090 = []
        for y in set(map(Tile.y0, self.tiles)):
            # get extremities of each horizontal slice
            row = list(filter(lambda t: t.p[0].y == y, self.tiles))
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
