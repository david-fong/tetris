from math import floor
import tkinter
from tkinter import Frame, Canvas, Button, Menu, Event, colorchooser

import data
from shapes import *


class Cell:
    """
    An entry in a Game's grid field.
    Represents a shape's key, which
    can be used to get a color value.
    """
    EMPTY = ' '
    WALL = None
    canvas_id: int
    key: str
    upstairs_neighbor = None  # Another Cell object

    def __init__(self, key: str = EMPTY):
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
        self.key = Cell.EMPTY

    def is_empty(self):
        return self.key is Cell.EMPTY


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
    stockpile: list             # RI: length should not exceed Data.STOCKPILE_CAPACITY
    pos: Pair                   # position of the current shape's pivot
    rot: int                    # {0:down=south, 1:down=east, 2:down=north, 3:down=west}

    gui = None

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

        self.dmn = Pair(num_cols, num_rows)
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
        if tmp is None:
            return

        # check if the stock shape has room to be swapped-in:
        for t in tmp.tiles:
            if not self.cell_at_tile(t.p[0]).is_empty():
                return

        self.stockpile[slot] = self.curr_shape
        self.curr_shape = tmp
        self.rot = 0

    def handle_clears(self):
        """
        makes lines above cleared lines fall.
        updates the player's score.
        """
        lowest_line = None

        lines_cleared = 0
        for y in range(self.dmn.y - self.ceil_len):
            if any(map(Cell.is_empty, self.grid[y])):
                continue
            if lowest_line is None:
                lowest_line = y
            lines_cleared += 1
            for line in self.grid[y]:
                for cell in line:
                    cell.catch_falling()
        self.lines += lines_cleared

        if lowest_line is None:
            return None

        if lines_cleared is not self.shape_size:
            self.combo = 0
        self.score += data.calculate_score(lines_cleared + self.combo)
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
        # get the pivot position for the next tile to spawn in
        shape_ceil = max(map(Tile.y0, self.next_shape.bounds[2]))
        spawn_y = self.dmn.y - 1 - self.ceil_len - shape_ceil
        self.pos = Pair(floor(self.dmn.x / 2) - 1, spawn_y)
        self.rot = 0

        # check if the next tile has room to spawn
        for t in self.next_shape.tiles:
            if not self.cell_at_tile(t.p[self.rot]).is_empty():
                return True

        # didn't lose; pass on next shape to current shape
        self.curr_shape = self.next_shape
        self.next_shape = data.get_random_shape(self.shape_size)
        return False

    def translate(self, direction: int = 0):
        """
        Returns True if a downward
        translation could not be done:
        ie. the host gui must call
        self.game.set_curr_shape()
        """
        angle = (self.rot + direction) % 4
        bounds: tuple = self.curr_shape.bounds[angle]

        for t in bounds:
            t_p: Pair = t.p[self.rot].shift(direction)
            if not self.cell_at_tile(t_p).is_empty():
                if direction is 0:
                    # the shape has something under itself:
                    return True
                # do not go through a wall
                return False

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
        if x < 0 or x >= self.dmn.x or y < 0 or y >= self.dmn.y:
            return Cell(Cell.WALL)
        else:
            return self.grid[y][x]


class UserKey(Button):
    bind_id: int
    master: Frame
    button: Button

    def __init__(self, master: Frame, key: str, command):
        super().__init__(master)
        self.master = master

        self.configure(
            command=command,
            height=data.GUI_CELL_WID,
            width=data.GUI_CELL_WID,
            bg='white',
            text='key'
        )


class KeyFrame(Frame):
    master: Frame
    rotate_cc: UserKey
    rotate_cw: UserKey
    hard_drop: UserKey
    soft_drop: UserKey
    move_left: UserKey
    move_right: UserKey

    def __init__(self, master: Frame):
        super().__init__(master)
        self.master = master
        self.pack()

        top = Frame(self)
        top.pack('top')
        rotate_cc = UserKey(top)
        rotate_cc.pack('left')

class GUI(Frame):
    """

    """
    master: Frame               # top level frame
    game: Game                  #
    cs: dict                    # a map from color swatches to actual color values

    menu: Menu                  #
    canvas: Canvas              #
    virtual_kbd: Frame          # emulates buttons used for playing

    period: float               #
    soft_drop: bool = False     #
    gravity_after_id = None     # Alarm identifier for after_cancel()

    def __init__(self, master):
        """

        """
        super().__init__(master)
        self.master = master
        self.focus_set()
        self.pack()

        game = Game(self)
        self.game = game
        self.period = data.get_period()
        self.set_color_scheme()
        canvas = Canvas(self.master, bg=self.cs['bg'])

        self.menu = Menu(master)
        master['menu'] = self.menu

        self.canvas = canvas
        self.canvas.pack(side='left')
        self.canvas['height'] = data.canvas_dmn(game.dmn.y)
        self.canvas['width'] = data.canvas_dmn(game.dmn.x)
        self.canvas['relief'] = 'flat'
        for y in range(game.dmn.y):
            for x in range(game.dmn.x):
                x0 = data.canvas_dmn(x)
                y0 = data.canvas_dmn(game.dmn.y - 1 - y)
                # create a rectangle canvas item
                #  and link it to a Cell object
                game.grid[y][x].canvas_id = self.canvas.create_rectangle(
                    x0, y0, x0 + data.GUI_CELL_WID, y0 + data.GUI_CELL_WID,
                    fill=self.cs[' '], tags='%d' % y, width=0
                )

        game.next_shape = data.get_random_shape(game.shape_size)
        game.spawn_next_shape()
        self.draw_shape()

        self.virtual_kbd = Frame(self.master, bg=self.cs['bg'])
        self.virtual_kbd.pack(side='right')

        # self.canvas.bind('<Button-1>', self.start)
        self.master.bind('Key', self.decode_key)

    def draw_shape(self, erase: bool = False):
        """
        requires that the current Shape is in the grid
        such that all corresponding Cell objects exist.
        """
        game = self.game
        key: str = game.curr_shape.name
        for t in game.curr_shape.tiles:
            cell = game.cell_at_tile(t.p[game.rot])
            if erase:
                cell.clear()
                self.canvas.itemconfigure(
                    cell.canvas_id, fill=self.cs[' ']
                )
            else:
                self.canvas.itemconfigure(
                    cell.canvas_id, fill=self.cs[key]
                )
        return

    def set_curr_shape(self):
        """
        actions performed when a shape
        contacts something underneath itself

        call whenever a call to
        Game.translate() returns True
        """
        game = self.game

        # set the tile data for the shape in self.grid
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

        # Check to see if the game is over:
        if self.game.spawn_next_shape():
            self.draw_shape()
            self.game_over()
        else:
            self.draw_shape()
            # TODO: update next shape display:
            #  self.gui.update_next_shape_canvas

    def gravity(self, counter: int = 0):
        """
        polling function that makes the
        current shape periodically fall
        """
        gran = data.PERIOD_GRANULARITY
        counter += 1
        sd_counter = floor(gran * data.PERIOD_SOFT_DROP)
        if counter is gran or (self.soft_drop and counter % sd_counter is 0):
            counter = 0
            print('drop')
            self.draw_shape(erase=True)
            if self.game.translate():
                self.draw_shape()
                print('and set!')
                self.set_curr_shape()
            else:
                self.draw_shape()
        self.gravity_after_id = self.canvas.after(
            ms=(self.period / gran),
            func=self.gravity(counter)
        )

    def start(self, event: Event):
        self.gravity()
        return

    def decode_key(self, event):
        bindings = {
            'rotate_cc': 'q',
            'rotate_cw': 'e',
            'hard_drop': 'w',
            'soft_drop': 's',
            'move_left': 'a',
            'move_right': 'd'
        }
        key: str = event.keysym
        if key not in bindings.values():
            return
        self.draw_shape(erase=True)
        if key is bindings['rotate_cc']:
            self.game.rotate(3)
        elif key is bindings['rotate_cw']:
            self.game.rotate(1)
        elif key is bindings['hard_drop']:
            self.hard_drop()
        elif key is bindings['soft_drop']:
            return  # TODO
        elif key is bindings['move_left']:
            self.game.translate(3)
        elif key is bindings['move_right']:
            self.game.translate(1)
        self.draw_shape()

    def stockpile_access(self, event: Event):
        self.draw_shape(erase=True)

        slot: int  # TODO
        self.game.stockpile_access(slot)

        self.draw_shape()
        return

    def set_soft_drop(self, event: Event):
        # TODO if press, set True, if release, set False
        return

    def hard_drop(self):
        self.after_cancel(self.gravity_after_id)
        # translate down until hit bottom or another shape
        not_done = self.game.translate()
        while not_done:
            not_done = self.game.translate()

        self.set_curr_shape()
        self.gravity()
        return

    def game_over(self):
        print(self.gravity_after_id)
        self.canvas.configure(bg='red')
        self.after_cancel(self.gravity_after_id)
        # TODO:
        return

    def set_color_scheme(self, cs_name: str = 'default'):
        self.cs = data.get_color_scheme(self.game.shape_size, cs_name)


def main():
    """

    """
    root = tkinter.Tk()
    gui = GUI(root)
    gui.mainloop()


main()
