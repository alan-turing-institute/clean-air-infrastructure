import tkinter

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
# Implement the default Matplotlib key bindings.
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure

import numpy as np


root = tkinter.Tk()
root.wm_title("Embedding in Tk")

top = tkinter.Frame(root)
top.place(relx=0.3)

left = tkinter.Frame(root)
left.place(relx=0.0)

page = tkinter.Frame(root)
page.pack(fill=tkinter.BOTH, expand=1)

fig = Figure(figsize=(20, 10),facecolor='#7f8c8d')
t = np.arange(0, 3, .01)
fig.add_subplot(111).plot(t, 2 * np.sin(2 * np.pi * t))
plt.tight_layout()

canvas = FigureCanvasTkAgg(fig, master=root)  # A tk.DrawingArea.
canvas.draw()
canvas.get_tk_widget().pack(in_=page)

#toolbar = NavigationToolbar2Tk(canvas, root)
#toolbar.update()
#canvas.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)


def on_key_press(event):
    print("you pressed {}".format(event.key))
    key_press_handler(event, canvas, toolbar)


canvas.mpl_connect("key_press_event", on_key_press)


def _quit():
    root.quit()     # stops mainloop
    root.destroy()  # this is necessary on Windows to prevent
                    # Fatal Python Error: PyEval_RestoreThread: NULL tstate



button = tkinter.Button(master=root, text="Quit", command=_quit)
button.pack(in_=left, side=tkinter.TOP)

button1 = tkinter.Button(master=root, text="Quit2", command=_quit)
button1.pack(in_=left, side=tkinter.TOP)

tkvar = tkinter.StringVar(root)
choices = { 'Pizza','Lasagne','Fries','Fish','Potatoe'}
tkvar.set('Pizza') # set the default option

popupMenu = tkinter.OptionMenu(root, tkvar, *choices)
popupMenu.config(width=10, height=2)

tkvar1 = tkinter.StringVar(root)
choices1 = { '1','2','3','3','4'}
tkvar1.set('1') # set the default option

popupMenu1 = tkinter.OptionMenu(root, tkvar1, *choices1)
popupMenu1.config(width=10, height=2)

popupMenu.pack(in_=top, side=tkinter.LEFT)
popupMenu1.pack(in_=top, side=tkinter.LEFT)

# on change dropdown value
def change_dropdown(*args):
    print( tkvar.get() )

# link function to change dropdown
tkvar.trace('w', change_dropdown)

tkinter.mainloop()
