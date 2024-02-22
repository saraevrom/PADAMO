# import os
# import multiprocessing


from numba import config as numba_config,threading_layer
# Prevent some errors
numba_config.THREADING_LAYER = "tbb"
print(f"Default threading layer request: {numba_config.THREADING_LAYER}")

import tkinter as tk
from .tools import Toolbox,Viewer,ProcessingEditor,Quicklook,RemoteExplorer,Bookmarker,DeviceEditor,Trigger
from .node_lib.index import load_addons
from .utilities.workspace import Workspace
from .build import APP_NAME

print(f"Threading layer chosen: {threading_layer()}")

class Application(tk.Tk):
    def __init__(self):
        Workspace.initialize_workspace(False)
        super().__init__()
        load_addons()
        self.title(APP_NAME)

        self.toolbox = Toolbox(self)
        self.toolbox.pack(fill="both",expand=True)
        self.viewer = self.toolbox.add_tool(Viewer)
        self.editor = self.toolbox.add_tool(ProcessingEditor)
        self.trigger = self.toolbox.add_tool(Trigger)
        self.quicklook = self.toolbox.add_tool(Quicklook)
        self.remote_explorer = self.toolbox.add_tool(RemoteExplorer)
        self.bookmarker = self.toolbox.add_tool(Bookmarker)
        self.device_editor = self.toolbox.add_tool(DeviceEditor)
        self.viewer.bookmarker = self.bookmarker
        topmenu = tk.Menu(self)

        filemenu = tk.Menu(topmenu, tearoff=0)
        filemenu.add_command(command=self.on_load, label="Load")
        filemenu.add_command(command=self.on_save, label="Save")

        runmenu = tk.Menu(topmenu, tearoff=0)
        runmenu.add_command(command=self.on_run, label="Run")

        settings_menu = tk.Menu(topmenu, tearoff=0)
        settings_menu.add_command(command=self.on_settings_setup, label="Setup workspace")

        topmenu.add_cascade(label="File", menu=filemenu)
        topmenu.add_cascade(label="Run", menu=runmenu)
        topmenu.add_cascade(label="Settings", menu=settings_menu)

        self.configure(menu=topmenu)
        # if os.path.exists(default_reader):
        #     self.editor:ProcessingEditor
        #     self.editor.load_file(default_reader)

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_signal_compile(self):
        pass

    def on_settings_setup(self):
        Workspace.initialize_workspace(True)

    def on_run(self):
        self.editor:ProcessingEditor
        self.editor.on_run()

    def on_save(self):
        self.toolbox.get_current_tool().on_save()

    def on_load(self):
        self.toolbox.get_current_tool().on_load()

    def on_close(self, *args):
        self.bookmarker.save_bookmarks()
        self.destroy()
