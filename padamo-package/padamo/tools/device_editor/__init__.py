import tkinter as tk

from padamo.ui_elements.configurable_gridview import DeviceParameters
from ..base import Tool
from padamo.ui_elements.configurable_gridplotter import ConfigurableGridPlotter
from padamo.ui_elements.button_panel import ButtonPanel
from padamo.ui_elements.tk_forms import TkDictForm
from .form import DetectorParser
from .workspace import DetectorWorkspace
from padamo.node_processing.node_canvas import GraphDraggableNode


DETECTOR_WORKSPACE = DetectorWorkspace("detectors")

class DeviceEditor(Tool):
    TAB_LABEL = "Detector"

    def __init__(self, master, globals_):
        Tool.__init__(self, master, globals_)
        self.plotter = ConfigurableGridPlotter(self)
        self.plotter.pack(side="left", fill="both", expand=True)
        rpanel = tk.Frame(self)
        rpanel.pack(side="right",fill="y")
        buttonpanel = ButtonPanel(rpanel)
        buttonpanel.pack(side="top", fill="x")

        self._config = None

        self.form_parser = DetectorParser()
        self.form = TkDictForm(rpanel,self.form_parser.get_configuration_root())
        self.form.pack(side="bottom", fill="both", expand=True)
        self.form.on_commit = self.on_form_commit
        self.on_form_commit()


    def on_save(self):
        if self._config is None:
            return
        filename = DETECTOR_WORKSPACE.asksaveasfilename(defaultextension="*.json", filetypes=[("Detector configuration", "*.json")])
        if filename:
            with open(filename,"w") as fp:
                fp.write(self._config.to_json())

    def on_load(self):
        filename = DETECTOR_WORKSPACE.askopenfilename(defaultextension="*.json", filetypes=[("Detector configuration", "*.json")])
        if filename:
            with open(filename, "r") as fp:
                self._config = DeviceParameters.from_json(fp.read())
                self.form_parser.set_data(self._config)
                self.form.set_values(self.form_parser.recover_formdata(),True)
                self.on_config_update()

    def on_form_commit(self):
        formdata = self.form.get_values()
        self.form_parser.parse_formdata(formdata)
        self._config = self.form_parser.get_data()
        self.on_config_update()

    def on_config_update(self):
        self.plotter.configure_detector(self._config)