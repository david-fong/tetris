import tkinter
from tkinter import Frame, Canvas, Menu, Event, colorchooser

import data
from game import Tile, Game


class GUI(Frame):
    """

    """
    master: Frame       # top level frame
    game: Game          #
    cs: dict            # a map from color swatches to actual color values

    menu: Menu
    canvas: Canvas
    virtual_kbd: Frame  # emulates buttons used for playing

    def __init__(self, master):
        """

        """
        super().__init__(master)
        self.master = master
        self.pack()

        self.set_color_scheme()
        canvas = Canvas(self.master, bg=self.cs['bg'])
        game = Game(self)
        self.game = game

        self.menu = Menu(master)
        master['menu'] = self.menu

        self.canvas = canvas
        self.canvas.pack(side='left')
        self.canvas['height'] = data.canvas_dmn(game.dmn.y0())
        self.canvas['width'] = data.canvas_dmn(game.dmn.x0())
        for y in range(game.dmn.y0()):
            for x in range(game.dmn.x0()):
                bbox = [0, 0, 0, 0]
                bbox[0] = data.canvas_dmn(x)
                bbox[1] = data.canvas_dmn(game.dmn.y0() - 1 - y)
                bbox[2] = bbox[0] + data.GUI_CELL_WID
                bbox[3] = bbox[1] + data.GUI_CELL_WID
                item_id: int = self.canvas.create_rectangle(
                    bbox=bbox, activebackground=self.cs[' '],
                    tags='%d' % y, width=0
                )
                game.grid[y][x].set_id(item_id)

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
                    cell.id, fill=self.cs[g.curr_shape.name]
                )

    def game_over(self):
        # TODO:
        return

    def set_color_scheme(self, cs_name: str = 'default'):
        self.cs = data.COLOR_SCHEMES[self.game.shape_size][cs_name]


def main():
    """

    """
    root = tkinter.Tk()
    gui = GUI(root)
    gui.game.start()  # TODO: make this by user input in the gui class
    gui.mainloop()


main()
