from math import ceil


class Pair:
    """
    A coordinate in 2D space.
    """
    x: int
    y: int

    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y

    def shift(self, direction: int):
        la_x = (0, 1, 0, -1)  # horizontal lookahead offsets
        la_y = (-1, 0, 1, 0)  # vertical lookahead offsets
        return Pair(self.x + la_x[direction], self.y + la_y[direction])

    def __eq__(self, other):
        if not isinstance(other, Pair):
            return False
        return self.x is other.x and self.y is other.y

    def __str__(self):
        return '(% d, % d)' % (self.x, self.y)


class Tile:
    """
    Represents an offset from a pivot, with four
    views: one for each clockwise 90 degree rotation.
    Each view is represented by a Pair object.
    """
    p: (Pair, Pair, Pair, Pair)

    def __init__(self, x: int, y: int, base: int, height: int, bottom_heavy: bool):
        x -= int(base / 2)  # bias pivot to right
        y -= int(height / 2)  # bias pivot to top
        p = [Pair(x, y), Pair(y, -x), Pair(-x, -y), Pair(-y, x)]

        if base % 2 is 0:
            if height % 2 is 0:
                p[1].y -= 1
            p[2].x -= 1
            p[3].x -= 1
        if height % 2 is 0:
            p[2].y -= 1
            if base % 2 is 1 and bottom_heavy:
                p[1].x += 1
                p[3].x -= 1

        self.p = tuple(p)

    def __eq__(self, other):
        if not isinstance(other, Tile):
            return False
        eq: True
        for i in range(4):
            eq = eq and self.p[i].__eq__(other.p[i])
        return eq

    def __repr__(self):
        return '(%s, %s, %s, %s)' % (
            str(self.p[0]), str(self.p[1]), str(self.p[2]), str(self.p[3])
        )

    def x0(self):
        return self.p[0].x

    def y0(self):
        return self.p[0].y


class Shape:
    """
    A collection of uniquely positioned
    tiles with a shared pivot point.

    Orient the default position following
    rule: height <= base.
    The game using this shape will require
    that base, height <= shape_size.
    """

    name: str
    tiles: (Tile, )
    faces: ((Tile, ), (Tile, ), (Tile, ), (Tile, ))

    def __init__(self, pairs: ((int, int), ), name: str):
        self.name = name

        assert len(pairs) > 0
        for p in pairs:
            assert p[0] >= 0 and p[1] >= 0

        # Initialize self.tiles
        base = max(map(lambda px: px[0], pairs)) - min(map(lambda px: px[0], pairs)) + 1
        height = max(map(lambda py: py[1], pairs)) - min(map(lambda py: py[1], pairs)) + 1
        low_pass_filter = list(filter(lambda cp: cp[1] <= ceil(height / 2) - 1, pairs))
        bottom_heavy: bool = len(low_pass_filter) >= (len(pairs) / 2)
        # print(name, 'bottom heavy?:', bottom_heavy)
        assert base >= height
        tiles = []
        for p in pairs:
            tiles.append(Tile(p[0], p[1], base, height, bottom_heavy))
        self.tiles = tuple(tiles)

        face_000 = []
        face_180 = []
        # get extremities of each vertical slice
        for x in sorted(list(set(map(Tile.x0, self.tiles)))):
            col = list(filter(lambda t: t.p[0].x == x, self.tiles))
            col.sort(key=Tile.y0)
            face_000.append(col[0])
            face_180.append(col[-1])
        # sort faces by decreasing extremity
        face_000.sort(key=Tile.y0)
        face_180.sort(key=Tile.y0, reverse=True)

        face_270 = []
        face_090 = []
        # get extremities of each horizontal slice
        for y in sorted(list(set(map(Tile.y0, self.tiles)))):
            row = list(filter(lambda t: t.p[0].y == y, self.tiles))
            row.sort(key=Tile.x0)
            face_270.append(row[0])
            face_090.append(row[-1])
        # sort faces by decreasing extremity
        face_270.sort(key=Tile.x0)
        face_090.sort(key=Tile.x0, reverse=True)

        self.faces = (tuple(face_000), tuple(face_090),
                      tuple(face_180), tuple(face_270))

    def __eq__(self, other):
        if not isinstance(other, Shape):
            return False
        if len(self.tiles) != len(other.tiles):
            return False
        for t in self.tiles:
            if t not in other.tiles:
                return False
        return True

    def extreme(self, rot: int, direction: int):
        """
        Returns the maximum distance of a tile
        from its parent shape's current position,
        in its current rotation with respect to
        the specified direction.
        """
        tile = self.faces[(rot + direction) % 4][0]
        pair = tile.p[rot]
        if direction % 2 is 0:
            return pair.y
        else:
            return pair.x
