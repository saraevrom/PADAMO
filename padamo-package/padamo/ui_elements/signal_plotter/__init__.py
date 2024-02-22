import datetime
import datetime
import json
import tkinter as tk
from tkinter.simpledialog import askinteger
from tkinter import filedialog

import h5py

#from ..configurable_gridplotter import TulomaGridPlotter as GridPlotter
from ..configurable_gridplotter import ConfigurableGridPlotter
import numpy as np
from ..settings_frame import SettingMenu
from .build_settings import build_menu
from ..button_panel import ButtonPanel

from .time_plotter import MainPlotter
from .binsearch import binsearch_tgt

def timestamp():
    now = datetime.datetime.now()
    return now.strftime("%Y%m%d%H%M%S")

class ChoosablePlotter(tk.Toplevel):
    def __init__(self, master, x_plot, display_data, grid_configuration, auxdata=None):
        super().__init__(master)
        if not grid_configuration.is_compatible(display_data.shape[1:]):
            print(display_data.shape[1:])
            print(grid_configuration.full_shape)
            raise IndexError(f"Plotter mismatch. Data: {display_data.shape[1:]}. Config {grid_configuration.full_shape}")
        self._grid_configuration = grid_configuration
        self.aux_data = auxdata
        self.x_data = x_plot
        self.display_data = display_data
        self._close_callback_cp = None
        self.controller = None
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.plotter = MainPlotter(self, x_plot, display_data, grid_configuration)
        self.plotter.pack(side="left", fill="both", expand=True)

        auxpanel = tk.Frame(self)
        auxpanel.pack(side="right", fill="y")
        self.selector = ConfigurableGridPlotter(auxpanel, enable_scale_configuration=False, bright=True)
        self.selector.configure_detector(grid_configuration)

        self.selector.axes.set_title("Pixel map select")
        self.selector.alive_pixels_matrix[:,:] = False
        self.selector.update_matrix_plot()
        self.selector.pack(side="top", anchor="ne",fill="x")
        self.selector.on_left_click_callback = self.on_lmb
        self.selector.draw()
        self.selector.toolbar.pack_forget()
        self.selector.on_right_click_callback_outofbounds = self.on_right_click_callback_oob_inside

        self.settings_menu = SettingMenu(auxpanel, autocommit=True)
        self.settings_menu.commit_action = self.on_settings_commit
        build_menu(self.settings_menu)
        self.settings_dict = dict()

        scale_panel = tk.Frame(auxpanel)

        self.xscale_var = tk.IntVar(self)
        self.xscale_var.set(0)
        self.yscale_var = tk.IntVar(self)
        self.yscale_var.set(0)

        tk.Label(scale_panel, text="X").grid(row=0,column=0)
        tk.Radiobutton(scale_panel,text="lin", variable=self.xscale_var, value=0).grid(row=0,column=1)
        tk.Radiobutton(scale_panel,text="log", variable=self.xscale_var, value=1).grid(row=0,column=2)
        self.xscale_var.trace("w", self.on_xscale_change)

        tk.Label(scale_panel, text="Y").grid(row=1,column=0)
        tk.Radiobutton(scale_panel, text="lin", variable=self.yscale_var, value=0).grid(row=1, column=1)
        tk.Radiobutton(scale_panel, text="log", variable=self.yscale_var, value=1).grid(row=1, column=2)
        self.yscale_var.trace("w", self.on_yscale_change)

        button_panel = ButtonPanel(auxpanel)
        button_panel.add_button("Load", command=self.on_load_settings, row=0)
        button_panel.add_button("Save", command=self.on_save_settings, row=0)
        button_panel.add_button("Detect active", command=self.on_active_select, row=1)
        button_panel.add_button("Export", command=self.on_export, row=2)
        button_panel.add_button("Tune x limits", command=self.on_xlim, row=3)
        button_panel.pack(side="bottom", fill="x")
        #
        # quickactive_btn.pack(side="bottom", fill="x")
        # xlim_btn.pack(side="bottom", fill="x")
        scale_panel.pack(side="bottom",fill="x")
        self.settings_menu.pack(side="bottom",fill="x")

        self.settings_menu.push_settings_dict(self.settings_dict)
        self.bind("<Configure>", self.on_size_changed)
        self.changed_size_flag = False
        self.alive = True
        self.get_axes().set_xlim(min(self.x_data), max(self.x_data))

    def x_is_scalar(self):
        if isinstance(self.x_data, np.ndarray):
            return self.x_data.dtype in [float,int]
        else:
            return type(self.x_data[0]) in [float, int]

    def on_export(self):
        if self.controller is not None:
            self.controller.popup_plot_export(self)

    def on_save_settings(self):
        filename = filedialog.asksaveasfilename(title="Save settings",
                                     filetypes=[("JSON file with settings", "*.json")],
                                     initialdir=".",
                                     parent=self)
        if filename:
            resdict = dict()
            self.settings_menu.push_settings_dict(resdict)
            with open(filename, "w") as fp:
                json.dump(resdict, fp)


    def on_load_settings(self):
        filename = filedialog.askopenfilename(title="Load settings",
                                                filetypes=[("JSON file with settings", "*.json")],
                                                initialdir=".",
                                                parent=self)
        if filename:
            with open(filename, "r") as fp:
                srcdict = json.load(fp)
            self.settings_menu.pull_settings_dict(srcdict)
            self.on_settings_commit()

    def on_size_changed(self, event):
        self.changed_size_flag = True
        self.after(1000, self._on_size_change)


    def _on_size_change(self):
        if self.changed_size_flag:
            self.plotter.tight_layout()
            self.changed_size_flag = False

    def on_xscale_change(self,*args):
        if self.xscale_var.get():
            self.plotter.axes.set_xscale("log")
        else:
            self.plotter.axes.set_xscale("linear")
        self.plotter.draw()

    def on_yscale_change(self,*args):
        if self.yscale_var.get():
            self.plotter.axes.set_yscale("log")
        else:
            self.plotter.axes.set_yscale("linear")
        self.plotter.draw()

    def get_axes(self):
        return self.plotter.axes

    def on_settings_commit(self):
        self.settings_menu.push_settings_dict(self.settings_dict)
        self.plotter.switch_accumulation_mode(self.settings_dict["lightcurve"],
                                              self.settings_dict["lightcurve_median_offset"],
                                              self.settings_dict["lightcurve_suppress_negative"],
                                              )
        self.plotter.use_mean = self.settings_dict["lightcurve_mean"]
        self.plotter.flatten_ma = self.settings_dict["lightcurve_ma"]
        self.on_lmb(-1,-1)
        self.plotter.axes.set_title(self.settings_dict["title"])
        self.plotter.axes.set_xlabel(self.settings_dict["x_label"])
        self.plotter.axes.set_ylabel(self.settings_dict["y_label"])
        self.plotter.set_font_size(self.settings_dict["tick_label_size"])
        self.plotter.tight_layout()
        self.plotter.draw()

    def on_active_select(self):
        self.on_settings_commit()
        dst_matrix = self.selector.alive_pixels_matrix[:]
        if self.settings_dict["threshold_whole"] or not self.x_is_scalar():
            print(self.x_is_scalar(), self.settings_dict["threshold_whole"])
            amplitudes = np.max(self.display_data, axis=0)
            src_matrix = (amplitudes > self.settings_dict["threshold"])
        else:
            frame1 = binsearch_tgt(self.x_data, self.settings_dict["threshold_frame_start"])
            frame2 = binsearch_tgt(self.x_data, self.settings_dict["threshold_frame_end"])

            #print("Analyzing only frame",frame)
            amplitudes = self.display_data[frame1:frame2]
            amplitudes = np.max(amplitudes, axis=0)
            src_matrix = (amplitudes > self.settings_dict["threshold"])
        dst_matrix = np.logical_or(src_matrix, dst_matrix)
        self.selector.alive_pixels_matrix = dst_matrix
        self.selector.update_matrix_plot()
        self.selector.draw()
        self.on_lmb(-1, -1)

    def on_lmb(self, i, j):
        adapt =  not self.settings_dict["display_full_matrix"]
        if self.settings_dict["show_pixels"]:
            self.plotter.set_visibility(self.selector.alive_pixels_matrix, True, adapt=adapt)
        else:
            self.plotter.set_visibility(self.selector.alive_pixels_matrix, False, adapt=adapt)
            self.plotter.display_matrix = self.selector.alive_pixels_matrix  # To accumulate data
            self.plotter.draw()
        self.plotter.update_accumulation_selected()

    def on_right_click_callback(self,i,j):
        self.selector.alive_pixels_matrix[i,j] = True
        self.selector.update_matrix_plot()
        self.selector.draw()
        self.on_lmb(i,j)

    def on_right_click_callback_oob(self):
        self.selector.alive_pixels_matrix[:,:] = True
        self.selector.update_matrix_plot()
        self.selector.draw()
        self.on_lmb(-1, -1)

    def on_right_click_callback_oob_inside(self):
        '''
        QOL improvement: clicking inside grid will reset selection.
        :return:
        '''
        if not self.selector.alive_pixels_matrix.any():
            self.selector.alive_pixels_matrix[:,:] = True
        else:
            self.selector.alive_pixels_matrix[:, :] = False
        self.selector.update_matrix_plot()
        self.selector.draw()
        self.on_lmb(-1, -1)

    def connect_close(self, callback):
        self._close_callback_cp = callback

    def on_closing(self):
        if self._close_callback_cp is not None:
            self._close_callback_cp()
        self.alive = False
        self.destroy()

    def on_xlim(self):
        low_x = askinteger("xlim","low=")
        high_x = askinteger("xlim","high=")
        self.get_axes().set_xlim(low_x,high_x)


class PopupPlotable(tk.Misc):
    def __init__(self, grid_plotter:ConfigurableGridPlotter, enable_invalidate=False, max_plots=1):
        self._active_gridplotter = grid_plotter
        self._plotter_window = None
        self._context_plotter = None
        self._active_gridplotter.on_right_click_callback = self.on_right_click_callback
        self._active_gridplotter.on_right_click_callback_outofbounds = self.on_right_click_callback_oob
        self._plot_valid = False
        self._plot_invalidating_enabled = enable_invalidate
        self._max_plots = max_plots
        self._plots_queue = []

    def invalidate_popup_plot(self):
        self._plot_valid = False

    def get_plot_data(self):
        raise NotImplementedError("Unable to obtain plot data")

    def postprocess_plot(self, axes):
        pass

    def postprocess_auxgrid(self, axes):
        pass

    def postprocess_plot_export(self, h5filename:str, caller_window:ChoosablePlotter):
        pass

    def popup_plot_export(self, caller_window:ChoosablePlotter):
        x_data = caller_window.x_data
        y_data = caller_window.display_data
        selection_data = caller_window.selector.alive_pixels_matrix[:]
        filename = filedialog.asksaveasfilename(parent=caller_window, initialfile=f"PLOT{timestamp()}.h5",filetypes=
                                                [("HDF5 file", "*.h5")])
        if filename:
            with h5py.File(filename, "w") as fp:
                fp.create_dataset("x_data", data=x_data)
                fp.create_dataset("y_data", data=y_data)
                fp.create_dataset("selection", data=selection_data)
            self.postprocess_plot_export(filename, caller_window)

    def on_left_click(self, i, j):
        if self.ensure_plotter():
            self._plotter_window.on_lmb(i, j)

    def on_right_click_callback(self,i,j):
        if self.ensure_plotter():
            self._plotter_window.on_right_click_callback(i,j)

    def on_right_click_callback_oob(self):
        if self.ensure_plotter():
            self._plotter_window.on_right_click_callback_oob()

    def ensure_plotter(self):
        self.decimate_plot_windows()
        if not self._plots_queue:
            self.invalidate_popup_plot()
        if (self._plotter_window is None) or (not self._plot_valid and self._plot_invalidating_enabled):
            self.create_plotter()

        return self._plotter_window is not None

    def _on_popup_close(self):
        self._plotter_window = None
        self.decimate_plot_windows()

    def set_max_windows(self, newmax):
        self._max_plots = newmax
        self.decimate_plot_windows()

    def decimate_plot_windows(self):
        i = 0
        while i<len(self._plots_queue):
            if self._plots_queue[i].alive:
                i += 1
            else:
                self._plots_queue.pop(i)
        # Control amount of plots
        while len(self._plots_queue)>self._max_plots:
            win = self._plots_queue.pop(0)
            if win.alive:
                win.destroy()

    def plot_add_attribute(self, key, obj):
        if self._context_plotter is not None:
            setattr(self._context_plotter, key, obj)

    def create_plotter(self):
        draw_data = self.get_plot_data()
        if draw_data is not None:
            if len(draw_data)==2:
                x_data, display_data = draw_data
                auxdata = None
            elif len(draw_data)==3:
                x_data, display_data, auxdata = draw_data
            else:
                raise RuntimeError(f"Unknown result type {draw_data}")
            conf = self._active_gridplotter.get_configuration()
            self._plotter_window = ChoosablePlotter(self, x_data, display_data, conf, auxdata=auxdata)
            self._context_plotter = self._plotter_window
            self._plotter_window.controller = self
            self.postprocess_plot(self._plotter_window.get_axes())
            self.postprocess_auxgrid(self._plotter_window.plotter.altlegend.subaxes)
            self._plotter_window.plotter.legend()
            self._plotter_window.connect_close(self._on_popup_close)
            self._plots_queue.append(self._plotter_window)
            self.decimate_plot_windows()
            if self._plot_invalidating_enabled:
                self._plot_valid = True
            self._context_plotter = None
