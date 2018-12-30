from math import floor
import tkinter
from tkinter import Frame, Canvas, Button, Menu, colorchooser, StringVar, Label

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
        for r in range(num_rows + floor(self.shape_size / 2) + 1):
            row = []
            for c in range(num_cols):
                cell = Cell()
                row.append(cell)
                if r is not 0 and r < num_rows:
                    grid[r-1][c].set_upstairs_neighbor(cell)
            grid.append(tuple(row))
        self.grid = tuple(grid)

        self.stockpile = []
        for i in range(data.STOCKPILE_CAPACITY):
            self.stockpile.append(None)

        # spawn the first shape
        self.prev_shapes = []
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


class UserKey(Button):
    bind_id: int
    master: Frame
    button: Button

    def __init__(self, master: Frame):
        super().__init__(master)
        self.master = master

        self.configure(
            height=data.GUI_CELL_WID,
            width=data.GUI_CELL_WID,
            bg='white',
            text='key'
        )

    def bind(self, sequence=None, func=None, add=None):
        self.configure(command=func)
        return  # TODO


class KeyFrame(Frame):
    master: Frame
    mappings: dict

    def __init__(self, master: Frame):
        super().__init__(master)
        self.master = master
        self.pack()

        top = Frame(self)
        top.pack('top')
        rotate_cc = UserKey(top)
        rotate_cc.pack('left')

        self.mappings = {
            'rotate_cc': UserKey,
            'rotate_cw': UserKey,
            'hard_drop': UserKey,
            'soft_drop': UserKey,
            'move_left': UserKey,
            'move_right': UserKey
        }


class GUI(Frame):
    """

    """
    master: Frame               # top level frame
    game: Game                  #
    bindings: dict              # map from special constant to a character
    cs: dict                    # a map from color swatches to actual color values
    cs_id: StringVar

    menu: Menu                  #
    canvas: Canvas              #
    virtual_kbd: Frame          # emulates buttons used for playing

    game_on: bool = False       #
    score: StringVar            #
    period: float               #
    soft_drop: bool = False     #
    gravity_after_id = None     # Alarm identifier for after_cancel()

    def __init__(self, master):
        """

        """
        super().__init__(master)
        self.master = master
        self.master.focus_set()
        self.pack()

        game = Game(self)
        self.game = game
        self.period = data.get_period()
        self.bindings = data.get_default_bindings()
        self.cs = data.COLOR_SCHEMES[game.shape_size]['default']

        menu = Menu(master)
        self.menu = menu
        self.master.configure(menu=menu)
        colors_menu = Menu(menu)
        self.cs_id = StringVar()
        self.cs_id.trace('w', self.set_color_scheme)
        menu.add_cascade(label='colors', menu=colors_menu)
        for scheme in data.COLOR_SCHEMES[self.game.shape_size].keys():
            colors_menu.add_radiobutton(
                label=scheme, value=scheme, variable=self.cs_id
            )

        # Configure the canvas
        canvas = Canvas(self.master, bg=self.cs['bg'])
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
                cell = game.grid[y][x]
                cell.canvas_id = self.canvas.create_rectangle(
                    x0, y0, x0 + data.GUI_CELL_WID, y0 + data.GUI_CELL_WID,
                    fill=self.cs[cell.key], tags='%d' % y, width=0
                )
        self.score = StringVar()
        self.score.set(self.game.score)
        score_label = Label(self, textvariable=self.score, anchor='nw')
        score_label.pack()
        self.draw_shape()

        self.virtual_kbd = Frame(self.master, bg=self.cs['bg'])
        self.virtual_kbd.pack(side='right')

        self.master.bind('<Button-1>', self.start)
        self.master.bind('<Key>', self.decode_move)

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
            self.score.set('score: %10d' % self.game.score)

        # Check to see if the game is over:
        self.spawn_next_shape()

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
            self.draw_shape(erase=True)
            if self.game.translate():
                self.set_curr_shape()
            else:
                self.draw_shape()
        self.gravity_after_id = self.master.after(
            floor(self.period / gran),
            self.gravity(counter)
        )

    def start(self, event):
        if not self.game_on:
            self.game_on = True
            # self.gravity()  # activate when gravity is working
        else:
            self.master.bell()

    def stockpile_access(self, slot: int):
        # TODO: Update canvases for slot
        self.draw_shape(erase=True)
        if self.game.stockpile_access(slot):
            self.spawn_next_shape()
        self.draw_shape()
        return

    def translate(self, direction: int = 0):
        if self.game.translate(direction) and direction is 0:
            self.set_curr_shape()

    def decode_move(self, event):
        if not self.game_on:
            return

        key = event.char
        if key is '':
            return  # SHIFT key. ignore.
        self.draw_shape(erase=True)
        b = self.bindings

        if key is b[data.RCC]:
            self.game.rotate(3)
        elif key in b[data.RCW]:
            self.game.rotate(1)

        elif key in b[data.TSD]:
            self.translate()
        elif key in b[data.TSH]:
            # self.after_cancel(self.gravity_after_id)  # TODO: fix after_cancel
            done = self.game.translate()
            while not done:
                done = self.game.translate()
            self.set_curr_shape()
            # self.gravity()  # TODO: fix after_cancel

        elif key in b[data.TSL]:
            self.translate(3)
        elif key in b[data.TSR]:
            self.translate(1)

        elif key in b[data.THL]:
            done = self.game.translate(3)
            while not done:
                done = self.game.translate(3)
        elif key in b[data.THR]:
            done = self.game.translate(1)
            while not done:
                done = self.game.translate(1)

        try:
            slot = int(key)
            print(slot)
            if slot in range(data.STOCKPILE_CAPACITY):
                self.game.stockpile_access(slot)
        except ValueError:
            pass

        self.draw_shape()

    def game_over(self):
        print(self.gravity_after_id)
        self.game_on = False
        self.after_cancel(self.gravity_after_id)
        # TODO:
        return

    def set_color_scheme(self, *args):
        schemes = data.COLOR_SCHEMES[self.game.shape_size]
        self.cs = schemes[self.cs_id.get()]
        for y in range(self.game.dmn.y):
            for cell in self.game.grid[y]:
                self.canvas.itemconfigure(
                    cell.canvas_id, fill=self.cs[cell.key]
                )
        self.canvas.configure(bg=self.cs['bg'])
        self.draw_shape()


def main():
    """

    """
    root = tkinter.Tk()
    gui = GUI(root)
    gui.mainloop()


main()
