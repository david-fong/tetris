import tkinter
from tkinter import Frame, Canvas, Menu, Event, colorchooser

import data
from game import Game, Tile


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

        g = Game()
        self.game = g
        self.set_color_scheme()

        self.menu = Menu(master)
        master['menu'] = self.menu

        self.canvas = Canvas(self.master, bg=self.cs['bg'])
        self.canvas.pack(side='left')
        self.canvas['height'] = data.canvas_dmn(g.dmn.y0())
        self.canvas['width'] = data.canvas_dmn(g.dmn.x0())
        for y in range(g.dmn.y0()):
            for x in range(g.dmn.x0()):
                p_y = data.canvas_dmn(g.dmn.y0() - 1 - y)
                position = (data.canvas_dmn(x), p_y)
                item_id: int = self.canvas.create_bitmap(
                    position=position, activebackground=self.cs[' '],
                    bitmap=data.BITMAP_PATH
                )
                g.grid[y][x].set_id(item_id)

        self.virtual_kbd = Frame(self.master, bg=self.cs['bg'])
        self.virtual_kbd.pack(side='right')

    def draw_shape(self, event: Event, erase: bool = False):
        g = self.game
        t: Tile
        for t in g.curr_shape.tiles:
            x = g.pos.x0() + t.x[g.rot]
            y = g.pos.x0() + t.y[g.rot]
            cell = g.grid[y][x]
            if erase:
                cell.clear()
            self.canvas.itemconfigure(cell.id, fill=self.cs[cell.key])

    def set_color_scheme(self, cs_name: str = 'default'):
        self.cs = data.COLOR_SCHEMES[self.game.shape_size][cs_name]


def main():
    root = tkinter.Tk()
    gui = GUI(root)
    gui.mainloop()
