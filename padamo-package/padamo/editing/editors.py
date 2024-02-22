import tkinter as tk
from tkinter import ttk
from .widgets import FloatEntry, IntegerEntry, parse_float, parse_int
from tkinter.filedialog import askopenfilename
from .filenames import Filename
from padamo.canvas_drawing.port_types import STRING, INTEGER, FLOAT, BOOLEAN

class Password(str):
    pass

class Default(object):
    pass

class Editor(tk.Frame):
    ASSOCIATED_LINK_TYPE = None

    def __init__(self, master, name, controller, starttype, allow_external=False, is_optional=False):
        super().__init__(master, highlightbackground="black", highlightthickness=1)
        self.name = name
        #self.body = tk.Frame(self)
        #self.pack(side="right", fill="both", expand=True)
        self.controller = controller
        self.starttype = starttype
        self.use_external_var = tk.IntVar(self)
        self.use_external_var.set(0)
        self.option_var = tk.IntVar(self)
        self.option_var.set(1)
        label = tk.Label(self, text=self.name)
        label.grid(row=0,column=0, sticky="nw")
        row = 1
        if allow_external:
            check = tk.Checkbutton(self, variable=self.use_external_var, text="External", anchor="nw")
            check.grid(row=1,column=0, sticky="nw")
            row += 1
            self.use_external_var.trace("w",self.on_external_update)
        if is_optional:
            check1 = tk.Checkbutton(self, variable=self.option_var, text="Enabled", anchor="nw")
            check1.grid(row=row, column=0, sticky="nw")
            row += 1
            self.option_var.trace("w",self.on_external_update)
        self.mainframe = tk.Frame(self)
        self._mainframe_grid = row
        self.mainframe.grid(row=row, column=0, sticky="nw",padx=20)
        self.rowconfigure(row, weight=1)
        self.build(self.mainframe)

    def on_external_update(self,*args):
        if self.use_external_var.get() or not self.option_var.get():
            self.mainframe.grid_forget()
        else:
            self.mainframe.grid(row=self._mainframe_grid, column=0, sticky="nw", padx=20)
        self.on_commit()

    def build(self, body):
        raise NotImplementedError

    def set_value(self, v):
        raise NotImplementedError

    def get_value(self):
        raise NotImplementedError

    def get_value_checked(self):
        if self.option_var.get():
            return self.get_value()
        else:
            print("NONE HERE", self.option_var.get(),type(self),self)
            return None

    def set_value_checked(self, val):
        if val is None:
            self.option_var.set(0)
        else:
            self.option_var.set(1)
            self.set_value(val)

    def get_editor_state(self):
        return [self.get_value_checked(), self.use_external_var.get()]

    def set_editor_state(self,state):
        self.set_value_checked(state[0])
        self.use_external_var.set(state[1])

    def on_commit(self,*args):
        self.controller.update_values()


class BooleanEditor(Editor):
    ASSOCIATED_LINK_TYPE = BOOLEAN

    def build(self, body):
        self.check_var = tk.IntVar(self)
        self.check_var.trace("w", self.on_commit)
        checkbox = tk.Checkbutton(body, variable=self.check_var, text="Value set", anchor="nw")
        checkbox.pack(fill="both", expand=True)

    def set_value(self, v):
        self.check_var.set(int(v))

    def get_value(self):
        return bool(self.check_var.get())


class StringEditor(Editor):
    ASSOCIATED_LINK_TYPE = STRING

    def build(self, body):
        self.var = tk.StringVar(self)
        self.var.trace("w", self.on_commit)
        entry = tk.Entry(body, textvariable=self.var)
        entry.pack(fill="both", expand=True)

    def set_value(self, v):
        self.var.set(v)

    def get_value(self):
        return self.var.get()


# class PasswordEditor(Editor):
#     ASSOCIATED_LINK_TYPE = STRING
#     def build(self, body):
#         print("PASS")
#         self.var = tk.StringVar(self)
#         self.var.trace("w", self.on_commit)
#         label = tk.Label(body, text=self.name)
#         label.pack(side="left")
#         entry = tk.Entry(body, textvariable=self.var, show="*")
#         entry.pack(fill="both", expand=True)
#
#     def set_value(self, v):
#         self.var.set(v)
#
#     def get_value(self):
#         return self.var.get()

class FilenameEditor(Editor):
    ASSOCIATED_LINK_TYPE = STRING

    def build(self, body):
        self.var = tk.StringVar(self)
        self.var.trace("w", self.on_commit)
        entry = tk.Entry(body, textvariable=self.var)
        entry.pack(fill="both", expand=True)
        pickbtn = tk.Button(body,text="Pick file", command=self.on_pick)
        pickbtn.pack(side="bottom", fill="x")

    def on_pick(self):
        filename = askopenfilename(defaultextension=self.starttype.DEFAULT_EXTENSION,
                                   filetypes=self.starttype.FILETYPES)
        if filename:
            self.var.set(filename)

    def set_value(self, v):
        self.var.set(v)

    def get_value(self):
        return self.var.get()


class IntEditor(Editor):
    ASSOCIATED_LINK_TYPE = INTEGER

    def build(self, body):
        self.var = tk.StringVar(self)
        self.var.trace("w", self.on_commit)
        entry = IntegerEntry(body, textvariable=self.var)
        entry.pack(fill="both", expand=True)

    def set_value(self, v):
        self.var.set(str(v))

    def get_value(self):
        return parse_int(self.var.get())


class FloatEditor(Editor):
    ASSOCIATED_LINK_TYPE = FLOAT

    def build(self, body):
        self.var = tk.StringVar(self)
        self.var.trace("w", self.on_commit)
        entry = FloatEntry(body, textvariable=self.var)
        entry.pack(fill="both", expand=True)

    def set_value(self, v):
        self.var.set(str(v))

    def get_value(self):
        return parse_float(self.var.get())


class SelectableOptions(object):
    OPTIONS = []
    DEFAULT_ID = 0
    options_persistent = None

    @classmethod
    def get_options(cls):
        return cls.OPTIONS

    @classmethod
    def get_default(cls):
        return cls.get_options()[cls.DEFAULT_ID]

    @classmethod
    def options(cls):
        if cls.options_persistent is None:
            cls.options_persistent = cls.get_options()
        return cls.options_persistent

    @classmethod
    def check(cls,option):
        if option in cls.options():
            return option
        else:
            raise ValueError(f"Value {option} is not in list {cls.options()}")


class OptionEditor(Editor):
    ASSOCIATED_LINK_TYPE = STRING

    def build(self, body):
        opts = self.starttype.options()
        self.combo = ttk.Combobox(body,values=opts)
        self._opts = opts
        if not opts:
            opts.append("----")
        #self.combo["values"] = opts
        self.combo.set(opts[0])
        self.combo["state"] = "readonly"
        self.combo.bind("<<ComboboxSelected>>", self.on_combo_select)

        self.combo.pack(fill="both", expand=True)
        self.on_commit()

    def on_combo_select(self,*args):
        print("TRIGGER")
        self.on_commit()

    def get_value(self):
        v = self.starttype.check(self.combo.get())
        if v is Default:
            self.set_value(self._opts[self.starttype.DEFAULT_ID])
            v = self.starttype.check(self.combo.get())
        #print("GET",v)
        return v

    def set_value(self, v):
        #print("SET", v)
        if v is Default:
            self.combo.set(self._opts[self.starttype.DEFAULT_ID])
        else:
            self.combo.set(v)



EDITOR_MAP = {
    float: FloatEditor,
    int: IntEditor,
    bool: BooleanEditor,
    str: StringEditor,
    Filename: FilenameEditor,
    SelectableOptions: OptionEditor
    #Password:PasswordEditor
}


def pick_editor(t_):
    if t_ in [float,int,bool,str,Password]:
        return EDITOR_MAP[t_]
    for k in EDITOR_MAP.keys():
        if issubclass(t_,k):
            return EDITOR_MAP[k]
    raise KeyError("No editor found for", t_)