import tkinter
from tkinter import Frame, Canvas, Menu, Event, colorchooser

from game import *


class GUI(Frame):
    """

    """

    game: Game          #
    cs: dict            # a map from color swatches to actual color values

    master: Frame       # top level frame
    menu: Menu
    canvas: Canvas
    virtual_kbd: Frame  # emulates buttons used for playing

    def __init__(self, master):
        """

        """

        super().__init__(master)
        self.master = master
        self.pack()

        self.game = Game()
        self.set_color_scheme()

        self.menu = Menu(master)
        master['menu'] = self.menu
        self.canvas = Canvas(self.master, bg=self.cs['bg']).pack(side='left')
        self.canvas['height'] = data.canvas_dimension(self.game.dimensions.y0())
        self.canvas['width'] = data.canvas_dimension(self.game.dimensions.x0())
        self.virtual_kbd = Frame(self.master, bg=self.cs['bg'])

    def draw_shape(self, event: Event, erase: bool = False):
        g = self.game
        s: Shape = g.curr_shape
        t: Tile
        for t in s.tiles:
            points = [0, 0, 0, 0]
            x = g.position.x0() + t.x[g.rotation]
            y = g.dimensions.y0() - (1 + g.position.x0() + t.y[g.rotation])
            points[0] = data.canvas_dimension(x)
            points[1] = data.canvas_dimension(y)
            points[2] = points[0] + data.GUI_CELL_WID
            points[3] = points[1] + data.GUI_CELL_WID
            self.canvas.create_rectangle(points, fill=self.cs[s.name])

    def set_color_scheme(self, cs_name: str = 'default'):
        self.cs = data.COLOR_SCHEMES[self.game.shape_size][cs_name]
