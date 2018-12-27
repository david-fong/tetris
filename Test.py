import random
import tkinter
from tkinter import Frame, Canvas, Menu, Event, colorchooser

root = tkinter.Tk()
c = Canvas(root, height=20, width=20, bg='purple')
c.pack(expand=False, fill='both')
cell = c.create_rectangle(0, 0, 10, 10, fill='green')
c['bg'] = 'orange'
root.mainloop()
