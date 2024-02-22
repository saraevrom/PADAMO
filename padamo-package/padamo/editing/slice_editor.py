import tkinter as tk
from tkinter import ttk
from .widgets import IntegerEntry

def parse_res(s):
    if s:
        return int(s)
    return None


class AlternatingView(tk.Frame):
    def __init__(self, master, keys, subitems_constructors):
        super().__init__(master)
        self.subitems = []
        self.selector = ttk.Combobox(self, state="readonly")
        self.selector.pack(side="top", fill="x")
        for item_c in subitems_constructors:
            frame = tk.Frame(self)
            frame.pack(side="top", fill="x")
            subitem = item_c(frame)
            subitem.pack(fill="both",expand=True)
            self.subitems.append(subitem)
        self.selector.bind('<<ComboboxSelected>>', self.on_select)

    def on_select(self, event):
        self.selector.get()

    def hide_all(self):
        for item in self.subitems:
            item.pack_forget()

    def show_item(self, index):
        self.hide_all()
        self.subitems[index].pack(fill="both",expand=True)




class FullSliceEditor(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.startvar = tk.StringVar()
        self.endvar = tk.StringVar()
        self.stepvar = tk.StringVar()
        start = IntegerEntry(self, textvariable=self.startvar)
        start.grid(row=0, column=0, sticky="nsew")
        end = IntegerEntry(self, textvariable=self.endvar)
        end.grid(row=0, column=1, sticky="nsew")
        step = IntegerEntry(self,textvariable=self.stepvar)
        step.grid(row=0, column=2, sticky="nsew")

    def get_slice(self):
        s1 = parse_res(self.startvar.get())
        s2 = parse_res(self.endvar.get())
        s3 = parse_res(self.stepvar.get())
        return slice(s1,s2,s3)

