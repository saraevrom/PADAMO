import matplotlib as mpl
import PIL.Image
import matplotlib.pyplot as plt
import numpy as np
from padamo.ui_elements.utilities import set_vlines_position
from matplotlib.backends.backend_agg import FigureCanvasAgg

class LCPlotter(object):
    def __init__(self, y_data, figsize,dpi=100):
        with mpl.rc_context({"backend": "agg"}):
            figure = plt.Figure(figsize=figsize,dpi=dpi)
            axes = figure.add_subplot(111)
            self.canvas = FigureCanvasAgg(figure)
            self.figure = figure
            self.axes = axes
        self.axes.get_xaxis().set_visible(False)
        self.axes.get_yaxis().set_visible(False)
        lc = np.sum(y_data, axis=(1,2))
        self.lc = lc
        xs = np.arange(lc.shape[0])
        self.axes.plot(xs, lc, color="black")
        min_y, max_y = self.axes.get_ylim()
        self.v_line = self.axes.vlines(0, min_y, max_y, color="red")
        self.axes.set_ylim(min_y, max_y)
        self.axes.set_xlim(0,xs[-1])
        self.last_x = xs[-1]
        self.figure.tight_layout()
        self.canvas.draw()

    def set_frame(self, i):
        set_vlines_position(self.v_line,i)
        self.canvas.draw()

    def get_frame(self):
        rgba = np.asarray(self.canvas.buffer_rgba())
        return PIL.Image.fromarray(rgba)
        #return PIL.Image.frombytes('RGB', self.figure.canvas.get_width_height(), self.figure.canvas.tostring_rgb())
