import os
import tkinter as tk
import typing

import matplotlib
matplotlib.use('Agg')
import matplotlib as mpl
import matplotlib.pyplot as plt
from padamo.ui_elements.configurable_gridplotter import ConfigurableGridAxes, PLOT_COLORMAP
from matplotlib.backends.backend_agg import FigureCanvasAgg

import PIL.Image
import numpy as np


class DetachedPlotter(ConfigurableGridAxes):
    def __init__(self, fig_size, autoscale, min_, max_, dpi=100):
        with mpl.rc_context({"backend": "agg"}):
            figure = plt.Figure(figsize=fig_size, dpi=dpi)
            axes = figure.add_subplot(111)
            self.canvas = FigureCanvasAgg(figure)
            self.figure = figure
            self.axes = axes
            self._cax_tuple = None
        self.autoscale = autoscale
        self.min_ = min_
        self.max_ = max_
        super().__init__(figure=figure, axes=axes, norm=None, bright=False)
        self.draw()

    def draw(self):
        self.canvas.draw()

    def correct_colorbar(self,norm):
        if os.name != "nt" or self.autoscale:
            super().correct_colorbar(norm)
            return 

        # Windows colorbar update is broken. Recreating it.
        # Linuxes don't have such problem
        # Also not needed if scale range is static
        if self.colorbar is not None:

            self.colorbar.remove()
            cax = self.figure.add_axes(self._cax_tuple)
            self.colorbar = self._conf_grid_figure.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=PLOT_COLORMAP),
                                                            cax=cax)
        else:
            self.colorbar = self._conf_grid_figure.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=PLOT_COLORMAP),
                                                            ax=self._conf_grid_axes)
            cax_pos = self.figure.axes[1].get_position()
            self._cax_tuple = (cax_pos.x0, cax_pos.y0, cax_pos.width/2, cax_pos.height)

    def update_norm_modulate(self,low_fallback,high_fallback) -> typing.Tuple[float,float]:
        if self.autoscale:
            #print(low_fallback,high_fallback)
            #assert high_fallback>=low_fallback
            return float(low_fallback), float(high_fallback)
        else:
            return self.min_, self.max_

    def update_norm(self, low_fallback=None, high_fallback=None):
        #super().update_norm(low_fallback,high_fallback)
        super().update_norm(low_fallback,high_fallback)
        #self.draw()

    def get_frame(self):
        rgba = np.asarray(self.canvas.buffer_rgba())
        return PIL.Image.fromarray(rgba)
