import tkinter as tk
from tkinter import ttk

import PIL.Image
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from matplotlib.axes import Axes
import numpy as np
from matplotlib.patches import Rectangle
from matplotlib.pyplot import Normalize
from .modified_base import EntryWithEnterKey
matplotlib.use("TkAgg")

HALF_PIXELS = 8
PIXEL_SIZE = 2.85
HALF_GAP_SIZE = 2.0
SCALE_FLOATING_POINT_FORMAT = "{:.2f}"
PLOT_HIGHLIGHT_COLOR = "red"
PLOT_BROKEN_COLOR = "black"
PLOT_COLORMAP = matplotlib.colormaps["viridis"]

LOWER_EDGES = np.arange(HALF_PIXELS)*PIXEL_SIZE+HALF_GAP_SIZE
LOWER_EDGES = np.concatenate([-np.flip(LOWER_EDGES)-PIXEL_SIZE, LOWER_EDGES])


def find_index(coord: np.ndarray):
    coord_sign = np.sign(coord)
    coord_abs = np.abs(coord)
    inbounds = np.logical_and(coord_abs <= HALF_GAP_SIZE+HALF_PIXELS*PIXEL_SIZE, coord_abs >= HALF_GAP_SIZE)

    pre_index = ((coord_abs-HALF_GAP_SIZE) / PIXEL_SIZE + HALF_PIXELS).astype(int)
    after_index = pre_index * (coord_sign > 0) + (2*HALF_PIXELS - 1 - pre_index) * (coord_sign < 0)

    return after_index * inbounds - (np.logical_not(inbounds))


class Plotter(ttk.Frame):
    def __init__(self, master, polar=False,figure=None, axes=None, *args, **kwargs):
        super(Plotter, self).__init__(master, *args, **kwargs)
        self.figure: Figure
        if figure is None:
            self.figure = Figure(figsize=(4, 4), dpi=100)
        else:
            self.figure = figure
        self.figure: Figure
        self.axes: Axes
        if figure is None:
            self.axes = self.figure.add_subplot(1, 1, 1, polar=polar)
        else:
            self.axes = axes
        self.axes: Axes

        self.mpl_canvas = FigureCanvasTkAgg(self.figure, self)
        self.mpl_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.toolbar = NavigationToolbar2Tk(self.mpl_canvas, self)
        self.toolbar.update()


    def allow_callbacks(self):
        return not self.figure.canvas.toolbar.mode

    def draw(self, fast=True):
        #self.figure.canvas.draw()
        #self.figure.canvas.flush_events()
        if fast:
            self.mpl_canvas.draw_idle()
        else:
            self.mpl_canvas.draw()


class PlottingToplevel(tk.Toplevel):
    def __init__(self,figure, axes, master=None):
        super().__init__(master)
        self.plotter = Plotter(self,figure=figure,axes=axes)
        self.plotter.pack(fill="both",expand=True)


def create_tuloma_grid(axes):
    axes.set_box_aspect(1)
    span = HALF_PIXELS*PIXEL_SIZE+HALF_GAP_SIZE
    axes.vlines(LOWER_EDGES, -span, -HALF_GAP_SIZE, colors="black")
    axes.vlines(LOWER_EDGES, span, HALF_GAP_SIZE, colors="black")
    axes.vlines([-HALF_GAP_SIZE, span], -span, -HALF_GAP_SIZE, colors="black")
    axes.vlines([-HALF_GAP_SIZE, span], span, HALF_GAP_SIZE, colors="black")
    axes.hlines(LOWER_EDGES, -span, -HALF_GAP_SIZE, colors="black")
    axes.hlines(LOWER_EDGES, span, HALF_GAP_SIZE, colors="black")
    axes.hlines([-HALF_GAP_SIZE, span], -span, -HALF_GAP_SIZE, colors="black")
    axes.hlines([-HALF_GAP_SIZE, span], span, HALF_GAP_SIZE, colors="black")
    axes.set_xlim(-span, span)
    axes.set_ylim(-span, span)

class TulomaGridView(object):
    def __init__(self, axes, initcolor="blue"):
        self._grid_axes = axes

        self.patches = []
        for y in LOWER_EDGES:
            row = []
            for x in LOWER_EDGES:
                rect = Rectangle((x, y), PIXEL_SIZE, PIXEL_SIZE, color=initcolor,
                                 linewidth=1,
                                 edgecolor='black')
                self._grid_axes.add_patch(rect)
                row.append(rect)
            self.patches.append(row)

        for y in LOWER_EDGES:
            for x in LOWER_EDGES:
                rect = Rectangle((x, y), PIXEL_SIZE, PIXEL_SIZE, fill=None,
                                 linewidth=1,
                                 edgecolor='black')
                self._grid_axes.add_patch(rect)

        axes.set_box_aspect(1)
        span = HALF_PIXELS*PIXEL_SIZE+HALF_GAP_SIZE
        axes.set_xlim(-span, span)
        axes.set_ylim(-span, span)
        #create_tuloma_grid(self._grid_axes)

    def set_colors(self, color_mat):
        for j in range(2 * HALF_PIXELS):
            for i in range(2 * HALF_PIXELS):
                self.set_pixel_color(j,i,color_mat[i,j])

    def set_pixel_color(self,j,i, color):
        self.patches[j][i].set_color(color)

