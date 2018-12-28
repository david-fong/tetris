import random
import tkinter
from tkinter import Frame, Canvas
import data

root = tkinter.Tk()
c = Canvas(root, height=200, width=200, bg='purple')
c.pack(expand=False, fill='both')
cell = c.create_rectangle(0, 0, 100, 100, fill='green')
c.itemconfigure(cell, fill='blue', width=0)
c['bg'] = 'orange'
root.mainloop()

list_test = []
list_test += [1]
list_test = tuple(list_test)
print(list_test)
dict_test = {'default': 0}
print(None)
try:
    print(dict_test['nonexistent_key'])
except KeyError:
    print(dict_test['default'])
print(dir(data))
# print(cell)
