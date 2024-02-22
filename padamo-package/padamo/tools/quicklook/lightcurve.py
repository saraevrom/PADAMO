import matplotlib.pyplot as plt
import numpy as np
from numpy.fft import fft, fftfreq
from matplotlib.colors import Normalize
from numpy.lib.stride_tricks import sliding_window_view

from padamo.lazy_array_operations import LazyArrayOperation
from padamo.utilities.dual_signal import Signal
from padamo.ui_elements.plotter import Plotter, PLOT_COLORMAP
from padamo.ui_elements.plotter import LOWER_EDGES, PIXEL_SIZE
from mpl_toolkits.axes_grid1 import make_axes_locatable


class LCPlotter(Plotter):
    def __init__(self,master):
        super().__init__(master)
        self.colorbar = None
        self.norm = None
        self.axes.set_title("Ligth Curve")
        self.colorbar = None
        self.norm = None

    def plot_lightcurve(self,spatial,temporal,):
        self.axes.clear()
        times = (1000*temporal).astype("datetime64[ms]")
        lc = np.sum(spatial,axis=(1,2))
        self.axes.plot(times,lc,color="black")
        self.axes.set_title("Ligthcurve")
        self.toolbar.update()
        self.draw()
        print("LC ready")