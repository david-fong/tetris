import random
import tkinter
from math import floor
from tkinter import Frame, Canvas
import data


def say_hi():
    print('hello')
    root.bell()


def func():
    say_hi()
    root.after(floor(1500.1), func)


def start(event):
    print('char:    ' + event.char)
    print('keysym:  ' + event.keysym)
    print('state:   ' + str(event.state))
    print('keycode: ' + str(event.keycode) + '\n')
    # func()


print(int(1.49), int(1.5), int(1.8))
tuple_test = (0, 1, 2, 3, 4, 5, 6)
data.get_random_shape(4, [])
root = tkinter.Tk()
canvas = Canvas(root, height=200, width=200, bg='purple')
canvas.pack(expand=False, fill='both')
cell = canvas.create_rectangle(0, 0, 100, 100, fill='green')
canvas.itemconfigure(cell, fill='blue', width=0)
canvas['bg'] = 'orange'
canvas.itemconfigure('all', fill='black')
root.bind('<Key>', start)
label = tkinter.Label(root)
label.configure(text='SIERGEY! MY FRIEND!')
label.pack()
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
