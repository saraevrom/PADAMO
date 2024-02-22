from .index import NODES
import tkinter as tk
from tkinter import ttk
from padamo.node_processing import NodeCanvas

class NodeView(ttk.Treeview):
    def __init__(self, master, canvaswrapper:NodeCanvas):
        super().__init__(master)
        self.canvaswrapper = canvaswrapper
        self.heading("#0",text="Node", anchor="w")
        self.nodedict = {}
        self.actiondict = {}
        for node in NODES:
            loc = node.LOCATION
            if loc.startswith("/"):
                loc = loc[1:]
            loc = loc.split("/")
            node_loc = loc[:-1]
            node_name = loc[-1]
            #print(loc)
            workon = ["",self.nodedict]
            for item in node_loc:
                parent, inner_dict = workon
                if item not in inner_dict.keys():
                    #print("ADD", item)
                    inner_dict[item] = [self.insert(parent=parent,text=item,index=tk.END), dict()]
                workon = inner_dict[item]
            parent, inner_dict = workon
            inner_dict[node_name] = [self.insert(parent=parent,text=node_name,index=tk.END), node]
            iid,node_cls = inner_dict[node_name]
            self.actiondict[iid] = node_cls
        self.bind("<Double-1>", self.on_dblclick)

    def on_dblclick(self, event):
        selected_items = self.selection()
        if not selected_items:
            return
        item_iid = selected_items[0]
        if item_iid in self.actiondict:
            cls = self.actiondict[item_iid]
            cls.add_graphnode(self.canvaswrapper)