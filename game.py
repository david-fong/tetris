from math import floor
import tkinter
from tkinter import Tk, Frame, Canvas, Label, Menu, StringVar

import data
from shapes import *


class Cell:
    """
    An entry in a Game's grid field.
    Represents a shape's key, which
    can be used to get a color value.
    """
    canvas_id: int
    key: str
    upstairs_neighbor = None  # Another Cell object

    def __init__(self, key: str = data.CELL_EMPTY_KEY):
        self.key = key

    def set_upstairs_neighbor(self, upstairs_neighbor=None):
        if upstairs_neighbor is not None:
            assert isinstance(upstairs_neighbor, Cell)
        self.upstairs_neighbor = upstairs_neighbor

    def catch_falling(self):
        """recursive"""
        if self.upstairs_neighbor is None:
            self.clear()
        else:
            self.key = self.upstairs_neighbor.key
            self.upstairs_neighbor.catch_falling()

    def clear(self):
        self.key = data.CELL_EMPTY_KEY

    def is_empty(self):
        return self.key is data.CELL_EMPTY_KEY

    def __str__(self):
        return ' ' + self.key


class Game:
    """
    Representation Invariant:
    any entry in the tuple 'grid' must be a list
    of length num_cols- an initializing parameter.
    """
    shape_size: int             # > 0. determines many of the following qualities
    dmn: Pair                   # stores the number of rows in y and cols in x
    grid: tuple                 # tuple of lists of shape keys (Cells)
    ceil_len: int = 0           # RI: must be < len(self.grid)

    lines: int = 0              # number of lines cleared in total
    score: int = 0              # for player (indicates skill?)
    combo: int = 0              # streak of clearing <shape_size> lines with one shape

    next_shape: Shape = None    # for player (helpful to them)
    curr_shape: Shape = None    # current shape falling & being controlled by the player
    prev_shapes: list           # queue of previous shapes' name fields
    stockpile: list             # RI: length should not exceed Data.STOCKPILE_CAPACITY
    pos: Pair                   # position of the current shape's pivot
    rot: int                    # {0:down=south, 1:down=east, 2:down=north, 3:down=west}

    def __init__(self,
                 shape_size: int,
                 num_rows: int,
                 num_cols: int
                 ):
        self.shape_size = shape_size
        self.dmn = Pair(num_cols, num_rows)
        grid = []
        for r in range(num_rows + floor(self.shape_size / 2) + 1):
            row = []
            for c in range(num_cols):
                cell = Cell()
                row.append(cell)
                if r is not 0 and r < num_rows:
                    grid[r-1][c].set_upstairs_neighbor(cell)
            grid.append(tuple(row))
        self.grid = tuple(grid)

        # spawn the first shape
        self.prev_shapes = []
        self.stockpile = []
        for i in range(self.shape_size):
            self.stockpile.append(None)
        self.next_shape = data.get_random_shape(self.shape_size, self.prev_shapes)
        self.spawn_next_shape()

    def stockpile_access(self, slot: int = 0):
        """
        switches the current shape with another
        being stored away. select by index, <slot>

        requires that slot is in
        range(data.STOCKPILE_CAPACITY)

        return True if the stockpile at slot
        was empty, and new shape needs to be spawned.
        """
        tmp: Shape = self.stockpile[slot]
        if tmp is None:
            self.stockpile[slot] = self.curr_shape

            return True

        # check if the stock shape has room to be swapped-in:
        for t in tmp.tiles:
            if not self.cell_at_tile(t.p[0]).is_empty():
                return False

        self.stockpile[slot] = self.curr_shape
        self.curr_shape = tmp
        self.rot = 0
        return False

    def handle_clears(self):
        """
        makes lines above cleared lines fall.
        updates the player's score.
        """
        lowest_line = None

        lines_cleared = 0
        y = 0
        range_ = self.dmn.y - self.ceil_len
        while y < range_:
            if any(list(map(Cell.is_empty, self.grid[y]))):
                y += 1
                continue
            lines_cleared += 1
            range_ -= 1
            if lowest_line is None:
                lowest_line = y
            for cell in self.grid[y]:
                cell.catch_falling()
        self.lines += lines_cleared

        if lines_cleared is not self.shape_size:
            self.combo = 0
        score = data.calculate_score(lines_cleared + self.combo)
        # TODO: make score higher if period is shorter
        self.score += score
        if lines_cleared is self.shape_size:
            self.combo += 1

        return lowest_line

    def spawn_next_shape(self):
        """
        called once during initialization, and
        always at the end of set_curr_shape().

        Returns True if there is no room for
        the next shape to spawn and the host
        gui must end the game.
        """
        self.rot = 0
        # get the pivot position for the next tile to spawn in
        shape_ceil = self.next_shape.extreme(self.rot, 2)
        spawn_y = self.dmn.y - (1 + self.ceil_len + shape_ceil)
        self.pos = Pair(floor(self.dmn.x / 2) - 1, spawn_y)

        # check if the next tile has room to spawn
        for t in self.next_shape.tiles:
            if not self.cell_at_tile(t.p[self.rot]).is_empty():
                return True

        # didn't lose; pass on next shape to current shape
        if hasattr(self.curr_shape, 'name'):  # for the __init__ call
            self.prev_shapes.append(self.curr_shape.name)
        if len(self.prev_shapes) >= data.SHAPE_QUEUE_SIZE:
            self.prev_shapes = self.prev_shapes[1:-1]
        self.curr_shape = self.next_shape
        self.next_shape = data.get_random_shape(self.shape_size, self.prev_shapes)
        return False

    def translate(self, direction: int = 0):
        """
        Returns True if a translation could
        not be done: ie. if translating down,
        the host gui must call self.game.set_curr_shape()
        """
        angle = (self.rot + direction) % 4
        for t in self.curr_shape.faces[angle]:
            t_p: Pair = t.p[self.rot].shift(direction)
            if not self.cell_at_tile(t_p).is_empty():
                return True  # was 'direction is 0'

        # translation is valid; execute it
        self.pos = self.pos.shift(direction)
        return False

    def rotate(self, angle: int):
        """
        returns True and performs the
        rotation if it is allowed
        """
        rot = (self.rot + angle) % 4
        for t in self.curr_shape.tiles:
            if not self.cell_at_tile(t.p[rot]).is_empty():
                return False

        self.rot = rot
        return True

    def cell_at_tile(self, p: Pair):
        x = self.pos.x + p.x
        y = self.pos.y + p.y
        if x < 0 or x >= self.dmn.x or y < 0:  # took out 'or y >= self.dmn.y'
            return Cell(data.CELL_WALL_KEY)
        else:
            return self.grid[y][x]

    def __str__(self):
        to_string = ''
        for line in reversed(self.grid):
            for cell in line:
                to_string += str(cell)
            to_string += '\n'
        return to_string


class ShapeFrame(Frame):
    master: Frame
    shape_size: int
    pos: Pair
    canvas: Canvas
    canvas_ids: tuple   # 2D tuple of canvas item ids

    def __init__(self, master: Frame, shape_size: int, name: str):
        super(ShapeFrame, self).__init__(master)
        self.master = master

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
        self.canvas = canvas
        canvas.pack()

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


class GameFrame(Frame):
    """

    """
    master: Frame               # top level frame
    game: Game                  #
    bindings: dict              # map from special constant to a character
    cs: dict                    # a map from color swatches to actual color values
    cs_string_var: StringVar

    canvas: Canvas              #
    stockpile: list             #

    un_paused: bool             #
    score: StringVar            #
    period: float               #
    gravity_after_id = None     # Alarm identifier for after_cancel()

    def __init__(self, master: Tk,
                 num_rows: int, num_cols: int,
                 bindings: dict):
        """

        """
        assert isinstance(master, TetrisApp)
        super(GameFrame, self).__init__(master)
        self.master = master

        game = Game(master.shape_size, num_rows, num_cols)
        self.period = data.get_period(game.lines)
        self.bindings = bindings
        self.cs = data.COLOR_SCHEMES[game.shape_size]['default']
        self.game = game

        self.cs_string_var = master.cs_string_var
        self.cs_string_var.trace('w', self.set_color_scheme)

        # Configure the canvas
        canvas = Canvas(self, bg=self.cs['bg'])
        canvas.configure(
            height=(data.canvas_dmn(game.dmn.y) - data.GUI_CELL_PAD),
            width=(data.canvas_dmn(game.dmn.x) - data.GUI_CELL_PAD),
            relief='flat'
        )
        for y in range(game.dmn.y):
            for x in range(game.dmn.x):
                x0 = data.canvas_dmn(x)
                y0 = data.canvas_dmn(game.dmn.y - 1 - y)
                # create a rectangle canvas item
                # and link it to a Cell object
                cell = game.grid[y][x]
                cell.canvas_id = canvas.create_rectangle(
                    x0, y0, x0 + data.GUI_CELL_WID, y0 + data.GUI_CELL_WID,
                    fill=self.cs[cell.key], tags='%d' % y, width=0
                )
        canvas.pack(side='top')
        self.canvas = canvas
        self.draw_shape()

        # Configure the stockpile display
        stockpile_frame = Frame(self)
        stockpile = []
        for slot in range(len(self.game.stockpile)):
            shape_frame = ShapeFrame(stockpile_frame, self.game.shape_size, str(slot))
            stockpile.append(shape_frame)  # TODO: make this dict from key_binding to ShapeFrame
            shape_frame.grid(row=slot, column=0)
        self.stockpile = stockpile
        stockpile_frame.pack()

        # Configure the score label
        self.score = StringVar()
        self.score.set('left-click to start')
        score_label = Label(self, textvariable=self.score)
        score_label.pack(side='top')

        self.master.bind('<Button-1>', self.start, '+')
        self.master.bind('<Key>', self.decode_move, '+')  # TODO: take out .master?

    def draw_shape(self, erase: bool = False):
        """
        requires that the current Shape is in the grid
        such that all corresponding Cell objects exist.
        """
        game = self.game
        key: str = game.curr_shape.name
        if erase:
            key = data.CELL_EMPTY_KEY
        for t in game.curr_shape.tiles:
            cell = game.cell_at_tile(t.p[game.rot])
            cell.key = key
            if hasattr(cell, 'canvas_id'):
                self.canvas.itemconfigure(
                    cell.canvas_id, fill=self.cs[key]
                )  # else rotated out the top of the grid
        return

    def spawn_next_shape(self):
        if self.game.spawn_next_shape():
            self.draw_shape()
            self.game_over()
        else:
            self.draw_shape()
            # TODO: update next shape display:
            #  self.gui.update_next_shape_canvas

    def set_curr_shape(self):
        """
        actions performed when a shape
        contacts something underneath itself

        call whenever a call to
        Game.translate() returns True
        """
        game = self.game

        # set the tile data for the shape in self.grid
        self.draw_shape()
        key = game.curr_shape.name
        for t in game.curr_shape.tiles:
            game.cell_at_tile(t.p[game.rot]).key = key

        # check if lines were cleared, handle if so
        y = self.game.handle_clears()
        if y is not None:
            # Calculate the value to use as a period
            #  based on the total number of lines cleared
            self.period = data.get_period(self.game.lines)
            # Update the canvas
            for line in self.game.grid[y:self.game.dmn.y - self.game.ceil_len]:
                for cell in line:
                    self.canvas.itemconfigure(
                        tagOrId=cell.canvas_id,
                        fill=self.cs[cell.key]
                    )
            # Update the score label
            self.score.set('%d : %d' % (self.game.lines, self.game.score))

        # Check to see if the game is over:
        self.spawn_next_shape()

    def translate(self, direction: int = 0):
        if self.game.translate(direction) and direction is 0:
            self.set_curr_shape()

    def stockpile_access(self, slot: int):
        # TODO: Update canvases for slot
        self.draw_shape(erase=True)
        if self.game.stockpile_access(slot):
            self.spawn_next_shape()
        self.draw_shape()
        return

    def gravity(self):
        """
        polling function that makes the
        current shape periodically fall
        """
        # terminating condition at game over
        if self.un_paused is None:
            return

        self.draw_shape(erase=True)
        if self.game.translate():
            self.set_curr_shape()
        else:
            self.draw_shape()
        self.gravity_after_id = self.master.after(
            ms=floor(self.period),
            func=self.gravity
        )

    def un_pause_gravity(self):
        self.gravity_after_id = self.master.after(
            ms=floor(self.period),
            func=self.gravity
        )

    def start(self, event):
        if not hasattr(self, 'un_paused'):
            self.un_paused = True
            self.score.set('%d : %d' % (self.game.lines, self.game.score))
            self.un_pause_gravity()
        else:
            self.master.bell()

    def decode_move(self, event):
        if not hasattr(self, 'un_paused') or self.un_paused is None:
            return

        key = event.keysym
        self.draw_shape(erase=True)
        b = self.bindings

        if not self.un_paused:
            if key in b[data.PAUSE]:
                self.un_paused = True
                self.un_pause_gravity()
                self.draw_shape()
                return
            else:
                self.draw_shape()
                return

        if key in b[data.RCC]:
            self.game.rotate(3)
        elif key in b[data.RCW]:
            self.game.rotate(1)

        elif key in b[data.TSD]:
            self.after_cancel(self.gravity_after_id)
            self.translate()
            self.un_pause_gravity()
        elif key in b[data.THD]:
            self.after_cancel(self.gravity_after_id)
            done = self.game.translate()
            while not done:
                done = self.game.translate()
            self.set_curr_shape()
            self.un_pause_gravity()

        elif key in b[data.TSL]:
            self.translate(3)
        elif key in b[data.THL]:
            done = self.game.translate(3)
            while not done:
                done = self.game.translate(3)

        elif key in b[data.TSR]:
            self.translate(1)
        elif key in b[data.THR]:
            done = self.game.translate(1)
            while not done:
                done = self.game.translate(1)

        elif key in b[data.PAUSE] and self.un_paused:
            self.un_paused = False
            self.after_cancel(self.gravity_after_id)

        else:
            try:
                slot = int(key)
                print(slot)
                if slot in range(data.STOCKPILE_CAPACITY):
                    self.stockpile_access(slot)
            except ValueError:
                pass

        self.draw_shape()

    def game_over(self):
        print(self.gravity_after_id)
        self.un_paused = None
        self.after_cancel(self.gravity_after_id)
        return

    def set_color_scheme(self, *args):
        schemes = data.COLOR_SCHEMES[self.game.shape_size]
        self.cs = schemes[self.cs_string_var.get()]
        for y in range(self.game.dmn.y):
            for cell in self.game.grid[y]:
                self.canvas.itemconfigure(
                    cell.canvas_id, fill=self.cs[cell.key]
                )
        self.canvas.configure(bg=self.cs['bg'])
        self.draw_shape()


class TetrisApp(Tk):
    """

    """
    shape_size: int
    cs_string_var: StringVar
    players: tuple

    def __init__(self,
                 shape_size: int = data.DEFAULT_SHAPE_SIZE,
                 num_rows: int = None,
                 num_cols: int = None,
                 num_players: int = 1):
        super(TetrisApp, self).__init__()

        if shape_size not in data.SHAPES.keys():
            shape_size = data.DEFAULT_SHAPE_SIZE
        self.shape_size = shape_size

        if num_rows is None:
            num_rows = data.DEFAULT_NUM_ROWS[shape_size]
        elif num_rows < shape_size * 4:
            num_rows = shape_size * 4
        if num_cols is None:
            num_cols = data.DEFAULT_NUM_COLS[shape_size]
        elif num_cols < shape_size * 2:
            num_cols = shape_size * 2

        if num_players not in data.DEFAULT_BINDINGS.keys():
            num_players = data.DEFAULT_NUM_PLAYERS

        menu = Menu(self)
        colors_menu = Menu(menu)
        menu.add_cascade(label='colors', menu=colors_menu)
        self.configure(menu=menu)

        self.cs_string_var = StringVar()
        for scheme in data.COLOR_SCHEMES[self.shape_size].keys():
            colors_menu.add_radiobutton(
                label=scheme, value=scheme, variable=self.cs_string_var
            )

        assert num_players > 0
        players = []
        for player_num in range(num_players):
            player = GameFrame(
                self, num_rows, num_cols,
                data.get_default_bindings(num_players, player_num)
            )
            player.grid(row=0, column=player_num)
            players.append(player)
        self.players = tuple(players)


def main():
    app = TetrisApp(num_players=2)
    app.mainloop()


main()
