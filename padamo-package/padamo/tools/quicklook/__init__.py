import tkinter as tk
from ..base import Tool
from padamo.ui_elements.button_panel import ButtonPanel
from padamo.ui_elements.tk_forms import TkDictForm
from .keograph import KeogramPlotter
from .spectrograph import SpectraPlotter
from .lightcurve import LCPlotter
from .form import RightForm
from padamo.ui_elements.tk_forms import ScrollView

class Quicklook(Tool):
    TAB_LABEL = "Quick-look"

    def __init__(self, master, globals_):
        Tool.__init__(self, master, globals_)
        self.globals["quicklook_view"] = None
        rpanel = tk.Frame(self)
        rpanel.pack(side="right", fill="both")
        mainview = ScrollView(self)
        mainview.pack(fill="both", expand=True)
        # mainpanel = tk.Frame(self)
        # mainpanel.pack(fill="both", expand=True)
        # mainpanel1 = tk.Frame(mainpanel)
        # mainpanel1.pack(side="top",fill="both", expand=True)
        # mainpanel2 = tk.Frame(mainpanel)
        # mainpanel2.pack(side="top",fill="both", expand=True)

        buttons = ButtonPanel(rpanel)
        buttons.pack(side="top", fill="x")
        buttons.add_button("Create looks",self.on_create_plots,0)

        self.formparser = RightForm()
        self.form = TkDictForm(rpanel,self.formparser.get_configuration_root())
        self.form.on_commit = self.on_commit
        self.form.pack(side="top", fill="x")

        self.keograph_main_diag = KeogramPlotter(mainview.contents,0)
        self.keograph_main_diag.axes.set_title("NS-keogram")
        self.keograph_aux_diag = KeogramPlotter(mainview.contents,1)
        self.keograph_aux_diag.axes.set_title("EW-keogram")

        self.spectrograph = SpectraPlotter(mainview.contents)
        self.lightcurve = LCPlotter(mainview.contents)

        self.keograph_main_diag.grid(row=0, column=0, sticky="nsew")
        self.keograph_aux_diag.grid(row=1, column=0, sticky="nsew")
        self.spectrograph.grid(row=2, column=0, sticky="nsew")
        self.lightcurve.grid(row=3, column=0, sticky="nsew")

        mainview.contents.columnconfigure(0, weight=1)
        for i in range(4):
            mainview.contents.rowconfigure(i, weight=1)
        self.formdata = None
        self.on_commit()

    def on_create_plots(self):
        data = self.globals["quicklook_view"]
        if data is None:
            data = self.globals["current_view"]

        levels = self.formdata["levels"]
        spatial = data.space.request_all_data()
        temporal = data.time.request_all_data()
        self.keograph_main_diag.plot_data(spatial,temporal,levels)
        self.keograph_aux_diag.plot_data(spatial,temporal,levels)
        self.spectrograph.plot_spectra(spatial,temporal,self.formdata["freq_space"],levels)
        self.lightcurve.plot_lightcurve(spatial,temporal)

    def on_commit(self):
        formdata = self.form.get_values()
        self.formparser.parse_formdata(formdata)
        self.formdata = self.formparser.get_data()