class Shape:
    """Documentation goes here"""
    color = 0x000000
    tiles = ()
    bounds = ((), (), (), ())

    def __init__(self, color, tiles):
        for c in tiles:
            if not isinstance(c, Coordinate):
                c = Coordinate(c.x, c.y)

        self.color = color
        self.tiles = tiles
        self.bounds = ((), (), (), ())

        down_bound = ()
        up_bound = ()
        for x in set(map(lambda c: c.x, tiles)):
            row = filter(lambda c: c.x == x, tiles)
            db = min(map(lambda c: c.y[0], tiles))
            ub = max(map(lambda c: c.y[0], tiles))
            down_bound += filter(lambda c: c.y == db, row)
            up_bound += filter(lambda c: c.y == ub, row)

        left_bound = ()
        right_bound = ()
        for y in set(map(lambda c: c.y, tiles)):
            row = filter(lambda c: c.y == y, tiles)
            lb = min(map(lambda c: c.x[0], tiles))
            rb = max(map(lambda c: c.x[0], tiles))
            left_bound += filter(lambda c: c.x == lb, row)
            right_bound += filter(lambda c: c.x == rb, row)

        self.bounds = (down_bound, right_bound, up_bound, left_bound)


class Coordinate:
    x = (0, 0, 0, 0)
    y = (0, 0, 0, 0)

    def __init__(self, x, y):
        self.x = (x, y, -x, -y)
        self.y = (y, -x, -y, x)
