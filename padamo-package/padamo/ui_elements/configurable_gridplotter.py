import tkinter as tk
import typing

import PIL.Image
import matplotlib
from matplotlib import pyplot as plt
from matplotlib.pyplot import Normalize
import numpy as np

from .configurable_gridview import ConfigurableGridView, DeviceParameters,CellLayer
from .plotter import Plotter


SCALE_FLOATING_POINT_FORMAT = "{:.2f}"
PLOT_COLORMAP = matplotlib.colormaps["viridis"]
PLOT_HIGHLIGHT_COLOR = "red"
PLOT_BROKEN_COLOR = "black"


class ConfigurableGridAxes(ConfigurableGridView):
    def __init__(self, figure, axes, norm=None, bright=False):
        super().__init__(axes)
        self._conf_grid_figure = figure
        self.bright = bright
        self.colorbar = None
        self.norm = norm
        self.alive_pixels_matrix = None
        self.buffer_matrix = None
        self.highlight_pixels_matrix = None

    def copy_conf_to(self,other):
        other.configure_detector(self._configuration)
        other.alive_pixels_matrix = self.alive_pixels_matrix[:,:]
        other.update_matrix_plot(True)

    def configure_detector(self, configuration: DeviceParameters):
        super().configure_detector(configuration)
        W,H = self.full_shape
        self.buffer_matrix = np.zeros((W,H))
        self.alive_pixels_matrix = np.ones([W,H]).astype(bool)
        self.highlight_pixels_matrix = np.zeros([W,H]).astype(bool)
        self.update_matrix_plot(True)
        #self.draw()

    def update_norm_modulate(self,low_fallback,high_fallback) -> typing.Tuple[float,float]:
        raise NotImplementedError

    def get_bounds(self, low_fallback=None, high_fallback=None):
        if low_fallback is None:
            if self.norm is None:
                return
            low_fallback = self.norm.vmin

        if high_fallback is None:
            if self.norm is None:
                return
            high_fallback = self.norm.vmax
        if low_fallback >= high_fallback:
            if self.bright:
                high_fallback = low_fallback - 1e-6
            else:
                high_fallback = low_fallback + 1e-6

        return self.update_norm_modulate(low_fallback,high_fallback)

    def update_norm(self, low_fallback=None, high_fallback=None):
        if self.alive_pixels_matrix is None:
            return

        low,high = self.get_bounds(low_fallback,high_fallback)

        if self.norm is None:
            self.norm = Normalize(low, high)
        else:
            # Magic: pyplot requires to assign twice
            self.norm.vmin = low
            self.norm.vmin = low
            self.norm.vmax = high
            self.norm.vmax = high

    def correct_colorbar(self,norm):
        if self.colorbar is None:
            self.colorbar = self._conf_grid_figure.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=PLOT_COLORMAP),
                                                            ax=self._conf_grid_axes)
        else:
            self.colorbar.update_normal(plt.cm.ScalarMappable(norm=norm, cmap=PLOT_COLORMAP))


    def update_matrix_plot(self, update_norm=False):
        if self.alive_pixels_matrix is None:
            return
        if update_norm or (self.norm is None):
            alive_data = self.buffer_matrix[self.alive_pixels_matrix]
            if len(alive_data) > 0:
                low_auto = np.min(alive_data)
                high_auto = np.max(alive_data)
            else:
                low_auto = -1
                high_auto = 0

            self.update_norm(low_auto, high_auto)
            self.correct_colorbar(self.norm)
            # if self.colorbar is None:
            #     self.colorbar = self._conf_grid_figure.colorbar(plt.cm.ScalarMappable(norm=self.norm, cmap=PLOT_COLORMAP),
            #                                          ax=self._conf_grid_axes)
            # else:
            #     self.colorbar.update_normal(self.norm)
        # print("Normalized:", time.time()-start_time)
        if self.norm is not None:
            W, H = self.full_shape
            # print("WH",W,H)
            for j in range(H):
                for i in range(W):
                    if self.highlight_pixels_matrix[i, j]:
                        self.set_pixel_color(j, i, PLOT_HIGHLIGHT_COLOR)
                    elif self.alive_pixels_matrix[i, j]:
                        self.set_pixel_color(j, i, PLOT_COLORMAP(self.norm(self.buffer_matrix[i, j])))
                    else:
                        self.set_pixel_color(j, i, PLOT_BROKEN_COLOR)

    def set_broken(self, broken):
        if self.alive_pixels_matrix is None:
            return
        W, H = self.full_shape
        self.alive_pixels_matrix = np.ones([W, H]).astype(bool)
        for i, j in broken:
            self.alive_pixels_matrix[i, j] = False

    def toggle_broken(self, i, j):
        if self.alive_pixels_matrix is None:
            return
        self.alive_pixels_matrix[i, j] = not self.alive_pixels_matrix[i, j]
        self._last_alive = self.alive_pixels_matrix[i, j]

    def mark_broken(self, i, j):
        if self.alive_pixels_matrix is None:
            return
        self.alive_pixels_matrix[i, j] = False

    def clear_highlight(self):
        if self.alive_pixels_matrix is None:
            return
        W, H = self.full_shape
        self.highlight_pixels_matrix = np.zeros([W, H]).astype(bool)

    def highlight_pixel(self, i, j):
        if self.alive_pixels_matrix is None:
            return
        self.highlight_pixels_matrix[i, j] = True

    def highlighted_pixels_query(self):
        if self.alive_pixels_matrix is None:
            raise RuntimeError("Plotter is not initialized")
        return np.array(np.where(self.highlight_pixels_matrix)).T

    def get_frame(self):
        if self.alive_pixels_matrix is None:
            raise RuntimeError("Plotter is not initialized")
        return PIL.Image.frombytes('RGB',
                                   self._conf_grid_figure.canvas.get_width_height(),
                                   self._conf_grid_figure.canvas.tostring_rgb())

    def get_detector_name(self):
        if self._configuration is None:
            return "<Unknown>"
        else:
            return self._configuration.name

class ConfigurableGridPlotter(Plotter, ConfigurableGridAxes):
    def __init__(self, master, norm=None, enable_scale_configuration=True, bright=False, *args, **kwargs):
        Plotter.__init__(self,master, *args, **kwargs)
        ConfigurableGridAxes.__init__(self, self.figure, self.axes, bright=bright, norm=norm)
        self.use_autoscale_var = tk.IntVar(self)
        self.use_autoscale_var.set(1)
        self.use_autoscale_var.trace("w", self.on_scale_change_commit)

        self.min_norm_entry = tk.StringVar(self)
        self.max_norm_entry = tk.StringVar(self)

        self.on_left_click_callback = None
        self.on_right_click_callback = None
        self.on_right_click_callback_outofbounds = None

        self.enable_scale_configuration = enable_scale_configuration
        self.use_autoscale_var = tk.IntVar(self)
        self.use_autoscale_var.set(1)
        self.use_autoscale_var.trace("w", self.on_scale_change_commit)

        self.min_norm_entry = tk.StringVar(self)
        self.max_norm_entry = tk.StringVar(self)

        self.enable_scale_configuration = enable_scale_configuration
        self.on_left_click_callback = None
        self.on_right_click_callback = None
        self.on_right_click_callback_outofbounds = None

        self.figure.canvas.mpl_connect("button_press_event", self.on_plot_click)
        self.figure.canvas.mpl_connect("motion_notify_event", self.on_hover)
        self.figure.canvas.mpl_connect("axes_leave_event", self.on_leave)

        tk_control_panel = tk.Frame(self)
        tk_control_panel.pack(side=tk.BOTTOM, fill=tk.X)
        for i in range(4):
            tk_control_panel.columnconfigure(i, weight=1)
        if enable_scale_configuration:
            autoscale_check = tk.Checkbutton(tk_control_panel, text="Autoscale",
                                             variable=self.use_autoscale_var)
            autoscale_check.grid(row=0, column=0, columnspan=4, sticky="w")
            tk.Label(tk_control_panel, text="Scale").grid(row=0, column=1, sticky="ew")
            tk.Label(tk_control_panel, text="-").grid(row=0, column=3, sticky="ew")
            from padamo.ui_elements.modified_base import EntryWithEnterKey
            min_ = EntryWithEnterKey(tk_control_panel, textvariable=self.min_norm_entry)
            min_.grid(row=0, column=2, sticky="ew")
            min_.on_commit = self.on_scale_change_commit
            max_ = EntryWithEnterKey(tk_control_panel, textvariable=self.max_norm_entry)
            max_.grid(row=0, column=4, sticky="ew")
            max_.on_commit = self.on_scale_change_commit
            tk.Button(tk_control_panel, text="C", command=self.clear_broken).grid(row=0, column=5, sticky="e")

        self.annotation = self.axes.annotate("", xy=(0, 0), xytext=(-25, 20), textcoords="offset points",
                            bbox=dict(boxstyle="round", fc="w"),
                            arrowprops=dict(arrowstyle="->"))
        self.annotation.set_visible(False)
        self._last_alive = None

    @staticmethod
    def require_initialized(func):
        def inner(self,*args,**kwargs):
            if self.alive_pixels_matrix is None:
                return
            return func(self,*args,**kwargs)
        return inner

    @require_initialized
    def on_scale_change_commit(self, *args):
        self.update_matrix_plot(True)
        self.draw()

    @require_initialized
    def get_broken(self):
        return np.logical_not(self.alive_pixels_matrix)

    @require_initialized
    def clear_broken(self):
        self.alive_pixels_matrix = np.ones(self.alive_pixels_matrix.shape).astype(bool)
        self.update_matrix_plot(True)
        self.draw()

    def autoscale(self):
        return not self.enable_scale_configuration or self.use_autoscale_var.get()

    def update_norm_modulate(self,low_fallback,high_fallback) -> typing.Tuple[float,float]:
        if self.autoscale():
            low = low_fallback
            high = high_fallback
            self.max_norm_entry.set(SCALE_FLOATING_POINT_FORMAT.format(high_fallback))
            self.min_norm_entry.set(SCALE_FLOATING_POINT_FORMAT.format(low_fallback))
        else:
            try:
                low = float(self.min_norm_entry.get())
            except ValueError:
                self.min_norm_entry.set(SCALE_FLOATING_POINT_FORMAT.format(low_fallback))
                low = low_fallback
            try:
                high = float(self.max_norm_entry.get())
            except ValueError:
                self.max_norm_entry.set(SCALE_FLOATING_POINT_FORMAT.format(high_fallback))
                high = high_fallback

        if low > high:
            low, high = high, low

        return low,high

    @require_initialized
    def on_plot_click(self, event):
        if self.alive_pixels_matrix is None:
            return
        if (event.xdata is not None) and (event.ydata is not None) and self.allow_callbacks():
            i = self.find_index_from_coord(0, event.xdata)
            j = self.find_index_from_coord(1, event.ydata)
            if i >= 0 and j >= 0:
                if event.button == 1:  #LMB
                    self.toggle_broken(i, j)
                    self.update_matrix_plot(True)
                    self.draw()
                    if self.on_left_click_callback:
                        self.on_left_click_callback(i, j)
                elif event.button == 3:  #RMB
                    if self.on_right_click_callback:
                        self.on_right_click_callback(i, j)

                    self.update_matrix_plot(True)
                    self.draw()
                    if self.on_left_click_callback:
                        self.on_left_click_callback(i, j)
            elif event.button == 3:
                if self.on_right_click_callback_outofbounds:
                    self.on_right_click_callback_outofbounds()
            elif event.button == 1:  # LMB OOB
                self._last_alive = None

            if (i<0 or j<0) and event.dblclick:
                self.alive_pixels_matrix = np.logical_not(self.alive_pixels_matrix)
                self.update_matrix_plot(True)
                self.draw()
                if self.on_left_click_callback:
                    self.on_left_click_callback(i, j)

    @require_initialized
    def on_leave(self, event):
        self.annotation.set_visible(False)
        self.figure.canvas.draw_idle()

    @require_initialized
    def on_hover(self, event):
        if event.xdata and event.ydata:
            i = self.find_index_from_coord(0, event.xdata)
            j = self.find_index_from_coord(1, event.ydata)
            if i >= 0 and j >= 0:
                v = self.buffer_matrix[i, j]
                self.annotation.xy = (event.xdata, event.ydata)
                self.annotation.set_visible(True)
                self.annotation.set_text(f"[{i+1}, {j+1}]\n({round(v,2)})")
                #print(f"HOVERING over {i},{j}")

                if event.button == 1 and self._last_alive is not None:
                    if self.alive_pixels_matrix[i,j] != self._last_alive:
                        self.alive_pixels_matrix[i,j] = self._last_alive
                        self.update_matrix_plot(True)
                        if self.on_left_click_callback:
                            self.on_left_click_callback(i, j)
                self.draw()
                return
        self.annotation.set_visible(False)
        self.draw()




class TulomaGridPlotter(ConfigurableGridPlotter):
    def __init__(self, master, norm=None, enable_scale_configuration=True, bright=False, *args, **kwargs):
        super().__init__(master, norm, enable_scale_configuration, bright, *args, **kwargs)
        tuloma_parameters = DeviceParameters(name="VTL", flipped_x=True,
                                             flipped_y=False,
                                             pixel_size=(2.85, 2.85),
                                             pixels_shape=(8, 8),
                                             supercells=[
                                                 CellLayer(layer_name="Detector", gap=(4.0, 4.0), shape=(2, 2), mask=[])
                                             ]
                                            )
        self.configure_detector(tuloma_parameters)