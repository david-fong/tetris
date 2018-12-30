import random
import tkinter
from math import floor
from tkinter import Frame, Canvas
import data


def say_hi():
        root.bell()


def func():
    say_hi()
    root.after(floor(1500.1), func)


def start(event):
    func()


tuple_test = (0, 1, 2, 3, 4, 5, 6)
for i in range(20):
    print('hi')
root = tkinter.Tk()
c = Canvas(root, height=200, width=200, bg='purple')
c.pack(expand=False, fill='both')
cell = c.create_rectangle(0, 0, 100, 100, fill='green')
c.itemconfigure(cell, fill='blue', width=0)
c['bg'] = 'orange'
root.bind('<Enter>', start)
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
