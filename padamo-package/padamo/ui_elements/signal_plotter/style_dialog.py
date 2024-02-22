import tkinter as tk
from tkinter import ttk
from tkinter.simpledialog import Dialog
from matplotlib import colors as mcolors

LINESTYLES = ['-', '--', '-.', ':']
VALID_COLORS = list(mcolors.BASE_COLORS.keys())+list(mcolors.CSS4_COLORS.keys())

def validate_color(col:str):
    col = col.strip()
    if col.startswith("#"):
        if len(col) != 7:
            return False
        for c in col[1:]:
            if c not in "0123456789ABCDEF":
                return False
        return True
    else:
        return col in VALID_COLORS

def fine_line(axes, label):
    for line in axes.get_lines():
        if line.get_label() == label:
            return line

class StyleDialog(Dialog):
    def __init__(self,master, line_artist, axes):
        self.line_artist = line_artist
        self.axes = axes
        self._grid_index = 0
        self._colorvar = None
        self._stylevar = None
        super().__init__(master)

    def add_entry(self, parent, key, initial_var, values=None):
        tk.Label(parent,text=key).grid(row=self._grid_index,column=0, sticky="nsew")
        var = tk.StringVar(parent)
        var.set(initial_var)
        if values is None:
            tk.Entry(parent,textvariable=var).grid(row=self._grid_index,column=1, sticky="nsew")
        else:
            ttk.Combobox(parent, textvariable=var, values=values,
                         state="readonly").grid(row=self._grid_index, column=1, sticky="nsew")
        self._grid_index += 1
        return var

    def body(self, master: tk.Frame):
        self._colorvar = self.add_entry(master, "Color", self.line_artist.get_color())
        self._stylevar = self.add_entry(master, "Style", self.line_artist.get_linestyle(),
                                        LINESTYLES)

    def apply(self) -> None:
        line = fine_line(self.axes, self.line_artist.get_label())
        if line:
            if validate_color(self._colorvar.get()):
                line.set_color(self._colorvar.get())
            line.set_linestyle(self._stylevar.get())
