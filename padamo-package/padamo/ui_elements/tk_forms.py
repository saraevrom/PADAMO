#!/usr/bin/env python3
#-*-coding:utf8-*-

import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import os.path
from .modified_base import EntryWithEnterKey


def get_kwarg(kwdict,key,defval):
    if key in kwdict.keys():
        return kwdict[key]
    else:
        return defval

def get_kw_bool(kwdict,key,defval=False):
    return get_kwarg(kwdict,key,defval)


'''
Creates tkinter input forms based on configuration
'''


class ScrollView(ttk.Frame):
    '''
    Class for scrollable frame view
    Obtained from tutorial at https://blog.teclado.com/tkinter-scrollable-frames/
    '''
    def __init__(self,parent,*args,**kwargs):
        super().__init__(parent,*args,**kwargs)
        self.canvas = tk.Canvas(self)
        self.v_scrollbar = tk.Scrollbar(self,orient="vertical",command = self.canvas.yview)
        self.h_scrollbar = tk.Scrollbar(self,orient="horizontal",command = self.canvas.xview)

        self.contents = tk.Frame(self.canvas)
        self.contents.bind("<Configure>", self.on_content_change)
        self.drawn_window_id = self.canvas.create_window((0,0), window=self.contents,anchor="nw")
        self.canvas.configure(yscrollcommand=self.v_scrollbar.set,xscrollcommand=self.h_scrollbar.set)
        # self.h_scrollbar.pack(side="bottom", fill="x")
        # self.v_scrollbar.pack(side="right", fill="y")
        # self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.h_scrollbar.grid(row=1, column=0, sticky="nsew", columnspan=2)
        self.v_scrollbar.grid(row=0, column=1, sticky="nsew")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.canvas.bind("<Configure>", self.on_canvas_change)

    def on_content_change(self,event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_canvas_change(self, event):
        width = self.canvas.winfo_width()
        if width>400:
            self.canvas.itemconfig(self.drawn_window_id, width=width)
        else:
            self.canvas.itemconfig(self.drawn_window_id, width=400)


class Validatable(object):
    def __init__(self, v_class):
        self.v_class = v_class
        self.old_value = 0

    def validate_value(self, var):
        new_value = var.get()
        try:
            if new_value == "-" or (new_value == "." and self.v_class == float):
                new_value = "0"
            new_value == '' or self.v_class(new_value)
            self.old_value = new_value
        except:
            var.set(self.old_value)

    def connect_validator(self, entryvar):
        entryvar.trace('w', lambda nm, idx, mode, var=entryvar: self.validate_value(var))



def index_to_color(color_index):
    if color_index % 2 == 0:
        color = "#AAAAAA"
    else:
        color = "#CCCCCC"
    return color

def index_to_style(color_index):
    color = index_to_color(color_index)
    return dict(highlightbackground="gray", background=color, highlightthickness=1,bd=5)

def index_to_style_nobd(color_index):
    color = index_to_color(color_index)
    return dict(highlightbackground="gray", background=color, highlightthickness=1)


LOCK_POSITIONS = {
    "r": (
        dict(side="right", fill="y"),
        dict(side="left", fill="both", expand=True)
    ),
    "t": (
        dict(side="top", fill="x"),
        dict(side="bottom", fill="both", expand=True)
    )
}

class ConfigEntry(object):
    '''
    Base class for form fields.
    Field can accept configuration dictionary, mentioned as "conf".
    Some keys are common:
    display_name -- field prompt that appears on screen
    default -- default value, optional

    type -- field type, not required by fields themselves. Instead TkDictForm class uses it to determine field type. it will be mentioned in fields.

    Some keys are unique to fields. See help(<Field type>Entry)
    '''
    def __init__(self,name,master,conf:dict,color_index=0, protection=False, lock_pos="r"):
        self.conf = conf
        self.name = name
        self._protection_enabled = protection
        self.color_index = color_index
        style = index_to_style(color_index)
        style1 = index_to_style_nobd(color_index)

        self.frame = tk.Frame(master, **style)
        self._protection_var = tk.IntVar(self.frame)
        lock_kwargs, main_kwargs = LOCK_POSITIONS[lock_pos]
        if protection:
            pframe = tk.Frame(self.frame, **style1)
            pframe.pack(**lock_kwargs)
            lock = tk.Checkbutton(pframe, text="LOCK", variable=self._protection_var, anchor="w")
            lock.pack(fill="both", expand=True)
            locked = conf.get("lock", False)
            self._protection_var.set(int(locked))
        self.content_frame = tk.Frame(self.frame, **style1)
        self.content_frame.pack(**main_kwargs)
        self.controller_obj = None

    def get_value(self):
        return self._get_value()

    def _get_value(self):
        raise NotImplementedError("This method is not implemented")

    def set_value(self, newval, force=False):
        if force or not (self._protection_enabled and self._protection_var.get()):
            self._set_value(newval, force)

    def _set_value(self,newval, force=False):
        raise NotImplementedError("This method is not implemented")

    def keep_none(self):
        return True

    def trigger_change(self):
        if self.controller_obj:
            self.controller_obj.trigger_change()

    def on_trace(self, *args):
        self.trigger_change()


class EntryInvalidException(Exception):
    '''
    Can occur when processing field result.
    '''
    def __init__(self,fieldname,reason):
        message = "Invalid value encountered at {}, reason: {}".format(fieldname,reason)
        super().__init__(message)
        self.fieldname = fieldname
        self.reason = reason

class StringEntry(ConfigEntry):
    '''
    Enter a string

    type: "str"
    No unique keys
    '''
    def __init__(self,name,master,conf,color_index=0, protection=False):
        super().__init__(name,master,conf,color_index)
        tk.Label(self.content_frame,text=conf["display_name"]).pack(side="left",fill="both")
        self.textvar = tk.StringVar(master)
        e = EntryWithEnterKey(self.frame,textvar=self.textvar)
        e.on_commit = self.trigger_change
        e.pack(side="left",fill="both")

    def _set_value(self, newval, force=False):
        self.textvar.set(newval)

    def _get_value(self):
        return self.textvar.get()

    def get_frame(self):
        return self.frame

class LabelEntry(ConfigEntry):
    '''
    Just a label for information

    type: "label"
    fancy: makes label big and noticeable
    '''
    def __init__(self,name,master,conf,color_index=0, protection=False):
        super().__init__(name, master, conf, color_index, protection)
        if conf["fancy"]:
            label = tk.Label(self.content_frame, text=conf["display_name"], anchor="center", font='TkDefaultFont 10 bold')
        else:
            label = tk.Label(self.content_frame, text=conf["display_name"], anchor="center")
        label.pack(side="left", fill="both", expand=True)

    def _set_value(self, newval, force=False):
        pass

    def _get_value(self):
        return None

    def keep_none(self):
        return False

    def get_frame(self):
        return self.frame

class IntEntry(ConfigEntry, Validatable):
    '''
    Enter an integer

    type: "int"
    No unique keys
    '''
    def __init__(self,name,master,conf,color_index=0, protection=False):
        ConfigEntry.__init__(self, name, master, conf, color_index, protection)
        Validatable.__init__(self, int)
        tk.Label(self.content_frame,text=conf["display_name"]).pack(side="left",fill="both")
        self.textvar = tk.StringVar(self.content_frame)
        self.connect_validator(self.textvar)
        integer_entry = EntryWithEnterKey(self.content_frame, textvar=self.textvar)
        integer_entry.pack(side="left",fill="both")
        integer_entry.on_commit = self.trigger_change

    def _set_value(self, newval, force=False):
        self.textvar.set(str(newval))
        self.old_value = newval

    def _get_value(self):
        sval = self.textvar.get()
        try:
            if sval:
                val = int(sval)
            else:
                val = 0
            return val
        except ValueError:
            raise EntryInvalidException(self.name,"Could not convert \"{}\" to integer".format(sval))

class FloatEntry(ConfigEntry, Validatable):
    '''
    Enter a float

    type: "float"
    No unique keys
    '''
    def __init__(self,name,master,conf,color_index=0, protection=False):
        ConfigEntry.__init__(self,name,master,conf,color_index, protection)
        Validatable.__init__(self, float)
        tk.Label(self.content_frame,text=conf["display_name"]).pack(side="left",fill="both")
        self.textvar = tk.StringVar(master)
        float_entry = EntryWithEnterKey(self.content_frame,textvar=self.textvar)
        float_entry.pack(side="left", fill="both")
        float_entry.on_commit = self.trigger_change
        self.connect_validator(self.textvar)


    def _set_value(self, newval, force=False):
        self.textvar.set(str(newval))

    def _get_value(self):
        sval = self.textvar.get()
        try:
            if sval == ".":
                val = 0.0
            elif sval:
                val = float(sval)
            else:
                val = 0.0
            return val
        except ValueError:
            raise EntryInvalidException(self.name,"Could not convert \"{}\" to float".format(sval))

class CheckmarkEntry(ConfigEntry):
    '''
    Enter a string

    type: "bool"
    No unique keys
    '''
    def __init__(self,name,master,conf,color_index=0, protection=False):
        super().__init__(name,master,conf,color_index, protection)
        self.intvar = tk.IntVar(master)
        tk.Checkbutton(self.content_frame,text=conf["display_name"],variable=self.intvar).pack(anchor="nw")
        self.intvar.trace("w", self.on_trace)



    def _set_value(self, newval, force=False):
        self.intvar.set(int(newval))

    def _get_value(self):
        return bool(self.intvar.get())

class FileEntry(ConfigEntry):
    '''
    Enter a filename. It has "Save file as" behaviour.

    type: "file"
    initialdir -- initial director for file dialog
    filetypes -- File types for dialog
    ask_mode -- Valid values are "open","saveas","directory". Mode for loading path. default is saveas
    '''
    def __init__(self,name,master,conf,color_index=0, protection=False):
        super().__init__(name,master,conf,color_index, protection)
        self.stringvar = tk.StringVar(master)
        tk.Label(self.content_frame, text=conf["display_name"]).pack(side="left")
        tk.Button(self.content_frame, text="Choose file", command=self.command).pack(side="left")
        tk.Label(self.content_frame, textvariable=self.stringvar).pack(side="left",fill="x")
        self.ask_mode = "saveas"
        if "ask_mode" in conf.keys():
            self.ask_mode = conf["ask_mode"]


    def command(self):
        if self.ask_mode == "open":
            asker = filedialog.askopenfilename
        elif self.ask_mode == "saveas":
            asker = filedialog.asksaveasfilename
        elif self.ask_mode == "directory":
            asker = filedialog.askdirectory
        else:
            raise ValueError("ask_mode is set to invalid option " + self.ask_mode)

        pth = asker(initialdir=self.conf["initialdir"], filetypes=self.conf["filetypes"])
        if pth:
            self.set_value(pth)
            self.trigger_change()
        top = self.frame.winfo_toplevel()
        #top.grab_set()
        top.lift()

    def _set_value(self, newval, force=False):
        if newval:
            self.stringvar.set(os.path.relpath(newval,self.conf["initialdir"]))
        else:
            self.stringvar.set("")
        self.realvalue = newval

    def _get_value(self):
        return self.realvalue

class RadioEntry(ConfigEntry):
    '''
    Choose a string via radio buttons.

    type: "radio"
    values -- selection options.
    '''
    def __init__(self,name,master,conf,color_index=0, protection=False):
        super().__init__(name,master,conf,color_index, protection)
        tk.Label(self.content_frame,text=conf["display_name"]).grid(row=0,column=0)
        self.intvar = tk.IntVar(master)
        self.intvar.set(0)
        self.intvar.trace("w", self.on_trace)
        ind = 0
        for val in self.conf["values"]:
            tk.Radiobutton(self.content_frame,text=val,value=ind,variable=self.intvar).grid(row=ind+1,column=1)
            ind+=1

    def _set_value(self, newval, force=False):
        self.intvar.set(self.conf["values"].index(newval))

    def _get_value(self):
        return self.conf["values"][self.intvar.get()]

class ComboEntry(ConfigEntry):
    '''
    Choose a string via combobox.

    type: "combo"
    values -- selection options.
    readonly -- is it possible to edit text inside box?
    '''
    def __init__(self,name,master,conf,color_index=0, protection=False):
        super().__init__(name,master,conf,color_index, protection)
        tk.Label(self.content_frame, text=conf["display_name"]).pack(side="left")
        ro = get_kw_bool(conf, "readonly")
        if ro:
            self.combobox = ttk.Combobox(self.content_frame, values=conf["values"], state="readonly")
        else:
            self.combobox = ttk.Combobox(self.content_frame, values=conf["values"])
        self.combobox.pack(side="left")
        self.combobox.bind("<Return>", self.on_trace)
        self.combobox.bind("<<ComboboxSelected>>", self.on_trace)

    def _set_value(self, newval, force=False):
        self.combobox.set(newval)

    def _get_value(self):
        return self.combobox.get()

FIELDTYPES = {
    "str":[StringEntry,False],
    "int":[IntEntry,False],
    "float":[FloatEntry,False],
    "bool":[CheckmarkEntry,False],
    "radio":[RadioEntry,False],
    "file":[FileEntry,False],
    "combo":[ComboEntry,False],
    "label": [LabelEntry,False]
}


def create_field(name,parent,conf, color_index=0,fill_entire=False, controller=None, protection=False):
    field_type, req_default = FIELDTYPES[conf["type"]]
    field = field_type(name,parent,conf, color_index, protection)
    field.controller_obj = controller
    if fill_entire:
        field.frame.pack(side="top", fill="both", expand=True)
    else:
        field.frame.pack(side="top", fill="x", expand=True)
    if "default" in conf.keys() or req_default:
        field.set_value(conf["default"], force=True)
    return field

class ArrayEntry(ConfigEntry):
    '''
    Creates array of certain field. To add and remove elements use +/- buttons.


    type: "array"
    subconf -- config for containing field. Index is appended to display_name.
    '''
    def __init__(self,name,master,conf,color_index=0, protection=False):
        super().__init__(name,master,conf,color_index, protection, lock_pos="t")
        tk.Label(self.content_frame,text=conf["display_name"]).pack(side="top", anchor="nw")
        self.subframe = tk.Frame(self.content_frame)
        self.subframe.pack(side="top",fill="both")
        self.subfields = []
        bottomframe = tk.Frame(self.content_frame)
        tk.Button(bottomframe,text="-",command=self.delfield).pack(side="right")
        tk.Button(bottomframe,text="+",command=self.addfield).pack(side="left")
        bottomframe.pack(side="bottom",fill="x")

    def addfield(self,value_to_set=None):
        subconf = self.conf["subconf"].copy()
        i = len(self.subfields)
        if "display_name" in subconf.keys():
            subconf["display_name"] = subconf["display_name"] + " " + str(i)
        else:
            subconf["display_name"] = str(i)
        name = "{}[{}]".format(self.name, i)

        def up_press():
            self.move_up(i)
        def down_press():
            self.move_down(i)

        def del_press():
            self._delete_at(i)

        def ins_press():
            self._insert_after(i)

        field = create_field(name, self.subframe, subconf, self.color_index+1, controller=self,
                             protection=self._protection_enabled)
        upbtn = tk.Button(field.frame,text="^", command=up_press)
        upbtn.pack(side="right", anchor="ne")
        downbtn = tk.Button(field.frame, text="v", command=down_press)
        downbtn.pack(side="right", anchor="ne")
        downbtn = tk.Button(field.frame, text="-", command=del_press)
        downbtn.pack(side="right", anchor="ne")
        downbtn = tk.Button(field.frame, text="+v", command=ins_press)
        downbtn.pack(side="right", anchor="ne")

        if value_to_set is not None:
            field.set_value(value_to_set)
        self.subfields.append(field)
        self.trigger_change()


    def _swap_indices(self, i1, i2):
        field_tmp = self.subfields[i1].get_value()
        self.subfields[i1].set_value(self.subfields[i2].get_value())
        self.subfields[i2].set_value(field_tmp)

    def _delete_at(self, index):
        for i in range(index, len(self.subfields)-1):
            self.subfields[i].set_value(self.subfields[i+1].get_value())
        self.delfield()

    def _insert_after(self, index):
        self.addfield()
        N = len(self.subfields)
        defval = self.subfields[N-1].get_value()
        for i in reversed(range(index+2, N)):
            self.subfields[i].set_value(self.subfields[i - 1].get_value())
        self.subfields[index+1].set_value(defval)

    def move_up(self, index):
        if index != 0:
            self._swap_indices(index, index-1)
        self.trigger_change()

    def move_down(self, index):
        if index < len(self.subfields)-1:
            self._swap_indices(index, index+1)
        self.trigger_change()

    def delfield(self):
        if self.subfields:
            last = self.subfields.pop(-1)
            last.frame.destroy()
        self.trigger_change()

    def _set_value(self, newval, force=False):
        self.subfields.clear()
        for widget in self.subframe.winfo_children():
            widget.destroy()
        for e in newval:
            self.addfield(e)


    def _get_value(self):
        r = []
        for sf in self.subfields:
            r.append(sf.get_value())
        return r

FIELDTYPES["array"] = [ArrayEntry,False]


class OptionEntry(ConfigEntry):
    '''
    Field that can be turned off

    type: "option"
    subconf -- controlled widget
    '''

    def __init__(self,name,master,conf,color_index=0, protection=False):
        super().__init__(name,master,conf,color_index, protection, lock_pos="t")
        self.use_var = tk.IntVar(master)
        tk.Checkbutton(self.content_frame, text=conf["display_name"], variable=self.use_var).pack(anchor="nw")
        self.subconf = conf["subconf"]

        name = self.name+".option"
        self.subfield = create_field(name, self.content_frame, self.subconf, self.color_index + 1, controller=self,
                                     protection=self._protection_enabled)
        self.subfield.frame.pack_forget()
        self.use_var.trace("w",self.update_visibility)


    def update_visibility(self,*args, **kwargs):
        if self.use_var.get():
            self.subfield.frame.pack(side="bottom", fill="both")
        else:
            self.subfield.frame.pack_forget()
        self.trigger_change()


    def _set_value(self, newval, force=False):
        if newval is None:
            self.use_var.set(0)
            self.update_visibility()
        else:
            self.use_var.set(1)
            self.update_visibility()
            self.subfield.set_value(newval, force=force)

    def _get_value(self):
        if self.use_var.get() != 0:
            return self.subfield.get_value()
        else:
            return None

FIELDTYPES["option"] = [OptionEntry, False]

class AlternatingEntry(ConfigEntry):
    '''
    Alternating field based on selection.

    type: "alter"
    values -- selection options. Array of dicts
        values[i]["name"] -- Branch name
        values[i]["subconf"] -- Entry config

    Return value is dict with structure:
        r["selection_type"] -- selected branch name
        r["value"] -- contents of branch
    '''
    def __init__(self,name,master,conf,color_index=0, protection=False):
        super().__init__(name,master,conf,color_index, protection, lock_pos="t")
        self.remembered_selections = dict()
        topframe = tk.Frame(self.content_frame)
        topframe.pack(side="top",fill="x")

        self.subframe = tk.Frame(self.content_frame)
        self.subframe.pack(side="bottom",fill="both",expand=True)

        tk.Label(topframe,text=conf["display_name"]).pack(side="left")

        self.visibility_toggle_var = tk.IntVar(self.content_frame)
        self.visibility_toggle_var.set(1)
        self.visibility_toggle_var.trace("w", self.update_visibility)
        visibility_toggle = tk.Checkbutton(topframe, variable=self.visibility_toggle_var)
        visibility_toggle.pack(side="right")

        self.valnames = [item["name"] for item in conf["values"]]
        self.subconfs = [item["subconf"] for item in conf["values"]]
        self.subfield = None

        self.sv = tk.StringVar(self.content_frame)
        self.sv.trace('w',self.on_combo_change)

        self.combobox = ttk.Combobox(topframe, textvar=self.sv, values=self.valnames, state="readonly")
        self.combobox.pack(side="left",fill="x",expand=False)
        #for sc in subconfs:
        #    self.addfield(sc)
        self.last_index=None


    def on_combo_change(self,*args,**kwargs):
        sel = self.sv.get()
        self.select_field(self.valnames.index(sel))
        stype = self.sv.get()
        if (stype in self.remembered_selections.keys()) and (self.subfield is not None):
            vset = self.remembered_selections[stype]
            if vset is not None:
                # print("Restoring", vset, "for", stype)
                self.subfield.set_value(vset)
        self.trigger_change()

    def select_field(self, index):
        if self.last_index == index:
            return False
        old_selection = self.get_value()
        index_to_remember = self.last_index
        if self.last_index is None:
            index_to_remember = index
        self.remembered_selections[self.valnames[index_to_remember]] = old_selection["value"]
        if self.subfield:
            self.subfield.frame.destroy()
            self.subfield = None
        subconf =self.subconfs[index]
        name = "{}[{}]".format(self.name, index)

        if subconf is None:
            field = None
        else:
            field = create_field(name, self.subframe, subconf, self.color_index+1, controller=self,
                                 protection=self._protection_enabled)

        self.subfield=field
        self.last_index=index
        self.update_visibility()
        return True

    def update_visibility(self,*_):
        if self.visibility_toggle_var.get():
            self.subframe.pack(side="bottom",fill="both",expand=True)
        else:
            self.subframe.pack_forget()

    def _set_value(self, newval, force=False):
        sel = newval["selection_type"]
        self.combobox.set(sel)
        self.select_field(self.valnames.index(sel))
        if "value" in newval.keys() and (self.subfield is not None):
            self.subfield.set_value(newval["value"], force=force)

    def _get_value(self):
        stype = self.combobox.get()
        if self.subfield:
            return {"selection_type": stype, "value": self.subfield.get_value()}
        else:
            return {"selection_type": stype, "value": None}

FIELDTYPES["alter"] = [AlternatingEntry,True]

class SubFormEntry(ConfigEntry):
    '''
    Creates small form inside.


    type: "subform"
    subconf -- config for internal form.
    use_scrollview -- should form use scrollable canvas?
    '''
    def __init__(self,name,master,conf,color_index=0, protection=False):
        super().__init__(name,master,conf,color_index, protection, lock_pos="t")
        lab = tk.Label(self.content_frame,text=conf["display_name"], anchor='w')
        lab.pack(side="top",fill="x",expand=True)
        self.subconf = conf["subconf"]
        use_scrollview = False
        if "use_scrollview" in conf.keys():
            use_scrollview = conf["use_scrollview"]
        self.subform = TkDictForm(self.content_frame, self.subconf, use_scrollview, color_index=color_index+1,
                                  protection=protection)
        self.subform.pack(side="bottom",fill="x",expand=True, padx=5)
        self.subform.on_commit = self.trigger_change

    def _set_value(self, newval, force=False):
        self.subform.set_values(newval, force=force)

    def _get_value(self):
        return self.subform.get_values()

FIELDTYPES["subform"] = [SubFormEntry,False]

class TkDictForm(tk.Frame):
    '''
    Tkinter configurable form.

    arguments for __init__:
    master -- master widget for form.
    tk_form_configuration -- configuration. See help(ConfigEntry) for details.
    use_scrollview -- shoud we use scrollable canvas instead of just tkinter frame?
    '''
    def __init__(self,master,tk_form_configuration,use_scrollview=True,color_index=0, protection=False):
        super(TkDictForm, self).__init__(master)
        self.color_index = color_index
        self.configure(index_to_style(color_index))
        self.master = master
        self.tk_form_configuration = tk_form_configuration
        self.on_commit = None

        if use_scrollview:
            self.formview = ScrollView(self)
            self.formview.pack(side="top",fill="both",expand=True)
            self.contents_tgt = self.formview.contents
        else:
            self.formview = None
            self.contents_tgt = tk.Frame(self)
            self.contents_tgt.pack(fill="both",expand=True)

        self.fields = dict()
        for i in tk_form_configuration.keys():
            conf = tk_form_configuration[i]
            name = i
            field = create_field(name, self.contents_tgt, conf, self.color_index, controller=self, protection=protection)
            self.fields[i] = field

    def get_values(self):
        '''
        Get dictionary of field values.
        '''
        res = dict()
        for i in self.tk_form_configuration.keys():
            val = self.fields[i].get_value()
            if (val is not None) or self.fields[i].keep_none():
                res[i] = val
        return res

    def set_values(self, values, force=False):
        '''
        Set fields by dictionary of values. Will set only present fields.
        '''
        keys = set(values.keys()).intersection(set(self.fields.keys()))
        #print("Requested values:",list(values.keys()))
        #print("Available values:",list(self.fields.keys()))
        for i in keys:
            self.fields[i].set_value(values[i], force=force)

    def trigger_change(self):
        if self.on_commit:
            self.on_commit()
