import datetime
import io
import pickle
import os.path
import sys
import tkinter
import traceback
import tkinter as tk
from tkinter import ttk
from tkinter import simpledialog, messagebox

import PIL.Image
import h5py
import numpy as np
import imageio as iio
import tqdm
from multiprocessing import Process, Value, Queue

from padamo.lazy_array_operations.base import slice_t
from padamo.ui_elements.configurable_gridview import DeviceParameters
from padamo.utilities.dual_signal import Signal
from ..base import Tool
from padamo.ui_elements.tk_forms import TkDictForm
from padamo.ui_elements.configurable_gridplotter import ConfigurableGridPlotter
from padamo.ui_elements.player_controls import PlayerControls
from .right_form import ViewerFrame
from padamo.ui_elements.signal_plotter import PopupPlotable
from padamo.ui_elements.button_panel import ButtonPanel

from padamo.lazy_array_operations import LazyArrayOperation
from .controllable_lc_plotter import LCPlotter
from padamo.utilities.workspace import Workspace

from padamo.tools.device_editor.workspace import DEVICE_VTL, DetectorWorkspace
#from .trigger_process import EventFinder
from .trigger_job import EventFinderHandle
from .animation_job import AnimationHandle, DATETIME_FORMAT
from .export_job import ExporterHandle

BUNCH_SIZE = 1000

DATA_WORKSPACE = Workspace("viewed_hdf5_data")
ANIMATIONS_WORKSPACE = Workspace("animations")
DETECTOR_WORKSPACE = DetectorWorkspace("detectors")


def pickled_clone(a):
    s = pickle.dumps(a)
    return s
    #return pickle.loads(s)

class ViewerAlivePixels(LazyArrayOperation):
    def __init__(self, plotter):
        self.plotter = plotter

    def request_data(self, interesting_slices:slice_t):
        return self.plotter.alive_pixels_matrix[interesting_slices]


def insert_number(fn,n):
    filename, ext = os.path.splitext(fn)
    return filename+f"-{n}"+ext


class Viewer(Tool, PopupPlotable):
    TAB_LABEL = "Viewer"

    def __init__(self, master, globals_):
        Tool.__init__(self,master, globals_)
        self.bookmarker = None
        self.globals["current_view"] = None
        topframe = tkinter.Frame(self)
        topframe.pack(side="top", fill="both", expand=True)
        self.plotter = ConfigurableGridPlotter(topframe)
        self.plotter.configure_detector(DEVICE_VTL)
        self.globals["chosen_detector_config"] = DEVICE_VTL

        self.plotter.pack(side="left", fill="both", expand=True)
        self.conf_parser = ViewerFrame()
        rframe = tkinter.Frame(topframe)
        rframe.pack(side="right", fill="y")
        self.conf_form = TkDictForm(rframe, self.conf_parser.get_configuration_root())
        self.conf_form.grid(row=1, column=0, sticky="nsew")
        rframe.rowconfigure(1,weight=1)
        buttonpanel = ButtonPanel(rframe)
        buttonpanel.grid(row=0, column=0, sticky="nsew")

        buttonpanel.add_button("Choose detector", self.on_detector_change)
        buttonpanel.advance()
        buttonpanel.add_button("Create animation",self.on_animation)
        #buttonpanel.advance()
        buttonpanel.add_button("Export data",self.on_export)
        buttonpanel.advance()
        buttonpanel.add_button("Next trigger", self.find_triggered)
        buttonpanel.add_button("Stop", self.on_stop)
        buttonpanel.advance()
        buttonpanel.add_button("Create bookmark", self.on_add_bookmark)
        #buttonpanel.advance()
        buttonpanel.add_button("Copy timespan", self.on_copy_timespan)
        buttonpanel.add_button("Paste timespan", self.on_bookmark_paste)
        buttonpanel.advance()
        self._formdata = None
        self.conf_form.on_commit = self.on_form_commit
        self.globals["loaded_file"] = ""
        self.globals["alive_pixels"] = ViewerAlivePixels(self.plotter)
        self.player_controls = PlayerControls(self, self.on_player_ctrl_frame, self.on_player_ctrl_click)
        self.player_controls.pack(side="bottom", fill="x")
        self.player_controls.playing_position.range_change_callback = self.on_range_changed
        self._known_frames = 100
        self._time = None
        self._start_t = None
        self._end_t = None
        self._finder = EventFinderHandle(self)
        self._animator = AnimationHandle(self)
        self._exporter = ExporterHandle(self)
        self._detector_error = False
        self._finder.set_callback(self.on_event_found)
        PopupPlotable.__init__(self, self.plotter, enable_invalidate=True, max_plots=10)
        self.on_form_commit(False)


    def on_range_changed(self):
        if self._plot_valid:
            print("Range changed. Invalidating plot...")
            self.invalidate_popup_plot()

    def configure_detector(self,conf):
        self.plotter.configure_detector(conf)
        self.globals["alive_pixels"] = ViewerAlivePixels(self.plotter)
        self.globals["chosen_detector_config"] = conf
        self.trigger_globals_update()

    def on_detector_change(self):
        filename = DETECTOR_WORKSPACE.askopenfilename(defaultextension="*.json",
                                                      filetypes=[("Detector configuration", "*.json")])
        if filename:
            with open(filename, "r") as fp:
                conf = DeviceParameters.from_json(fp.read())
            self.configure_detector(conf)
            self._detector_error = False

    def find_triggered(self):
        if self.globals["current_view"] is None:
            return
        view: Signal = self.globals["current_view"]
        if view.trigger is None:
            return
        self._finder.start(trigger=pickled_clone(view.trigger),
                           start_i=self.player_controls.playing_position.get_frame())

    def on_event_found(self,frame):
        self.player_controls.playing_position.set_frame(frame)

    def on_stop(self):
        self._finder.stop()
        self._animator.stop()
        self._exporter.stop()

    def on_copy_timespan(self):
        mark = self.player_controls.create_bookmark()
        if mark:
            stamp = mark.make_timestamp()
            messagebox.showinfo(title="Copy timestamp", message=f"Copied timestamp {stamp}")
            self.clipboard_clear()
            self.clipboard_append(stamp)

    def on_export(self):
        start,end = self.player_controls.get_selected_range()
        stepsize = simpledialog.askinteger("Export", "Export step",initialvalue=1)
        if stepsize and stepsize>0:
            if self.globals["current_view"] is not None:
                view: Signal = self.globals["current_view"]
                filename = DATA_WORKSPACE.asksaveasfilename(defaultextension="*.h5", filetypes=[("HDF5 file", "*.h5"),])
                if filename:
                    kwargs = {
                        "filename": filename,
                        "start":start,
                        "end":end+1,
                        "signal":pickled_clone(view),
                        "stepsize":stepsize
                    }
                    self._exporter.start(**kwargs)

    def on_animation(self):
        if self.globals["current_view"] is None:
            print("No signal to animate")
            return

        view: Signal = self.globals["current_view"]
        if not self.plotter.is_compatible(view.space.shape()[1:]):
            print("Signal is not compatible with chosen detector")
            return


        filename = ANIMATIONS_WORKSPACE.asksaveasfilename(defaultextension="*.gif", filetypes=[("GIF animation","*.gif"),
                                                                                  ("MP4 animation", "*.mp4"),
                                                                                     ("PNG Image", "*.png")])
        if filename:
            animation_params = self._formdata["animation"]
            low, high = self.player_controls.get_selected_range()
            fps: int = animation_params["fps"]
            skip: int = animation_params["skip"]
            insert_lc:bool = animation_params["lc_insert"]
            if fps < 1:
                fps = 1
            if skip < 1:
                skip = 1
            print("ANIMATION RENDER")
            print("-" * 20)
            print(f"FROM {low} to {high}")
            print("-" * 20)
            print(animation_params)
            print("-" * 20)
            kwargs = {
                "filename":filename,
                "signal":pickled_clone(view),
                "parent_plotter":self.plotter,
                "insert_lc":insert_lc,
                "fps":fps,
                "step":skip,
                "low_frame": low,
                "high_frame": high+1,
                "time_format": self._formdata["time_format"],
                "show_time": self._formdata["show_time"],
                "trigger_only": animation_params["trigger_only"],
                "png_dpi": animation_params["png_dpi"]
            }
            self._animator.start(**kwargs)

    def get_view(self):
        if self.globals["current_view"] is not None:
            try:
                a, b = self.player_controls.get_selected_range()
                cur_view = self.globals["current_view"]
                views = cur_view.space.request_data(slice(a, b))
                return views
            except Exception:
                print(traceback.format_exc(), file=sys.stderr)
                return None

    def get_plot_data(self):
        if self.globals["current_view"] is not None:
            if not self.plotter.is_compatible(self.globals["current_view"].space.shape()[1:]):
                return
            try:
                a, b = self.player_controls.get_selected_range()
                cur_view = self.globals["current_view"]
                if b-a>self._formdata["popup_safeguard"]:
                    if not messagebox.askokcancel(title="Popup plot",message="Selected interval is too big. Proceed?"):
                        return
                views = cur_view.space.request_data(slice(a,b))

                xs = self._formdata["time_format"].time_xs(cur_view.time,a,b)
                return xs,views
                # if self._formdata["use_times"]:
                #     times = cur_view.time.request_data(slice(a,b))
                #     times = np.array([self._formdata["time_format_old"](x) for x in times])
                #     return times, views
                # else:
                #     xs = np.arange(a,b)
                #     return xs, views
            except Exception:
                print(traceback.format_exc(), file=sys.stderr)


    def try_connect_time(self):
        if self.globals["current_view"] is not None:
            time_access = self.globals["current_view"].time.activate()
            try:
                time_shape = time_access.shape
                self.player_controls.link_time(time_access)
            except Exception:
                print(traceback.format_exc(), file=sys.stderr)


    def on_load(self):
        filename = DATA_WORKSPACE.askopenfilename(defaultextension="*.h5", filetypes=[("Data source","*.h5"),
                                                                                  ("MATLAB 7.3 data", "*.mat"),
                                                                                      ("Other", "*.*")])
        if filename:
            self.globals["current_frame"] = 0
            self.set_global("loaded_file", filename)
            self.set_title(f"({os.path.basename(filename)})")



    def on_player_ctrl_frame(self, frame):
        #print(self.globals["current_view"])
        if self.globals["current_view"] is not None:
            try:
                cur_view = self.globals["current_view"]
                view = cur_view.space.request_data(frame)
                time_ = cur_view.time.request_data(frame)
                #dt = datetime.datetime.utcfromtimestamp(float(time_))
                if isinstance(view, np.ndarray):
                    if self.plotter.is_compatible(view.shape):
                        self.plotter.buffer_matrix = view[:, :]
                        self.plotter.update_matrix_plot(True)
                        if self._formdata["show_time"]:
                            self.plotter.axes.set_title(self._formdata["time_format"].format_time(frame, float(time_)))
                            #self.plotter.axes.set_title(dt.strftime(DATETIME_FORMAT))
                        else:
                            self.plotter.axes.set_title("")
                        self.plotter.draw()
                    elif not self._detector_error:
                        messagebox.showerror(title="Data shape error", message=f"Data with shape {view.shape} is not compatible with detector {self.plotter.get_detector_name()}")
                        self._detector_error = True
            except Exception:
                print(traceback.format_exc(), file=sys.stderr)

    def on_player_ctrl_click(self):
        pass

    def on_globals_update(self):
        if self.globals["current_view"] is not None:
            #print(self.globals["current_view"])
            try:
                min_frames = self.globals["current_view"].space.shape()[0]
                if min_frames!=self._known_frames:
                    self.player_controls.set_limit(min_frames-1)
                    self._known_frames = min_frames
                self.try_connect_time()
            except ValueError or FileNotFoundError:
                pass
        self.player_controls.draw_frame()
        self.invalidate_popup_plot()
        self._detector_error = False

    def on_form_commit(self, update=True):
        data = self.conf_form.get_values()
        self.conf_parser.parse_formdata(data)
        self._formdata = self.conf_parser.get_data()
        start_time = self._formdata["toi_start"]
        end_time = self._formdata["toi_end"]
        needs_upd = False
        if end_time!=self._end_t:
            self._end_t = end_time
            self.globals["toi_end"] = end_time
            needs_upd = True
        if start_time != self._start_t:
            self._start_t = start_time
            self.globals["toi_start"] = start_time
            needs_upd = True

        if needs_upd and update:
            print("Sensitive change")
            self.trigger_globals_update()

        self.player_controls.draw_frame()

    def on_add_bookmark(self):
        mark = self.player_controls.create_bookmark()
        if mark is not None:
            self.bookmarker.add_mark(mark)
            messagebox.showinfo(title="Add bookmark", message="Added new bookmark")

    def on_bookmark_paste(self):
        ts = self.clipboard_get()
        self.player_controls.set_time_range_bookmark_str(ts)

