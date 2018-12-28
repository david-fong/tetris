from math import log, floor
from threading import Thread, Condition
import tkinter
from tkinter import Frame, Canvas, Menu, Event, colorchooser

import data
from shapes import *


class Cell:
    """
    An entry in a Game's grid field.
    Represents a shape's key, which
    can be used to get a color value.
    """
    EMPTY = None
    canvas_id: int
    key: str
    upstairs_neighbor = None  # Another Cell object

    def __init__(self):
        self.key = Cell.EMPTY

    def set_upstairs_neighbor(self, upstairs_neighbor=None):
        if upstairs_neighbor is not None:
            assert isinstance(upstairs_neighbor, Cell)
        self.upstairs_neighbor = upstairs_neighbor

    def set_id(self, canvas_id: int):
        self.canvas_id = canvas_id

    def catch_falling(self):
        if self.upstairs_neighbor is None:
            self.clear()
        else:
            self.key = self.upstairs_neighbor.key

    def clear(self):
        self.key = Cell.EMPTY

    def is_empty(self):
        return self.key is Cell.EMPTY


class Game:
    """
    Representation Invariant:
    any entry in the tuple 'grid' must be a list
    of length num_cols- an initializing parameter.

    Start the game by calling self.start()
    """
    shape_size: int             # > 0. determines many of the following qualities
    dmn: Tile                   # stores the number of rows in y and cols in x
    grid: tuple                 # tuple of lists of shape keys (Cells)
    ceil_len: int = 0           # RI: must be < len(self.grid)

    lines: int = 0              # number of lines cleared in total
    score: int = 0              # for player (indicates skill?)
    combo: int = 0              # streak of clearing <shape_size> lines with one shape

    next_shape: Shape = None    # for player (helpful to them)
    curr_shape: Shape = None    # current shape falling & being controlled by the player
    stockpile: list             # RI: length should not exceed Data.STOCKPILE_CAPACITY
    pos: Tile                   # position of the current shape's pivot
    rot: int                    # {0:down=south, 1:down=east, 2:down=north, 3:down=west}

    gui = None

    @staticmethod
    def new_grid_row(num_cols: int):
        row = []
        for c in range(num_cols):
            row.append(Cell())
        return tuple(row)

    def __init__(self, gui,
                 shape_size: int = 4,
                 num_rows: int = None,
                 num_cols: int = None
                 ):
        assert isinstance(gui, GUI)
        self.gui = gui
        self.shape_size = shape_size

        # use defaults or floor choices
        # to make sure user doesn't give
        # themselves a bad time
        if num_rows is None:
            num_rows = data.NUM_ROWS[shape_size]
        elif num_rows < shape_size * 4:
            num_rows = shape_size * 4
        if num_cols is None:
            num_cols = data.NUM_COLS[shape_size]
        elif num_cols < shape_size * 2:
            num_cols = shape_size * 2

        self.dmn = Tile(num_cols, num_rows)
        grid = []
        for r in range(num_rows):
            row = []
            for c in range(num_cols):
                cell = Cell()
                row.append(cell)
                if r is not 0:
                    grid[r-1][c].set_upstairs_neighbor(cell)
            grid.append(tuple(row))
        self.grid = tuple(grid)

        self.stockpile = []
        for i in range(data.STOCKPILE_CAPACITY):
            self.stockpile.append(None)

    def init_curr_shape(self):
        """
        Call after the calling canvas
        is ready to be drawn shapes on
        """
        self.next_shape = data.get_random_shape(self.shape_size)
        self.spawn_next_shape()

    def stockpile_access(self, slot: int = 0):
        """
        switches the current shape with another
        being stored away. select by index, <slot>
        """
        if slot < 0:
            slot = 0
        elif slot >= data.STOCKPILE_CAPACITY:
            slot = data.STOCKPILE_CAPACITY - 1

        tmp: Shape = self.stockpile[slot]
        if tmp is not None:
            # check if the stock shape has room to be swapped-in:
            for t in tmp.tiles:
                x = self.pos.x0() + t.x0()
                y = self.pos.y0() + t.y0()
                if not self.grid[y][x].is_empty():
                    return

            # TODO: update the stockpile canvas
            self.gui.draw_shape(erase=True)
            self.stockpile[slot] = self.curr_shape
            self.curr_shape = tmp
            self.rot = 0
            self.gui.draw_shape()

    def handle_clears(self):
        """
        shifts all lines above those cleared down.
        updates the player's score, calculates the
        new period based on the new self.lines, and
        resets the timer.

        always called at the end of set_curr_shape(),
        just before calling spawn_next_shape().
        """
        lines_cleared = 0
        for y in range(self.dmn.y0() - self.ceil_len):
            if any(map(Cell.is_empty, self.grid[y])):
                continue
            lines_cleared += 1
            for line in self.grid[y:-1]:
                for cell in line:
                    cell.catch_falling()
                    self.gui.canvas.itemconfigure(
                        tagOrId=cell.canvas_id,
                        fill=self.gui.cs[cell.key]
                    )
        self.lines += lines_cleared

        if lines_cleared is not self.shape_size:
            self.combo = 0

        self.score += data.calculate_score(lines_cleared + self.combo)
        self.gui.calculate_period()

        if lines_cleared is self.shape_size:
            self.combo += 1

    def spawn_next_shape(self):
        """
        called once during initialization, and
        always at the end of set_curr_shape().
        """
        # get the pivot position for the next tile to spawn in
        shape_ceil = max(set(map(Tile.y0, self.next_shape.bounds[2])))
        spawn_y = self.dmn.y0() - 1 - self.ceil_len - shape_ceil
        self.pos = Tile(floor(self.dmn.x0() / 2), spawn_y)
        self.rot = 0

        # check if the next tile has room to spawn
        for t in self.next_shape.tiles:
            x = self.pos.x0() + t.x0()
            y = self.pos.y0() + t.y0()
            if not self.grid[y][x].is_empty():
                self.gui.game_over()
                print('game over')
                # TODO: END THE GAME HERE
                return

        # didn't lose; pass on next shape to current shape
        self.curr_shape = self.next_shape
        self.next_shape = data.get_random_shape(self.shape_size)
        self.gui.draw_shape()
        # TODO: update next shape display:
        #  self.gui.update_next_shape_canvas

    def set_curr_shape(self):
        """
        actions performed when a shape
        contacts something underneath itself
        """

        # set the tile data for the shape in self.grid
        for c in self.curr_shape.tiles:
            x = self.pos.x0() + c.x[self.rot]
            y = self.pos.y0() + c.y[self.rot]
            self.grid[y][x].set(self.curr_shape.name)

        # check if lines were cleared, handle if so
        self.handle_clears()

        self.spawn_next_shape()

    def translate(self, direction: int = 0,
                  update_canvas: bool = True):
        """
        Automatically calls self.set_curr_shape()
        if at bottom. Returns True if a downward
        translation could not be done: ie. the
        current shape was set.
        """
        la_x = (0, 1, 0, -1)  # horizontal lookahead offsets
        la_y = (-1, 0, 1, 0)  # vertical lookahead offsets
        angle = (self.rot + direction) % 4
        bounds: tuple = self.curr_shape.bounds[angle]

        for t in bounds:
            x = self.pos.x0() + t.x[self.rot] + la_x[direction]
            y = self.pos.y0() + t.y[self.rot] + la_y[direction]
            if not self.grid[y][x].is_empty():
                if direction == 0:
                    # the shape has something under itself:
                    if not update_canvas:
                        self.gui.draw_shape()
                    self.set_curr_shape()
                    return False
                # do not go through a wall
                return True

        # translation is valid; execute it
        if update_canvas:
            self.gui.draw_shape(erase=True)
        self.pos.x[0] += la_x[direction]
        self.pos.y[0] += la_y[direction]
        if update_canvas:
            self.gui.draw_shape()
        return True

    def hard_drop(self):
        self.gui.draw_shape(erase=True)
        # translate down until hit bottom or another shape
        not_done = self.translate(0, update_canvas=False)
        while not_done:
            not_done = self.translate(0)

    def rotate_clockwise(self):
        self.rot += 1
        self.rot %= 4

    def rotate_counterclockwise(self):
        self.rot += 3
        self.rot %= 4


class UserKey(Frame):
    bind_id: int


class GUI(Frame):
    """

    """
    master: Frame               # top level frame
    game: Game                  #
    cs: dict                    # a map from color swatches to actual color values

    menu: Menu                  #
    canvas: Canvas              #
    virtual_kbd: Frame          # emulates buttons used for playing

    period: int                 #
    soft_drop: bool = False     #
    after_id: int               #

    def __init__(self, master):
        """

        """
        super().__init__(master)
        self.master = master
        self.pack()

        game = Game(self)
        self.game = game
        self.calculate_period()
        self.set_color_scheme()
        canvas = Canvas(self.master, bg=self.cs['bg'])

        self.menu = Menu(master)
        master['menu'] = self.menu

        self.canvas = canvas
        self.canvas.pack(side='left')
        self.canvas['height'] = data.canvas_dmn(game.dmn.y0())
        self.canvas['width'] = data.canvas_dmn(game.dmn.x0())
        for y in range(game.dmn.y0()):
            for x in range(game.dmn.x0()):
                x0 = data.canvas_dmn(x)
                y0 = data.canvas_dmn(game.dmn.y0() - 1 - y)
                item_id: int = self.canvas.create_rectangle(
                    x0, y0, x0 + data.GUI_CELL_WID, y0 + data.GUI_CELL_WID,
                    fill=self.cs[' '], tags='%d' % y, width=0
                )
                game.grid[y][x].set_id(item_id)

        self.game.init_curr_shape()

        self.virtual_kbd = Frame(self.master, bg=self.cs['bg'])
        self.virtual_kbd.pack(side='right')

    def draw_shape(self, erase: bool = False):
        g = self.game
        t: Tile
        for t in g.curr_shape.tiles:
            x = g.pos.x0() + t.x[g.rot]
            y = g.pos.x0() + t.y[g.rot]
            cell = g.grid[y][x]
            if erase:
                cell.clear()
                self.canvas.itemconfigure(
                    cell.id, fill=self.cs[' ']
                )
            else:
                self.canvas.itemconfigure(
                    cell.canvas_id, fill=self.cs[g.curr_shape.name]
                )

    def calculate_period(self):
        """
        hey! this is pretty neat:
        with scalar = 1, base = 2, and offset = 16,
        the inverse of this function is 16 times
        a number from the period function
        """
        x = self.game.lines
        self.period = (x + data.PERIOD_OFFSET + 1) / (data.PERIOD_OFFSET + 1)
        self.period = data.PERIOD_SCALAR * log(self.period, data.PERIOD_BASE) + 1
        self.period *= 1000

    def gravity(self, counter: int = 0):
        counter += 1
        if counter is data.PERIOD_GRANULARITY:
            self.game.translate()
            self.after_id = self.after(
                self.period / data.PERIOD_GRANULARITY,
                func=self.gravity()
            )
        sd_counter = floor(data.PERIOD_GRANULARITY * data.PERIOD_SOFT_DROP)
        if self.soft_drop and (counter is sd_counter):
            self.game.translate()
            self.after_id = self.after(
                self.period / data.PERIOD_GRANULARITY,
                func=self.gravity(counter)
            )

    def start(self, event: Event):
        self.gravity()
        return

    def set_soft_drop(self, event: Event):
        # TODO if press, set True, if release, set False
        return

    def hard_drop(self, event: Event):
        self.after_cancel(self.after_id)
        self.game.hard_drop()
        self.gravity()

    def game_over(self):
        self.after_cancel(self.after_id)
        # TODO:
        return

    def set_color_scheme(self, cs_name: str = 'default'):
        self.cs = data.get_color_scheme(self.game.shape_size, cs_name)


def main():
    """

    """
    root = tkinter.Tk()
    gui = GUI(root)
    gui.start(None)  # TODO: make this by user input in the gui class
    gui.mainloop()


main()
