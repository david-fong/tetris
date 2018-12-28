import random
import tkinter
from tkinter import Frame, Canvas, Menu, Event, colorchooser, Label

root = tkinter.Tk()
c = Canvas(root, height=200, width=200, bg='purple')
c.pack(expand=False, fill='both')
cell = c.create_rectangle(0, 0, 10, 10, fill='green')
c.itemconfigure(cell, fill='blue')
c['bg'] = 'orange'
root.mainloop()

list_test = []
list_test += [1]
list_test = tuple(list_test)
print(list_test)
list_test[0] = 2
# print(cell)
