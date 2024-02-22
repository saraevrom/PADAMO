import tkinter as tk
from tkinter import ttk
from .editors import pick_editor, Editor
from padamo.canvas_drawing.linkable_nodes import DraggableNode




class ScrollView(ttk.Frame):
    '''
    Class for scrollable frame view
    Obtained from tutorial at https://blog.teclado.com/tkinter-scrollable-frames/
    '''
    def __init__(self,parent,*args,**kwargs):
        super().__init__(parent,*args,**kwargs)
        self.canvas = tk.Canvas(self,width=200)
        self.v_scrollbar = tk.Scrollbar(self,orient="vertical",command = self.canvas.yview)
        #self.h_scrollbar = tk.Scrollbar(self,orient="horizontal",command = self.canvas.xview)

        self.contents = tk.Frame(self.canvas)
        self.contents.bind("<Configure>", self.on_content_change)
        self.drawn_window_id = self.canvas.create_window((0,0), window=self.contents,anchor="nw")
        self.canvas.configure(yscrollcommand=self.v_scrollbar.set)#,xscrollcommand=self.h_scrollbar.set)
        # self.h_scrollbar.pack(side="bottom", fill="x")
        # self.v_scrollbar.pack(side="right", fill="y")
        # self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        #self.h_scrollbar.grid(row=1, column=0, sticky="nsew", columnspan=2)
        self.v_scrollbar.grid(row=0, column=1, sticky="nsew")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.canvas.bind("<Configure>", self.on_canvas_change)

    def on_content_change(self,event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_canvas_change(self, event):
        width = self.canvas.winfo_width()
        #if width<100:
        self.canvas.itemconfig(self.drawn_window_id, width=width)
        #else:
        #    self.canvas.itemconfig(self.drawn_window_id, width=100)


class VolatileEditorWindow(tk.Frame):
    def __init__(self, master):
        super().__init__(master,width=100)
        self.scrollable = ScrollView(self)
        self.scrollable.pack(fill="both",expand=True)
        self.fields = []
        self.linked_node = None

    def delete_fields(self):
        for f in self.fields:
            f.destroy()
        self.fields.clear()

    def get_values(self):
        return {x.name:x.get_value() for x in self.fields}

    def get_states(self):
        return {x.name: x.get_editor_state() for x in self.fields}

    def set_values(self, vs):
        for f in self.fields:
            f.set_value(vs[f.name])

    def set_states(self, states):
        for f in self.fields:
            f.set_editor_state(states[f.name])



    def update_editable_list(self):
        self.delete_fields()
        if self.linked_node is None:
            return
        node = self.linked_node()
        if node is None:
            self.linked_node = None
            return
        node:DraggableNode
        const_dict = node.get_constants()
        for k in const_dict.keys():
            const_def = const_dict[k]
            req_type = pick_editor(const_def.const_type)
            #const_def.associated_link = req_type.ASSOCIATED_LINK_TYPE
            new_field = req_type(self.scrollable.contents, k,self,const_def.const_type,
                                 allow_external=const_def.allow_external, is_optional=const_def.optional)
            new_field.set_editor_state(const_def.state())
            new_field.pack(side="top", fill="x")
            self.fields.append(new_field)

    def update_values(self):
        if self.linked_node is None:
            return
        node = self.linked_node()
        if node is None:
            self.linked_node = None
            return
        states = self.get_states()
        #print(states)
        node.set_constants(states)
