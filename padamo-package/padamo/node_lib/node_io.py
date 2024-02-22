import os.path

import matplotlib, h5py
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from padamo.node_processing import Node, ANY, STRING, PLOT, AllowExternal
from tkinter.messagebox import showinfo
from padamo.lazy_array_operations import LazyArrayOperation
from padamo.utilities.plot import LazyPlotter
from padamo.ui_elements.plotter import PlottingToplevel


class LazyHDF5reader(LazyArrayOperation):
    def __init__(self, filename, field):
        self.filename = filename
        self.field = field
        self._file = None
        self.ensure_file()

    def ensure_file(self):
        if not self.filename:
            raise ValueError("Filename is not set")
        if not os.path.isfile(self.filename):
            raise FileNotFoundError(f"File {self.filename} is not found")
        if self._file is None:
            self._file = h5py.File(self.filename,"r")

    def request_data(self, interesting_slices):
        #print("H5",interesting_slices)
        self.ensure_file()
        res = np.array(self._file[self.field][interesting_slices])
        return res

    def shape(self):
        return self._file[self.field].shape






class PrintNode(Node):
    INPUTS = {
        "value": ANY,
    }
    MIN_SIZE = (100, 100)
    LOCATION = "/IO/Print"
    IS_FINAL = True
    REPR_LABEL = "Print"

    def calculate(self, globalspace:dict) ->dict:
        i = self.require("value")
        if isinstance(i,LazyArrayOperation):
            print(i.request_all_data())
        else:
            print(i)
        return dict()


class AlertNode(Node):
    INPUTS = {
        "value": ANY,
    }
    CONSTANTS = {
        "title": AllowExternal("Alert")
    }
    MIN_SIZE = (100, 100)
    LOCATION = "/IO/Alert"
    IS_FINAL = True
    REPR_LABEL = "Alert"

    def calculate(self, globalspace:dict) ->dict:
        i = self.require("value")
        title = self.constants["title"]
        showinfo(title=title, message=str(i))
        return dict()



class GlobalSetNode(Node):
    INPUTS = {
        "value": ANY,
    }
    CONSTANTS = {
        "key": "key"
    }
    MIN_SIZE = (100, 100)
    LOCATION = "/IO/Global set"
    REPR_LABEL = "Global setvar"
    IS_FINAL = True

    def calculate(self, globalspace:dict) ->dict:
        globalspace[self.constants["key"]] = self.require("value")
        return dict()

    @classmethod
    def on_constants_update(cls, graphnode):
        graphnode.set_title(cls.REPR_LABEL + f"({graphnode.get_constant('key')})")


class GlobalGetNode(Node):
    OUTPUTS = {
        "value": ANY,
    }
    CONSTANTS = {
        "key": "key"
    }
    MIN_SIZE = (100, 100)
    LOCATION = "/IO/Global get"
    REPR_LABEL = "Global getvar"
    IS_FINAL = True

    def calculate(self, globalspace:dict) ->dict:
        key = self.constants["key"]
        if key in globalspace.keys():
            v = globalspace[key]
        else:
            v = None
        return dict(value=v)

    @classmethod
    def on_constants_update(cls, graphnode):
        graphnode.set_title(cls.REPR_LABEL + f"({graphnode.get_constant('key')})")

class ShowPlotNode(Node):
    INPUTS = {
        "plot":PLOT
    }
    CONSTANTS = {
        "figure_width":12,
        "figure_height":9
    }
    IS_FINAL = True
    LOCATION = "/IO/Show Plot"
    REPR_LABEL = "Show plot"

    def calculate(self, globalspace:dict) ->dict:
        plotter:LazyPlotter = self.require( "plot")
        with matplotlib.rc_context(dict(backend="TkAgg")):
            fig, ax = plotter.make_plot((self.constants["figure_width"],self.constants["figure_height"]))
            window = PlottingToplevel(fig,ax)

        return dict()

class SavePlotNode(Node):
    INPUTS = {
        "plot":PLOT,
        "path_to_file":STRING
    }
    CONSTANTS = {
        "figure_width":12,
        "figure_height":9,
        "make_dir":True,
        "dual_format":False,
        "font_scale":20,
        "x_label":"",
        "y_label":""
    }
    IS_FINAL = True
    LOCATION = "/IO/Save Plot"
    REPR_LABEL = "Save plot"

    def calculate(self, globalspace:dict) ->dict:
        plotter:LazyPlotter = self.require( "plot")
        filename = self.require("path_to_file")
        dirname = os.path.dirname(filename)
        if self.constants["make_dir"]:
            os.makedirs(dirname,exist_ok=True)
        elif not os.path.isdir(dirname):
            raise NotADirectoryError("Cannot access directory for plot")


        rc = {"font.size":self.constants["font_scale"]}
        with matplotlib.rc_context(rc):
            fig, ax = plotter.make_plot((self.constants["figure_width"],self.constants["figure_height"]))
            if self.constants["x_label"]:
                ax.set_xlabel(self.constants["x_label"])
            if self.constants["y_label"]:
                ax.set_ylabel(self.constants["y_label"])
            if self.constants["dual_format"]:
                fig.savefig(filename+".png")
                fig.savefig(filename+".pdf")
            else:
                fig.savefig(filename)
        return dict()