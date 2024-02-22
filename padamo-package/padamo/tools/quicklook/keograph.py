import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import Normalize

from padamo.lazy_array_operations import LazyArrayOperation
from padamo.utilities.dual_signal import Signal
from padamo.ui_elements.plotter import Plotter, PLOT_COLORMAP
from padamo.ui_elements.plotter import LOWER_EDGES, PIXEL_SIZE
from mpl_toolkits.axes_grid1 import make_axes_locatable

CENTERS = LOWER_EDGES+PIXEL_SIZE/2

MODE_MAINDIAG = 0
MODE_INVDIAG = 1


def get_pixels(mode):
    if mode==MODE_MAINDIAG:
        x = np.arange(16)
        x = np.vstack([x,x])
        return x
    elif mode==MODE_INVDIAG:
        x = np.arange(16)
        y = 15-x
        return np.vstack([x,y])


class KeogramPlotter(Plotter):
    def __init__(self,master, mode):
        super().__init__(master)
        self.mode = mode
        self.colorbar = None
        self.norm = None

    def plot_data(self, spatial,times, levels=None):
        title = self.axes.get_title()
        self.axes.clear()
        pixels = get_pixels(self.mode)
        pixel_ys = CENTERS*(2**0.5)
        # times = src.time.request_all_data()
        # spatial = src.space.request_all_data()
        if len(times.shape)>1:
            times = times[:,0]
        print("TIMES", times)
        self.axes:plt.Axes
        spatial_all = spatial[:,pixels[0],pixels[1]]

        spatial_low = spatial[:,pixels[0][:8],pixels[1][:8]]
        times = (1000*times).astype('datetime64[ms]')
        X, Y = np.meshgrid(times, pixel_ys[:8], indexing="ij")
        self.axes.contourf(X,Y,spatial_low, levels=levels)

        spatial_up = spatial[:, pixels[0][8:], pixels[1][8:]]
        X, Y = np.meshgrid(times, pixel_ys[8:], indexing="ij")
        self.axes.contourf(X, Y, spatial_up, levels=levels)

        low = np.min(spatial_all)
        high = np.max(spatial_all)

        if self.norm is None:
            self.norm = Normalize(low, high)
        else:
            # Magic: pyplot requires to assign twice
            self.norm.vmin = low
            self.norm.vmin = low
            self.norm.vmax = high
            self.norm.vmax = high

        if self.colorbar is None:
            self.colorbar = self.figure.colorbar(plt.cm.ScalarMappable(norm=self.norm, cmap=PLOT_COLORMAP),
                                                 orientation='vertical', ax=self.axes)
        self.axes.set_title(title)
        self.axes.relim()
        self.toolbar.update()
        self.draw()
        print("Keoghraph ready")
