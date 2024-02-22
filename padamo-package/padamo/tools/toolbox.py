import tkinter as tk
from tkinter import ttk

class Toolbox(ttk.Notebook):
    def __init__(self, master):
        super().__init__(master)
        self.globals = dict()
        self.tools = []

    def add_tool(self, tool_cls):
        tool = tool_cls(self,self.globals)
        self.add(tool,text=tool_cls.TAB_LABEL)
        self.tools.append(tool)
        return tool

    def get_current_tool(self):
        i = self.index("current")
        return self.tools[i]

    def trigger_globals_update(self, exclude=None):
        for t in self.tools:
            if t != exclude:
                t.on_globals_update()
