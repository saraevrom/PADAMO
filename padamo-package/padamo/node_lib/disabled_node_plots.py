from matplotlib import pyplot as plt
import numpy as np
import numba as nb

from padamo.node_processing import Node, ANY, STRING, PLOT, SIGNAL, ARRAY, DETECTOR
from padamo.lazy_array_operations import LazyArrayOperation
from padamo.utilities.plot import LazyPlotter
from typing import Optional
from padamo.utilities.dual_signal import Signal
from padamo.ui_elements.plotter import HALF_PIXELS,LOWER_EDGES, create_tuloma_grid, PIXEL_SIZE, Rectangle
from padamo.ui_elements.configurable_gridview import DeviceParameters, ConfigurableGridView

# GRID BASED COLORATION
def hsv_to_rgb(h,s,v):
    '''
    0<=h<=360
    0<=s<=1
    0<=v<=1
    '''
    h = h % 360
    c = v*s
    x = c*(1-abs((h/60)%2-1))
    m = v-c
    if h<60:
        _r = c; _g = x; _b = 0
    elif h<120:
        _r = x
        _g = c
        _b = 0
    elif h<180:
        _r = 0
        _g = c
        _b = x
    elif h<240:
        _r = 0
        _g = x
        _b = c
    elif h<300:
        _r = x
        _g = 0
        _b = c
    else:
        _r = c
        _g = 0
        _b = x
    return _r+m, _g+m, _b+m


def h_color(i, hue_shift=0.0,s_shift = 0.0, v_shift = 0.0):
    h = (i)/8*360+hue_shift
    s = 1-s_shift
    v = 1-v_shift
    return hsv_to_rgb(h,s,v)

WIDTH = 2*HALF_PIXELS
HEIGHT = 2*HALF_PIXELS


def floormod(x,y):
    pivot = int(np.floor(x/y))*y
    return x-pivot

def get_color(i,j):
    if i%2==0:
        j1 = j
    else:
        j1 = j + 1
    shift_id = floormod(floormod(i-j1*WIDTH//4,WIDTH),WIDTH)
    gray_shift = 0.0
    if j%2==0 and (i-j//2)%2==0:
        gray_shift = 1.0
    return h_color(shift_id,j/HEIGHT*180,
                   v_shift=gray_shift*0.5,
                   s_shift=gray_shift*0.3)


class LazyLabeller(LazyPlotter):
    def __init__(self, earlier:Optional[LazyPlotter], x_label:Optional[str], y_label:Optional[str], title:Optional[str]):
        self.earlier = earlier
        self.x_label = x_label
        self.y_label = y_label
        self.title = title

    def apply(self, figure:plt.Figure, axes:plt.Axes):
        if self.earlier is not None:
            self.earlier.apply(figure,axes)
        if self.x_label is not None:
            axes.set_xlabel(self.x_label)
        if self.y_label is not None:
            axes.set_ylabel(self.y_label)
        if self.title is not None:
            axes.set_title(self.title)

class SetLabelsNode(Node):
    INPUTS = {
        "plot":PLOT,
        "x_label":STRING,
        "y_label":STRING,
        "title":STRING
    }
    OUTPUTS = {
        "plot":PLOT
    }
    LOCATION = "/Plotter/Label plot"
    REPR_LABEL = "Label plot"

    def calculate(self, globalspace:dict) ->dict:
        plot = self.require( "plot", optional=True)
        x_label = self.require( "x_label", optional=True)
        y_label = self.require( "y_label", optional=True)
        title = self.require("title", optional=True)
        return dict(plot=LazyLabeller(plot, x_label, y_label, title))

class LazyXlim(LazyPlotter):
    def __init__(self, earlier:Optional[LazyPlotter], lower, upper):
        self.earlier = earlier
        self.lower = lower
        self.upper = upper

    def apply(self, figure:plt.Figure, axes:plt.Axes):
        if self.earlier is not None:
            self.earlier.apply(figure,axes)
        axes.set_xlim(self.lower, self.upper)

class LazyYlim(LazyPlotter):
    def __init__(self, earlier:Optional[LazyPlotter], lower, upper):
        self.earlier = earlier
        self.lower = lower
        self.upper = upper

    def apply(self, figure:plt.Figure, axes:plt.Axes):
        if self.earlier is not None:
            self.earlier.apply(figure,axes)
        axes.set_ylim(self.lower, self.upper)


class SetXlimNode(Node):
    INPUTS = {
        "plot": PLOT,
        "lower": ANY,
        "upper": ANY,
    }
    OUTPUTS = {
        "plot": PLOT
    }
    LOCATION = "/Plotter/Set X limits"
    REPR_LABEL = "Set X limits"

    def calculate(self, globalspace:dict) ->dict:
        plot = self.require("plot",optional=True)
        lower = self.require( "lower", optional=True)
        upper = self.require( "upper", optional=True)
        return dict(plot=LazyXlim(plot,lower,upper))



class SetYlimNode(Node):
    INPUTS = {
        "plot": PLOT,
        "lower": ANY,
        "upper": ANY,
    }
    OUTPUTS = {
        "plot": PLOT
    }
    LOCATION = "/Plotter/Set Y limits"
    REPR_LABEL = "Set Y limits"

    def calculate(self, globalspace:dict) ->dict:
        plot = self.require("plot",optional=True)
        lower = self.require( "lower", optional=True)
        upper = self.require( "upper", optional=True)
        return dict(plot=LazyYlim(plot,lower,upper))



@nb.njit()
def find_uneven_resolutions(t, tolerance=1e-6):
    res = nb.typed.List()
    res.append(0)
    resolution = t[1]-t[0]
    for i in range(1,len(t)):
        r1 = t[i]-t[i-1]
        if abs(r1-resolution)>tolerance:
            res.append(i)
    res.append(len(t)+1)
    return res


class LCPlotter(LazyPlotter):
    def __init__(self, lc_signal:Signal, color, linestyle, find_uneven=False, tolerance=1e-6):
        self.lc_signal = lc_signal
        self.color = color
        self.linestyle = linestyle
        self.find_uneven = find_uneven
        self.tolerance = tolerance

    def apply(self, figure:plt.Figure, axes:plt.Axes):
        spatial = self.lc_signal.space.request_all_data()
        temporal = self.lc_signal.time.request_all_data()
        if self.find_uneven:
            breaks = find_uneven_resolutions(temporal)
            for i in range(len(breaks)-1):
                start = breaks[i]
                end = breaks[i+1]-1
                axes.plot(temporal[start:end], spatial[start:end], self.linestyle, color=self.color)
        else:
            axes.plot(temporal,spatial,self.linestyle, color=self.color)


class LCPlotterNode(Node):
    INPUTS = {
        "lightcurve": SIGNAL,
        "color": STRING,
        "linestyle":STRING
    }
    CONSTANTS = {
        "detect_uneven":False,
        "tolerance":1e-6
    }
    OUTPUTS = {
        "plot":PLOT
    }

    LOCATION = "/Plotter/Lightcurve plot"
    REPR_LABEL = "Lightcurve plot"

    def calculate(self, globalspace:dict) ->dict:
        lc = self.require( "lightcurve")
        color = self.require( "color", optional=True) or "black"
        linestyle = self.require("linestyle", optional=True) or "-"
        return dict(plot=LCPlotter(lc,color,linestyle, self.constants["detect_uneven"], self.constants["tolerance"]))


class LazyChannelPlotter(LazyPlotter):
    def __init__(self, source:Signal, pixelmap:LazyArrayOperation):
        self.source = source
        self.pixelmap = pixelmap

    def apply(self, figure:plt.Figure, axes:plt.Axes):
        pixelmap = self.pixelmap.request_all_data()
        x_data = self.source.time.request_all_data()
        y_data = self.source.space.request_all_data()
        pix_shape = self.pixelmap.shape()
        if len(pix_shape)!=2:
            raise ValueError("Pixel map can have only 2D arrays")
        for i in range(pix_shape[0]):
            for j in range(pix_shape[1]):
                if pixelmap[i,j]:
                    axes.plot(x_data,y_data[:,i,j], color=get_color(i,j))


class LazyPixelmapInserter(LazyPlotter):
    def __init__(self, pixelmap:LazyArrayOperation, bounds, conf):
        self.pixelmap = pixelmap
        self.bounds = bounds
        self.conf = conf

    def apply(self, figure:plt.Figure, axes:plt.Axes):
        pixelmap = self.pixelmap.request_all_data()
        if len(pixelmap.shape)!=2:
            raise ValueError("Pixelmap must have 2 dimensions")
        if pixelmap.shape!=(16,16):
            raise ValueError(f"Tuloma PDM has 16x16 frame but {pixelmap.shape[0]}x{pixelmap.shape[1]} was supplied")
        axin1 = axes.inset_axes(self.bounds)
        axin1.get_xaxis().set_visible(False)
        axin1.get_yaxis().set_visible(False)
        view = ConfigurableGridView(axin1)
        view.configure_detector(self.conf)

        # create_tuloma_grid(axin1)
        # for j,y in enumerate(LOWER_EDGES):
        #     for i,x in enumerate(LOWER_EDGES):
        #         if pixelmap[i,j]:
        #             rect = Rectangle((x, y), PIXEL_SIZE, PIXEL_SIZE, color=get_color(i,j))
        #             axin1.add_patch(rect)


class ChannelPlotterNode(Node):
    INPUTS = {
        "signal":SIGNAL,
        "pixelmap":ARRAY,
    }
    OUTPUTS = {
        "plot":PLOT
    }

    LOCATION = "/Plotter/Pixel plot"
    REPR_LABEL = "Pixel plot"

    def calculate(self, globalspace:dict) ->dict:
        signal = self.require("signal")
        pixelmap = self.require("pixelmap")
        return dict(plot=LazyChannelPlotter(signal,pixelmap))


class VTLPixelMapPlotterNode(Node):
    INPUTS = {
        "pixelmap":ARRAY,
        "device_config":DETECTOR
    }
    CONSTANTS = {
        "x0":0.00,
        "y0":0.65,
        "width":0.35,
        "height":0.35
    }
    OUTPUTS = {
        "plot": PLOT
    }

    LOCATION = "/Plotter/Detector pixelmap"
    REPR_LABEL = "Detector pixelmap"

    def calculate(self, globalspace:dict) ->dict:
        pixelmap = self.require("pixelmap")
        bounds = [self.constants[i] for i in ["x0","y0","width","height"]]
        return dict(plot=LazyPixelmapInserter(pixelmap,bounds, conf=self.require("device_config")))


class CombinePlots(Node):
    INPUTS = {
        "plot_a":PLOT,
        "plot_b":PLOT
    }
    OUTPUTS = {
        "combination":PLOT
    }

    LOCATION = "/Plotter/Combine plots"
    REPR_LABEL = "Combine plots"

    def calculate(self, globalspace:dict) ->dict:
        a = self.require("plot_a")
        b = self.require("plot_b")
        return dict(combination=(a+b))