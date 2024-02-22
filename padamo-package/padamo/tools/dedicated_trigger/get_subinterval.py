import tkinter as tk
from tkinter.simpledialog import Dialog
from .storage import IntervalStorage, Interval
from padamo.editing.widgets import IntegerEntry, parse_int


class IntervalAsker(Dialog):
    def __init__(self, master, storage:IntervalStorage):
        self.result = None
        self.src_storage = storage.get_available()
        self.listbox = None
        self.startvar = None
        self.endvar = None
        super().__init__(master)

    def body(self, master: tk.Frame):
        panel = tk.Frame(self)
        panel.pack(side="top",fill="x")
        self.startvar = tk.StringVar()
        self.endvar = tk.StringVar()
        IntegerEntry(panel,textvariable=self.startvar).pack(side="left",fill="both",expand=True)
        IntegerEntry(panel,textvariable=self.endvar).pack(side="right",fill="both",expand=True)

        self.listbox = tk.Listbox(master)
        for interval in self.src_storage:
            self.listbox.insert(tk.END,str(interval))
        self.listbox.pack(fill="both",expand=True)
        self.listbox.bind('<<ListboxSelect>>', self.on_select)
        self.listbox.bind("<Double-Button-1>", self.ok)

    def on_select(self,ev):
        sel = self.listbox.curselection()
        if sel:
            index = sel[0]
            interval = self.src_storage[index]
            self.startvar.set(str(interval.start))
            self.endvar.set(str(interval.end))

    def apply(self):
        start = parse_int(self.startvar.get())
        end = parse_int(self.endvar.get())
        if start>=end:
            return
        self.result = Interval(start,end)