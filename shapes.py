from math import floor
from tkinter import Frame, Canvas, Label

import data


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
    faces: (tuple, tuple, tuple, tuple)

    def __init__(self, pairs: tuple, name: str = '?'):
        self.name = name

        self.tiles = []
        base = max(map(lambda px: px[0], pairs)) - min(map(lambda px: px[0], pairs)) + 1
        height = max(map(lambda py: py[1], pairs)) - min(map(lambda py: py[1], pairs)) + 1
        even_base = base % 2 == 0
        xor_encl_parity = even_base ^ (height % 2 == 0)
        tiles = []
        for p in pairs:
            tiles.append(Tile(p[0], p[1], xor_encl_parity, even_base))
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
        tile = self.faces[(rot + direction) % 4][0]
        pair = tile.p[rot]
        if direction % 2 is 0:
            return pair.y
        else:
            return pair.x


class ShapeFrame(Frame):
    master: Frame
    shape_size: int
    pos: Pair
    canvas: Canvas
    canvas_ids: tuple   # 2D tuple of canvas item ids

    def __init__(self, master: Frame, shape_size: int, name: str):
        super().__init__(master)
        self.master = master
        self.pack()

        self.shape_size = shape_size
        self.pos = Pair(floor(shape_size / 2), floor(shape_size / 2))

        canvas = Canvas(self)
        canvas.configure(
            height=(data.canvas_dmn(shape_size) - data.GUI_CELL_PAD),
            width=(data.canvas_dmn(shape_size) - data.GUI_CELL_PAD)
        )
        canvas_ids = []
        for y in range(shape_size):
            row = []
            for x in range(shape_size):
                x0 = data.canvas_dmn(x)
                y0 = data.canvas_dmn(shape_size - 1 - y)
                canvas_id = canvas.create_rectangle(
                    x0, y0, x0 + data.GUI_CELL_WID, y0 + data.GUI_CELL_WID,
                    width=0
                )
                row.append(canvas_id)
            canvas_ids.append(tuple(row))
        self.canvas_ids = tuple(canvas_ids)

        label = Label(self)
        label.configure(text=str(name))
        label.pack()

    def redraw_shape(self, cs: dict, shape: Shape):
        key = cs[shape.name]
        # clear all drawn tiles
        self.canvas.itemconfigure('ALL', fill=cs[data.CELL_EMPTY_KEY])
        for t in shape.tiles:
            canvas_id = self.id_at_tile(t.p[0])
            self.canvas.configure(canvas_id, fill=cs[key])

    def id_at_tile(self, p: Pair):
        x = self.pos.x + p.x
        y = self.pos.y + p.y
        return self.canvas_ids[y][x]
