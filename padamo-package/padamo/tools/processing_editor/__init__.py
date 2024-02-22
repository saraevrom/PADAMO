import json
import os
import traceback
import tkinter as tk
import sys
from tkinter import filedialog, messagebox

import toposort

from padamo.node_lib import NodeView
from padamo.tools.base import Tool

from padamo.editing import VolatileEditorWindow
from padamo.node_processing.node_canvas import NodeCanvas, NodeExecutionError, GraphDraggableNode
from .workspace import GraphWorkspace
from padamo.utilities.workspace import Workspace

from  padamo.ui_elements.button_panel import ButtonPanel

STATIC_GRAPH_WORKSPACE = GraphWorkspace()
GRAPH_WORKSPACE = Workspace("graphs")


def get_default_filename():
    return STATIC_GRAPH_WORKSPACE("default_scheme.json")

class ProcessingEditor(Tool):
    TAB_LABEL = "Processing"

    def __init__(self, master, globals_):
        super().__init__(master, globals_)
        mainframe = tk.Frame(self)
        mainframe.pack(fill="both", expand=True)
        rpanel = tk.Frame(mainframe)
        rpanel.pack(side="right", fill="y")

        buttonpanel = ButtonPanel(rpanel)
        buttonpanel.pack(side="bottom", fill="x")
        buttonpanel.add_button("Delete selected node", self.on_delete_node)

        self.inspector = VolatileEditorWindow(rpanel)
        self.canvas_wrapper = NodeCanvas(mainframe, self.inspector, bg="#AAAAAA")
        self.node_src = NodeView(mainframe, self.canvas_wrapper)
        self.node_src.pack(side="left", fill="y")
        self.canvas_wrapper.pack(side="left", fill="both", expand=True)
        self.inspector.pack(side="top", fill="both", expand=True)
        self._was_error = None
        bpanel = tk.Frame(self)
        bpanel.pack(side="bottom")
        runbtn = tk.Button(bpanel, text="Run", command=self.on_run)
        runbtn.grid(row=0, column=0)
        default_set = tk.Button(bpanel, text="Set as default", command=self.on_save_default)
        default_set.grid(row=0, column=1)

        default_file = get_default_filename()
        if not os.path.isfile(default_file):
            STATIC_GRAPH_WORKSPACE.populate()
        if os.path.isfile(default_file):
            try:
                self.load_file(default_file)
            except KeyError:
                os.remove(default_file)


    def on_delete_node(self):
        GraphDraggableNode.remove_selected()

    def on_save(self):
        filename = GRAPH_WORKSPACE.asksaveasfilename(defaultextension="*.json", filetypes=[("Schematic","*.json")])
        if filename:
            self.save_profile(filename)

    def on_save_default(self):
        if messagebox.askyesno("Set default", "Are you sure that you want to save this profile as default?",
                               default=messagebox.NO):
            filename = get_default_filename()
            self.save_profile(filename)

    def save_profile(self,filename):
        serialized = self.canvas_wrapper.serialize()
        with open(filename, "w") as fp:
            json.dump(serialized, fp, indent=4)

    def on_load(self):
        filename = GRAPH_WORKSPACE.askopenfilename(defaultextension="*.json", filetypes=[("Schematic","*.json")])
        if filename:
            self.load_file(filename)
            self.on_run()

    def load_file(self, filename):
        with open(filename, "r") as fp:
            serialized = json.load(fp)
        self.canvas_wrapper.deserialize(serialized)


    def on_run(self):
        if self._was_error:
            self.canvas_wrapper.remove_highlight()
            self._was_error = False
        try:
            objections = self.ask_any_objections("run")
            if not objections:
                self.canvas_wrapper.calculate(self.globals)
        except toposort.CircularDependencyError as e:
            messagebox.showerror("Error",str(e))
        except NodeExecutionError as e:
            messagebox.showerror("Error", str(e))
            self._was_error = True
            self.canvas_wrapper.highlight_node(e.node.graph_node)
            print(traceback.format_exc(), file=sys.stderr)
        self.trigger_globals_update(self)

    def on_globals_update(self):
        self.canvas_wrapper.invalidate_cache()
        #print("GLOBALS UPDATED")
        self.on_run()
