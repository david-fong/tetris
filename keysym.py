from tkinter import Tk, StringVar, Label


def set_keysym(event):
    keysym.set(event.keysym)


root = Tk()
root.bind('<Key>', set_keysym)

keysym = StringVar()

label = Label(root)
label.configure(textvariable=keysym)
label.pack()

root.mainloop()
