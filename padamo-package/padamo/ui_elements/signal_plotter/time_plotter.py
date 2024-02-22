import contextlib
import datetime
import io
import logging
import warnings

import numpy.random as rng
import numpy as np
import numba as nb
from .binsearch import binsearch_tgt
from ..plotter import Plotter

from ..utilities import set_vlines_position, set_vlines_position_ylims

from ..plotter import SCALE_FLOATING_POINT_FORMAT
from .grid_display import get_color, AltLegendView
from .style_dialog import StyleDialog

@nb.njit()
def window_limiting(index, window, target_length):
    if window>target_length:
        return 0, target_length
    start = index - window // 2
    if start < 0:
        start = 0
    end = start + window
    if end > target_length:
        end = target_length
        start = end - window
    return start, end

@nb.njit()
def moving_average(src, win):
    res = np.zeros(shape=src.shape)
    for i in range(src.shape[0]):
        start, end = window_limiting(i,win,src.shape[0])
        res[i] = np.mean(src[start:end])
    return res



LEGEND_PARAMS = dict(loc='upper right')
MPL_LOGGER = logging.getLogger("matplotlib")


class MainPlotter(Plotter):
    def __init__(self, master, x_plot, display_data,conf):
        super().__init__(master)
        self._use_offset = False
        self._suppress_negative = False
        self.lines = []
        for i in range(display_data.shape[1]):
            line_row = []
            for j in range(display_data.shape[2]):
                line, = self.axes.plot(x_plot, display_data[:,i,j], c=get_color(i,j), label="_hidden")
                line.set_visible(False)
                line_row.append(line)
            self.lines.append(line_row)
        self.display_data = display_data
        self.use_mean = False
        self.flatten_ma = 1
        self.accumulated, = self.axes.plot(x_plot, np.zeros(shape=display_data.shape[0]), "-",
                                           color="black", label="_hidden")
        self.accumulated.set_visible(False)
        box = self.axes.get_position()
        self.axes.set_position([box.x0, box.y0, box.width * 0.8, box.height])
        self._legend_size = None
        self.legend()
        self.draw()
        self._accumulation_mode = "Off"
        self.display_matrix = np.full(fill_value=False, shape=self.display_data.shape[1:])
        self.figure.canvas.mpl_connect('button_press_event', self.on_button_press_event)
        self.figure.canvas.mpl_connect('motion_notify_event', self.on_hover_event)
        self.figure.canvas.mpl_connect('figure_leave_event', self.on_mouse_leave)
        self.figure.canvas.mpl_connect('pick_event', self.onpick)

        self.__right_hold = False
        self.__start_x = 0
        self.__end_x = 0
        self._legend = None

        self.axis_x_data = x_plot
        lowx = np.min(x_plot)
        lowy = np.min(display_data)
        highy =np.max(display_data)
        self.__start_line = self.axes.vlines(lowx, lowy, highy, colors=["black"])
        self.__start_line.set_visible(False)
        self.__end_line = self.axes.vlines(lowx, lowy, highy, colors=["black"])
        self.__end_line.set_visible(False)
        self.__arrow = self.axes.arrow(lowx,lowy,0,0)
        self.__arrow.set_visible(False)
        self.__display_dt_annotation = self.axes.annotate("0", (0,0), xytext=(10,10),
                                                          xycoords="axes pixels",textcoords="offset pixels")

        self.altlegend = AltLegendView(self, conf)
        self.tight_layout()

    def set_font_size(self, size):
        self.axes.tick_params(axis='both', which='major', labelsize=size)
        xlabel = self.axes.get_xlabel()
        self.axes.set_xlabel(xlabel, fontsize=size)
        ylabel = self.axes.get_ylabel()
        self.axes.set_ylabel(ylabel, fontsize=size)
        self._legend_size = size
        self.legend()

    def onpick(self, event):

        label = event.artist.get_label()
        if label and self._legend:
            self._legend
            print(label)
            print(event.artist.get_color())
            print(event.artist.get_linestyle())
            StyleDialog(self, event.artist, self.axes)
            self.legend()
        self.draw()

    def legend(self):
        MPL_LOGGER.setLevel(logging.ERROR)
        if self._legend_size is None:
            legend = self.axes.legend(**LEGEND_PARAMS)
        else:
            legend = self.axes.legend(prop={'size': self._legend_size}, **LEGEND_PARAMS)
        self._legend = legend


        MPL_LOGGER.setLevel(logging.WARNING)
        if legend.legend_handles:
            for obj in legend.legend_handles:
                obj.set_picker(5)
        else:
            legend.remove()
            self._legend = None


    def tight_layout(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.figure.tight_layout()
        self.altlegend.update_view()
        self.draw()

    def set_visibility(self, matrix, show_pixels=True, adapt=True):
        for i in range(self.display_data.shape[1]):
            for j in range(self.display_data.shape[2]):
                self.lines[i][j].set_visible(matrix[i, j] and show_pixels)
                # if matrix[i,j]:
                #     self.lines[i][j].set_label(f"[{i + 1}, {j + 1}]")
                # else:
                #     self.lines[i][j].set_label("_hidden")
        self.altlegend.set_alive(matrix, adapt=adapt)
        self.legend()
        self.tight_layout()
        self.display_matrix = matrix
        self.draw()

    def set_accumulation_visibility(self, visible):
        self.accumulated.set_visible(visible)
        if visible:
            self.accumulated.set_label("Σ")
        else:
            self.accumulated.set_label("_hidden")
        self.draw()

    def on_button_press_event(self, event):
        x_is_dt = isinstance(self.axis_x_data[0],datetime.datetime)
        if event.button == 3 and (event.xdata is not None) and (self.allow_callbacks() and not x_is_dt):
            self.__right_hold = True
            print("START")
            self.__start_x = event.xdata
            ymin, ymax = self.axes.get_ylim()
            set_vlines_position_ylims(self.__start_line, self.__start_x, ymin, ymax)
            self.axes.set_autoscaley_on(False)

            self.__show_field(self.__start_line)
            self.__show_field(self.__end_line)
            self.__show_field(self.__arrow)
            self.__show_field(self.__display_dt_annotation)
            self.track_position(event)
        if not self.allow_callbacks() or event.button == 1 or x_is_dt:
            self.__hide_field(self.__start_line)
            self.__hide_field(self.__end_line)
            self.__hide_field(self.__arrow)
            self.__hide_field(self.__display_dt_annotation)



    def on_hover_event(self, event):
        if event.button == 3 and self.__right_hold:
            self.track_position(event)
        else:
            self.stop_measuring()

    def on_mouse_leave(self, event):
        self.stop_measuring()


    def __hide_field(self, field):
        # if not hasattr(self, field_name):
        #     setattr(self, field_name, None)
        field.set_visible(False)

    def __show_field(self, field):
        # if not hasattr(self, field_name):
        #     setattr(self, field_name, None)
        field.set_visible(True)

    def stop_measuring(self):
        self.__right_hold = False

        self.axes.set_autoscaley_on(True)
        self.draw()


    def track_position(self,event):
        if (event.xdata is not None):
            self.__end_x = event.xdata
            ymin, ymax = self.axes.get_ylim()
            middle_y = (ymin+ymax)/2
            set_vlines_position_ylims(self.__end_line, self.__end_x, ymin, ymax)

            self.__arrow.set_data(x=self.__start_x,
                                               y=middle_y,
                                               dx=(self.__end_x - self.__start_x),
                                               dy=0)

            dx = abs(self.__start_x - self.__end_x)
            txt = "{:.4f}".format(dx)
            i1 = binsearch_tgt(self.axis_x_data, self.__start_x)
            i2 = binsearch_tgt(self.axis_x_data, self.__end_x)
            if i1 > i2:
                i1, i2 = i2 , i1
            middle_x = (self.__start_x + self.__end_x)/2
            #self.__display_dt_annotation.set_position((middle_x, middle_y))
            if 0 <= i2 < self.display_data.shape[0]:
                frag = self.display_data[i1:i2, self.display_matrix]
                if frag.size > 0:
                    txt = txt + "\n"
                    mean = np.mean(frag)
                    std = np.std(frag)
                    txt += f"mean={SCALE_FLOATING_POINT_FORMAT.format(mean)}\n"
                    txt += f"std={SCALE_FLOATING_POINT_FORMAT.format(std)}"
            self.__display_dt_annotation.set_text(txt)

        self.draw()


    def update_accumulation_selected(self, checkmode=None):
        if checkmode is None:
            checkmode = self._accumulation_mode
        if checkmode == "Selected":
            srcdata = self.display_data[:, self.display_matrix]
            if self._suppress_negative:
                srcdata = np.where(srcdata > 0, srcdata, 0.0)
            func = self.get_lightcurve_func()
            base_lc = func(srcdata, axis=1)
            if self._use_offset:
                base_lc = base_lc - np.median(base_lc)
            diffused = moving_average(base_lc,self.flatten_ma)
            self.accumulated.set_ydata(diffused)

        self.draw()

    def get_lightcurve_func(self):
        if self.use_mean:
            return np.mean
        else:
            return np.sum

    def switch_accumulation_mode(self, new_mode, use_offset=False, suppress_negative = False):
        if self._accumulation_mode != new_mode:
            self.set_accumulation_visibility(new_mode != "Off")
            if new_mode == "All":
                func = self.get_lightcurve_func()
                if suppress_negative:
                    used_data = np.where(self.display_data>0,self.display_data, 0.0)
                else:
                    used_data = self.display_data
                full_sum = func(used_data, axis=(1, 2))
                if use_offset:
                    full_sum -= np.median(full_sum)
                full_sum = moving_average(full_sum, self.flatten_ma)
                self.accumulated.set_ydata(full_sum)
            self.update_accumulation_selected(new_mode)
        self._accumulation_mode = new_mode
        self._use_offset = use_offset
        self._suppress_negative = suppress_negative
