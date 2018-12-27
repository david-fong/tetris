import tkinter
from tkinter import Frame, Button, Event

from game import *


class GUI:
    """

    """

    game: Game              #
    cv: Condition           # used to be notified when ready to update display
    root: Frame             # top level frame
    grid: Frame             # holds buttons for display that represent Cell objects
    buttons: tuple          # stores buttons for code use
    cell_map: dict          # maps buttons to their corresponding cells
    virtual_kbd: Frame      # emulates buttons used for playing

    color_schemes: dict     # a dictionary of color schemes for this game's shape size
    current_cs: str         # a key to get color values for Frame and Shape objects

    def __init__(self):
        """

        """

        self.cv = Condition()
        self.game = Game(cv=self.cv)
        self.color_schemes = data.COLOR_SCHEMES[self.game.shape_size]
        self.current_cs: str = 'default'

        self.root = tkinter.Tk('Tetris')  # TODO: do I need to pack this?
        self.grid = Frame(self.root, bg=self.cs('bg')).pack(side='left')
        self.virtual_kbd = Frame(self.root, bg=self.cs('bg'))

        self.buttons = ()
        self.cell_map = {}
        for row in range(len(self.game.grid)):
            button_row = ()
            for col in range(len(self.game.grid[row])):
                b: Button = Button(
                    self.grid,
                    bg=self.cs(' '),
                    height=data.GUI_CELL_WID,
                    width=data.GUI_CELL_WID).grid(row=row, col=col)
                for kbd_event in data.KBD_EVENTS:
                    b.bind(kbd_event, self.update_grid, '+')
                button_row += b
                self.cell_map[b] = self.game.grid[row][col]
            self.buttons += button_row

        self.root.mainloop()

    def update_grid(self, event: Event):
        with self.cv:  # see game.Game.set_curr_shape
            self.cv.wait(data.GUI_WAIT_TIMEOUT)
            cell = self.cell_map[event.widget]
            event.widget['bg'] = self.cs(cell.key)

    def cs(self, key: str = ' '):
        """helper function to get value from color_scheme dict"""
        return self.color_schemes[self.current_cs][key]
