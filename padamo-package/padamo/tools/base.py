import tkinter as tk
from typing import Callable


class Tool(tk.Frame):
    TAB_LABEL=""
    OBJECTIONS = dict()
    
    def __init__(self, master, globals_):
        super().__init__(master)
        self.globals = globals_
        self.controller = master

    def add_objection_hook(self, key: str, hook: Callable):
        if key not in self.OBJECTIONS.keys():
            self.OBJECTIONS[key] = []
        self.OBJECTIONS[key].append(hook)

    def ask_any_objections(self,key:str):
        if key not in self.OBJECTIONS.keys():
            return False
        for hook in self.OBJECTIONS[key]:
            if hook():
                return True
        return False

    def on_save(self):
        pass

    def on_load(self):
        pass

    def on_globals_update(self):
        pass

    def trigger_globals_update(self, exclude=None):
        #print("GLOBALS UPDATE REQUESTED BY", self)
        self.controller.trigger_globals_update(exclude)

    def set_global(self, key, value, exclude=None):
        self.globals[key] = value
        self.trigger_globals_update(exclude)

    def set_title(self, appended):
        self.winfo_toplevel().title("Signal viewer "+appended)