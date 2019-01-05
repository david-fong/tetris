from tkinter import Tk, Frame, Canvas, Label, Menu, StringVar, IntVar, messagebox

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
    grid: ([Cell, ], )          # tuple of lists of shape keys (Cells)
    ceil_len: int = 0           # RI: must be < len(self.grid)

    lines: int = 0              # number of lines cleared in total
    score: int = 0              # for player (indicates skill?)
    combo: int = 0              # streak of clearing <shape_size> lines with one shape

    shape_set: str              # a key for this shape_size to a set of shapes
    next_shape: Shape = None    # for player (helpful to them)
    curr_shape: Shape = None    # current shape falling & being controlled by the player
    prev_shapes: [str, ]        # queue of previous shapes' name fields
    stockpile: [str, ]          # shape keys. RI: length should not exceed Data.STOCKPILE_CAPACITY
    pos: Pair                   # position of the current shape's pivot
    rot: int                    # {0:down=south, 1:down=east, 2:down=north, 3:down=west}

    def __init__(self,
                 shape_size: int,
                 num_rows: int,
                 num_cols: int,
                 shape_set: str
                 ):
        self.shape_size = shape_size
        self.dmn = Pair(num_cols, num_rows)
        grid = []
        for r in range(num_rows + int(self.shape_size / 2) + 1):
            row = []
            for c in range(num_cols):
                cell = Cell()
                row.append(cell)
                if r is not 0 and r < num_rows:
                    grid[r-1][c].set_upstairs_neighbor(cell)
            grid.append(tuple(row))
        self.grid = tuple(grid)

        # spawn the first shape
        self.curr_shape = None
        self.shape_set = None
        self.change_shape_set(shape_set)

    def stockpile_access(self, slot: int):
        """
        switches the current shape with another
        being stored away. select by index, <slot>

        requires that slot is in
        range(data.STOCKPILE_CAPACITY)

        return True if the stockpile at slot
        was empty, and new shape needs to be spawned.
        """
        slot_copy: str = self.stockpile[slot]
        if slot_copy is data.SHAPE_EMPTY_NAME:
            self.stockpile[slot] = self.curr_shape.name
            return True

        slot_shape = data.SHAPES[self.shape_size][self.shape_set][slot_copy]

        # check if the stock shape has no room to be swapped-in:
        for t in slot_shape.tiles:
            if not self.cell_at_tile(t.p[0]).is_empty():
                return False

        self.stockpile[slot] = self.curr_shape.name
        self.curr_shape = slot_shape
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
        Also called when changing shape_set

        Returns True if there is no room for
        the next shape to spawn and the host
        gui must end the game.
        """
        self.rot = 0
        # get the pivot position for the next tile to spawn in
        shape_ceil = self.next_shape.extreme(self.rot, 2)
        spawn_y = self.dmn.y - (1 + self.ceil_len + shape_ceil)
        self.pos = Pair(int(self.dmn.x / 2), spawn_y)

        # check if the next tile has room to spawn
        for t in self.next_shape.tiles:
            if not self.cell_at_tile(t.p[self.rot]).is_empty():
                return True

        # didn't lose; pass on next shape to current shape
        if self.curr_shape is not None:  # for the __init__ call
            self.prev_shapes.append(self.curr_shape.name)
        if len(self.prev_shapes) >= data.SHAPE_QUEUE_SIZE:
            self.prev_shapes = self.prev_shapes[1:-1]
        self.curr_shape = self.next_shape
        self.next_shape = data.get_random_shape(
            self.shape_size, self.shape_set, self.prev_shapes
        )
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

    def restart(self):
        self.lines = 0
        self.combo = 0
        self.score = data.calculate_score(self.lines)

        # TODO: add a HIGH_SCORES dict to data?
        #  would be cool if it saved by player name too.

        for line_num in range(self.dmn.y):
            for cell in self.grid[line_num]:
                cell.clear()

        for slot in range(self.shape_size):
            self.stockpile[slot] = data.SHAPE_EMPTY_NAME

        self.prev_shapes = []
        self.curr_shape = None
        self.next_shape = data.get_random_shape(
            self.shape_size, self.shape_set, self.prev_shapes
        )
        self.spawn_next_shape()

    def change_shape_set(self, shape_set: str):
        not_compatible: bool = False
        if self.shape_set is not None:
            # Check to see if the key sets (shape names) are the same
            for key in data.SHAPES[self.shape_size][self.shape_set].keys():
                if key not in data.SHAPES[self.shape_size][shape_set].keys():
                    not_compatible = True
                    break
        else:
            not_compatible = True

        self.shape_set = shape_set
        if not_compatible:
            # Clear previous shape data and stockpile
            self.prev_shapes = []
            self.stockpile = []
            for i in range(self.shape_size):
                self.stockpile.append(data.SHAPE_EMPTY_NAME)

        self.next_shape = data.get_random_shape(
            self.shape_size, self.shape_set, self.prev_shapes
        )
        self.spawn_next_shape()

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
    """
    Used to display the shape in a Game object's
    stockpile at a specific slot. Labeled with the
    key a user should press to access this slot.
    """
    parent_game = None
    shape_size: int
    pos: Pair
    canvas: Canvas
    canvas_ids: tuple   # 2D tuple of canvas item ids
    label: Label

    def __init__(self, master: Frame, shape_size: int, cs: dict, name: str):
        super(ShapeFrame, self).__init__(master)
        self.parent_game = master.master
        assert isinstance(self.parent_game, GameFrame)

        self.shape_size = shape_size
        self.pos = Pair(int(shape_size / 2), int(shape_size / 2))

        self.label = Label(self, text=str(name))
        self.label.pack()

        canvas = Canvas(self, relief='flat', bd=0)
        canvas.configure(
            height=(data.canvas_dmn(shape_size) - data.GUI_CELL_PAD),
            width=(data.canvas_dmn(shape_size) - data.GUI_CELL_PAD),
        )
        canvas_ids = []
        for y in range(shape_size):
            row = []
            for x in range(shape_size):
                x0 = data.canvas_dmn(x)
                y0 = data.canvas_dmn(shape_size - 1 - y)
                canvas_id = canvas.create_rectangle(
                    x0, y0, x0 + data.GUI_CELL_WID, y0 + data.GUI_CELL_WID,
                    width=0, fill=cs[data.CELL_EMPTY_KEY]
                )
                row.append(canvas_id)
            canvas_ids.append(tuple(row))
        self.canvas_ids = tuple(canvas_ids)
        self.canvas = canvas
        canvas.pack()

    def redraw_shape(self, name: str):
        # clear all drawn tiles
        self.canvas.itemconfigure(
            'all', fill=self.parent_game.cs[data.CELL_EMPTY_KEY]
        )

        shape_set = data.SHAPES[self.shape_size][self.parent_game.shape_set.get()]
        if name is not data.SHAPE_EMPTY_NAME:
            color = self.parent_game.cs[name]
            for t in shape_set[name].tiles:
                canvas_id = self.id_at_tile(t.p[0])
                self.canvas.itemconfigure(canvas_id, fill=color)

    def set_color_scheme(self):
        cs = self.parent_game.cs
        self.configure(bg=cs['bg'])
        self.canvas.configure(bg=cs['grid-lines'])
        self.label.configure(bg=cs['bg'], fg=cs['text'])

    def id_at_tile(self, p: Pair):
        x = self.pos.x + p.x
        y = self.pos.y + p.y
        return self.canvas_ids[y][x]


class GameFrame(Frame):
    """
    Displays the Game object corresponding to a
    specific player (there may be multiple).
    """
    master: Frame               # top level frame
    game: Game                  #
    bindings: {int: str, }      # map from special constant to a list of keysym strings
    cs: {str: str, }            # a map from color swatches to actual color values

    speed_index_int_var: IntVar
    shape_set: StringVar        #
    cs_string_var: StringVar    #

    next_shape: ShapeFrame      #
    canvas: Canvas              #
    stockpile: [ShapeFrame, ]   #

    un_paused: bool             #
    score: StringVar            #
    score_label: Label          #
    period: float               #
    gravity_after_id = None     # Alarm identifier for after_cancel()

    def configure_canvas(self, grid_frame: Frame):
        """
        initializes a canvas of rectangle items
        corresponding to cells in the game field's grid
        """
        game = self.game
        canvas = Canvas(grid_frame, relief='flat', bd=0)
        canvas.configure(
            height=(data.canvas_dmn(game.dmn.y) - data.GUI_CELL_PAD),
            width=(data.canvas_dmn(game.dmn.x) - data.GUI_CELL_PAD),
        )
        # draw cells for each cell in the game
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

    def __init__(self, master: Tk,
                 num_rows: int, num_cols: int,
                 bindings: dict):
        """
        initializes a GameFrame instance
        """
        assert isinstance(master, TetrisApp)
        super(GameFrame, self).__init__(master)
        self.master = master

        game = Game(
            master.shape_size,
            num_rows,
            num_cols,
            master.shapes_string_var.get()
        )
        self.game = game
        self.bindings = bindings
        self.cs = data.COLOR_SCHEMES[game.shape_size]['default']
        # Associate the parent's speed variable to update
        self.speed_index_int_var = master.speed_index_int_var
        self.speed_index_int_var.trace('w', self.set_period)
        self.set_period()
        # Associate the parent's shape set variable to update
        self.shape_set = master.shapes_string_var
        self.shape_set.trace('w', self.change_shape_set)
        # Associate the parent's color scheme variable to update
        self.cs_string_var = master.cs_string_var
        self.cs_string_var.trace('w', self.set_color_scheme)

        grid_frame = Frame(self)
        grid_frame.pack(side='left', expand=False)

        # Configure the score label
        self.score = StringVar()
        self.score.set('left-click to start')
        self.score_label = Label(grid_frame, textvariable=self.score)
        self.score_label.pack(side='top')

        # Configure the next shape display
        self.next_shape = ShapeFrame(
            grid_frame,
            master.shape_size,
            self.cs, 'next shape:'
        )
        self.next_shape.pack(side='top')
        self.next_shape.redraw_shape(self.game.next_shape.name)

        # Configure the canvas
        self.configure_canvas(grid_frame)

        # Configure the stockpile display
        stockpile_frame = Frame(self)
        stockpile = []
        for slot in range(len(self.game.stockpile)):
            shape_frame = ShapeFrame(
                stockpile_frame,
                self.game.shape_size,
                self.cs,
                (str(bindings[data.STOCKPILE][slot]))
            )
            stockpile.append(shape_frame)
            shape_frame.grid(row=slot, column=0)
        self.stockpile = stockpile
        stockpile_frame.pack(side='bottom', expand=False)

        self.set_color_scheme()
        self.master.bind('<Button-1>', self.start, '+')
        self.master.bind('<Key>', self.decode_move, '+')
        # TODO: bind to a custom event that makes ceiling length increase

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
            self.next_shape.redraw_shape(self.game.next_shape.name)

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
            self.set_period()
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
        self.draw_shape(erase=True)
        if self.game.stockpile_access(slot):
            self.spawn_next_shape()
        self.draw_shape()

        self.stockpile[slot].redraw_shape(self.game.stockpile[slot])

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

        if self.un_paused:
            # above if statement not absolutely necessary.
            self.gravity_after_id = self.master.after(
                ms=int(self.period),
                func=self.gravity
            )

    def un_pause_gravity(self):
        self.gravity_after_id = self.master.after(
            ms=int(self.period),
            func=self.gravity
        )

    def start(self, event):
        if not hasattr(self, 'un_paused'):
            self.un_paused = True
            self.score.set('%d : %d' % (self.game.lines, self.game.score))
            self.un_pause_gravity()
        else:
            self.master.bell()

    def restart(self):
        self.after_cancel(self.gravity_after_id)
        self.game.restart()
        self.set_period()
        self.score.set('%d : %d' % (self.game.lines, self.game.score))
        self.set_color_scheme()
        self.un_paused = True
        self.un_pause_gravity()

    def decode_move(self, event):
        key = event.keysym
        b = self.bindings
        if not hasattr(self, 'un_paused'):
            return  # game hasn't even started yet
        if key in b[data.RESTART]:
            self.restart()
            return
        if self.un_paused is None:
            return  # game is paused
        self.draw_shape(erase=True)

        # Game paused
        if not self.un_paused:
            if key in b[data.PAUSE]:
                self.un_paused = True
                self.un_pause_gravity()
                self.draw_shape()
                return
            else:
                self.draw_shape()  # Undo the erase first
                return

        # Rotation
        if key in b[data.RCC]:
            self.game.rotate(3)
        elif key in b[data.RCW]:
            self.game.rotate(1)

        # Downward translation
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

        # Left translation
        elif key in b[data.TSL]:
            self.translate(3)
        elif key in b[data.THL]:
            done = self.game.translate(3)
            while not done:
                done = self.game.translate(3)

        # Right translation
        elif key in b[data.TSR]:
            self.translate(1)
        elif key in b[data.THR]:
            done = self.game.translate(1)
            while not done:
                done = self.game.translate(1)

        # Game un-paused -> Pause game
        elif key in b[data.PAUSE] and self.un_paused:
            self.un_paused = False
            self.after_cancel(self.gravity_after_id)

        # Stockpile access
        else:
            for slot in range(self.game.shape_size):
                if key in b[data.STOCKPILE][slot]:
                    self.stockpile_access(slot)

        self.draw_shape()

    def game_over(self):
        self.un_paused = None

    def set_period(self, *args):
        """
        a trace method associated with
        the parent window's speed menu.
        """
        self.period = data.get_period(
            self.game.lines,
            self.speed_index_int_var.get()
        )

    def change_shape_set(self, *args):
        self.draw_shape(erase=True)
        self.game.change_shape_set(self.shape_set.get())

        self.next_shape.redraw_shape(self.game.next_shape.name)
        for slot in range(self.game.shape_size):
            self.stockpile[slot].redraw_shape(self.game.stockpile[slot])
        self.draw_shape()

    def set_color_scheme(self, *args):
        """
        a trace method associated with
        the parent window's color menu.
        """
        # update the color scheme field
        schemes = data.COLOR_SCHEMES[self.game.shape_size]
        self.cs = schemes[self.cs_string_var.get()]
        self.configure(bg=self.cs['bg'])

        # redraw the next shape canvas
        self.next_shape.set_color_scheme()
        self.next_shape.redraw_shape(self.game.next_shape.name)

        # redraw the main canvas
        self.canvas.master.configure(bg=self.cs['bg'])
        self.canvas.configure(bg=self.cs['grid-lines'])
        for y in range(self.game.dmn.y):
            for cell in self.game.grid[y]:
                self.canvas.itemconfigure(
                    cell.canvas_id, fill=self.cs[cell.key]
                )
        self.draw_shape()
        self.score_label.configure(bg=self.cs['bg'], fg=self.cs['text'])

        # redraw each slot in the stockpile
        self.stockpile[0].master.configure(bg=self.cs['bg'])
        for slot in range(self.game.shape_size):
            self.stockpile[slot].set_color_scheme()
            self.stockpile[slot].redraw_shape(self.game.stockpile[slot])


class TetrisApp(Tk):
    """
    Implements a window.
    Contains a number of GameFrame Frames
    """
    shape_size: int
    speed_index_int_var: IntVar
    shapes_string_var: StringVar
    cs_string_var: StringVar
    players: tuple

    def configure_menu(self):
        menu_bar = Menu(self)
        self.configure(menu=menu_bar)

        # controls command
        menu_bar.add_command(label='controls', command=self.popup_controls)

        # speed menu
        speed_menu = Menu(menu_bar)
        menu_bar.add_cascade(label='speed', menu=speed_menu)
        self.speed_index_int_var = IntVar()
        for speed_string, scalar in data.FREQ_SCALAR_KEYS.items():
            speed_menu.add_radiobutton(
                label=speed_string, value=scalar,
                variable=self.speed_index_int_var
            )
        speed_menu.invoke(speed_menu.index('1.00x'))

        # shapes menu
        shapes_menu = Menu(menu_bar)
        menu_bar.add_cascade(label='shapes', menu=shapes_menu)
        self.shapes_string_var = StringVar()
        self.shapes_string_var.set('default')
        for shape_set in data.SHAPES[self.shape_size].keys():
            shapes_menu.add_radiobutton(
                label=shape_set, value=shape_set,
                variable=self.shapes_string_var
            )
        shapes_menu.invoke(shapes_menu.index('default'))

        # color menu
        colors_menu = Menu(menu_bar)
        menu_bar.add_cascade(label='colors', menu=colors_menu)
        self.cs_string_var = StringVar()
        for scheme in data.COLOR_SCHEMES[self.shape_size].keys():
            colors_menu.add_radiobutton(
                label=scheme, value=scheme,
                variable=self.cs_string_var
            )
        colors_menu.invoke(colors_menu.index('default'))

    def __init__(self,
                 shape_size: int = data.DEFAULT_SHAPE_SIZE,
                 num_rows: int = None,
                 num_cols: int = None,
                 num_players: int = 1):
        super(TetrisApp, self).__init__()
        self.title('Tetris - david fong')
        # self.iconbitmap('error')  # TODO: make a tetromino bitmap
        self.focus_set()

        if shape_size not in data.SHAPES.keys():
            shape_size = data.DEFAULT_SHAPE_SIZE
        self.shape_size = shape_size

        # Perform some cleaning
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

        # Configure the menu
        self.configure_menu()

        # Create and pack GameFrame objects
        assert num_players > 0
        players = []
        for player_num in range(num_players):
            player = GameFrame(
                self, num_rows, num_cols,
                data.get_default_bindings(num_players, player_num)
            )
            player.grid(row=0, column=player_num, sticky='w')
            players.append(player)
        self.players = tuple(players)

    def popup_controls(self):
        """
        Pops up a window for each player displaying their controls.
        """
        for player_num in range(len(self.players)):
            player: GameFrame = self.players[player_num]
            title = 'controls - player #%d' % (player_num + 1)
            import pprint
            message = pprint.pformat(player.bindings)
            messagebox.showinfo(title, message, parent=self)
        return


def main():
    options = str(list(data.DEFAULT_BINDINGS.keys()))
    num_players = input('input a number of players in %s: ' % options)
    app = TetrisApp(num_players=int(num_players))
    app.mainloop()


main()
