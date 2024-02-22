import datetime
import zipfile
import json
import pickle
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

import h5py
import numpy as np

from ..base import Tool
from padamo.ui_elements.configurable_gridplotter import ConfigurableGridPlotter
from padamo.ui_elements.signal_plotter import PopupPlotable
from padamo.ui_elements.tk_forms import TkDictForm
from padamo.ui_elements.button_panel import ButtonPanel
from .form import TriggerForm
from .storage import IntervalStorage, Interval
from .get_subinterval import IntervalAsker
from .triggering_parallel import ParallelTriggerHandle
from .tracks_storage import DisplayStorage
from padamo.utilities.workspace import Workspace
from padamo.ui_elements.searching import comparing_binsearch as comparing_binsearch_temporal

from .data_exporter import TriggerExporterHandle

TRIGGER_INTERVALS_WORKSPACE = Workspace("marked_up_tracks")
TRACKS_WORKSPACE = Workspace("tracks")

class Indicator(tk.Frame):
    def __init__(self,master):
        super().__init__(master)
        self._max_value = 100
        self._value = None
        self._prog_visible = False
        self.labelvar = tk.StringVar()
        label = tk.Label(self, textvariable=self.labelvar)
        label.grid(row=0, column=0, sticky="nsew")
        self.progress = ttk.Progressbar(self,maximum=self._max_value,orient="horizontal")
        self.columnconfigure(0,weight=1)
        self._redraw()

    def _set_prog_visibility(self,new):
        if new and not self._prog_visible:
            self.progress.grid(row=1, column=0, sticky="nsew")
            self._prog_visible = True
        elif not new and self._prog_visible:
            self.progress.grid_forget()
            self._prog_visible = False

    def _redraw(self):
        if self._value is None:
            self.labelvar.set("---")
            self._set_prog_visibility(False)
        else:
            self._set_prog_visibility(True)
            self.labelvar.set(f"{self._value}/{self._max_value}")
            self.progress["value"] = self._value

    def set_value(self, v):
        self._value = v
        self._redraw()

    def set_max(self, v):
        self._max_value = v
        self.progress['maximum'] = v
        if self._value is not None:
            self._value = min(self._value, v)
        self._redraw()


class Trigger(Tool, PopupPlotable):
    TAB_LABEL = "Trigger"

    def __init__(self, master, globals_):
        Tool.__init__(self, master, globals_)
        self.chosen_detector = None
        self.signal = None
        self._formdata = None
        self._source_storage = None
        self._event_storage = None
        self._bg_storage = None
        self._worker = None
        self._plot_data = None
        self.last_select = None
        self._exporter = TriggerExporterHandle(self)

        self.form_parser = TriggerForm()

        lpanel = tk.Frame(self)
        lpanel.pack(side="left", fill="y")
        self._event_storage_display = DisplayStorage(lpanel, "Triggered intervals")
        self._bg_storage_display = DisplayStorage(lpanel, "Rejected intervals")

        self._event_storage_display.pack(side="top",fill="both",expand=True)
        self._bg_storage_display.pack(side="bottom",fill="both",expand=True)
        self._event_storage_display.select_callback = self.on_event_select
        self._bg_storage_display.select_callback = self.on_bg_select

        self.plotter = ConfigurableGridPlotter(self)
        self.plotter.pack(side="left",fill="both", expand=True)

        PopupPlotable.__init__(self, self.plotter)

        rpanel = tk.Frame(self)
        rpanel.pack(side="right", fill="y")
        self.indicator = Indicator(rpanel)
        self.indicator.pack(side="top", fill="x")

        button_panel = ButtonPanel(rpanel)
        button_panel.add_button("Start trigger", self.on_trigger_start)
        button_panel.add_button("Stop trigger", self.on_trigger_stop)
        button_panel.advance()
        button_panel.add_button("Clear", self.on_clear)
        button_panel.add_button("Remove", self.on_remove)
        button_panel.advance()
        button_panel.add_button("Export", self.on_export)
        button_panel.pack(side="top", fill="x")

        self.form = TkDictForm(rpanel, self.form_parser.get_configuration_root())
        self.form.pack(fill="both", expand=True)
        self.form.on_commit = self.on_form_commit

        self.on_globals_update()
        self.on_form_commit()
        self.after(10,self.monitor)
        self.add_objection_hook("run",self.not_saved_objection)

    def not_saved_objection(self):
        if self._event_storage is None:
            return False   # No storage - no objections
        if self._event_storage.is_empty():
            return False   # No results to lose - no objections
        if messagebox.askokcancel(title="Rerunning", message="Trigger results are not saved. Rerunning graph will clear them. Continue?"):
            return False   # User agreed to discard results - no objections
        return True        # OBJECTION!


    def on_export(self):

        if not self._event_storage or not self.signal:
            return
        filename = TRACKS_WORKSPACE.asksaveasfilename(defaultextension="*.zip",
                                                                 filetypes=[("Data export", "*.zip")])
        if not filename:
            return
        signal_serialized = pickle.dumps(self.signal)
        self._exporter.start(filename=filename,
                             signal_serialized=signal_serialized,
                             intervals=self._event_storage.get_available())



    def monitor(self):
        if self._source_storage is not None and self._event_storage is not None:
            if self._worker is not None:
                self._worker:ParallelTriggerHandle
                self._source_storage: IntervalStorage
                self._end_storage: IntervalStorage
                self._pull_data()
                if not self._worker.is_alive():
                    print("Worker stopped")
                    self.on_trigger_stop()
        self.after(100, self.monitor)

    def _pull_data(self):
        if self._worker is None or self._worker.is_stopped():
            return
        stati = self._worker.poll_stati()
        for status in stati:
            #print("Pull", status)
            if len(status) == 3:
                start, end, positive = status
                interval = Interval(start, end)
                if positive:
                    antifp = self._formdata["anti_fp_cutter"]
                    if antifp is None:
                        allow = True
                    else:
                        event = self.signal.space.request_data(interval.to_slice())
                        allow = antifp(event)
                    if allow:
                        self._source_storage.try_move_to(self._event_storage, interval)
                    else:
                        self._source_storage.try_move_to(self._bg_storage, interval)
                else:
                    self._source_storage.try_move_to(self._bg_storage, interval)
            else:
                self.indicator.set_value(status[0])

    def on_clear(self):
        if messagebox.askokcancel(title="Clear", message="Are you sure?"):
            self.reset_storages()

    def on_remove(self):
        if self.last_select is not None:
            s = self.last_select.get_selected()
            if s is not None:
                interval = self.last_select.storage.get_available()[s]
                self.last_select.storage.try_move_to(self._source_storage, interval)


    def on_bg_select(self,i):
        self.last_select = self._bg_storage_display

    def on_event_select(self, index):
        self.last_select = self._event_storage_display
        self._event_storage:IntervalStorage
        interval = self._event_storage.get_available()[index]
        data = self.signal.space.request_data(interval.to_slice())
        temp_data = np.arange(interval.length())
        view = np.max(data[:], axis=0)
        print(interval)
        if self.plotter.is_compatible(view.shape):
            self._plot_data = temp_data,data
            self.plotter.buffer_matrix = view
            self.plotter.update_matrix_plot(True)
            self.plotter.draw()

    def on_form_commit(self):
        raw_formdata = self.form.get_values()
        self.form_parser.parse_formdata(raw_formdata)
        self._formdata = self.form_parser.get_data()

    def on_trigger_start(self):
        if self._worker is not None:
            return
        if self.signal is None:
            messagebox.showerror(title="Trigger", message="No signal")
            return

        if self.signal.trigger is None:
            messagebox.showerror(title="Trigger", message="No trigger attached to signal")
            return

        interval_asked = IntervalAsker(self,self._source_storage)
        if interval_asked.result is not None:
            print(interval_asked.result)
            interval_asked = interval_asked.result
            self._source_storage:IntervalStorage
            if self._source_storage.get_available_index_to_take(interval_asked) is None:
                messagebox.showerror(title="Start trigger", message=f"Cannot use {repr(interval_asked)} since it contains used intervals")
                return

            self.on_trigger_stop()
            self.indicator.set_max(interval_asked.end-interval_asked.start)
            self._worker = ParallelTriggerHandle(pickle.dumps(self.signal), interval_asked, self._formdata["chunk_size"])
            self._worker.start()

    def on_trigger_stop(self):
        print("Stopping and cleaning up")
        self._pull_data()
        if self._worker is not None:
            self._worker.stop()
            self._worker = None
            self.indicator.set_value(None)

    def reset_storages(self):
        if self.signal is not None:
            length = self.signal.length()
            self._source_storage = IntervalStorage(0, length, empty=False)
            self._event_storage = IntervalStorage(0, length, empty=True)
            self._bg_storage = IntervalStorage(0, length, empty=True)
            self._event_storage_display.set_storage(self._event_storage)
            self._bg_storage_display.set_storage(self._bg_storage)

    def on_globals_update(self):
        if self.chosen_detector != self.globals["chosen_detector_config"]:
            self.chosen_detector = self.globals["chosen_detector_config"]
            self.plotter.configure_detector(self.chosen_detector)
            self.plotter.draw()
        if self.globals["current_view"] is not self.signal:
            self.signal = self.globals["current_view"]
            self.reset_storages()

    def get_plot_data(self):
        return self._plot_data

    def serialize_interval(self,x: Interval):
        start,end = x.start, x.end
        ut_start = self.signal.time.request_data(start)
        ut_end = self.signal.time.request_data(end-1)
        return float(ut_start),float(ut_end)

    def deserialize_interval(self,ut1,ut2):
        time_active = self.signal.time.activate()
        i1 = comparing_binsearch_temporal(time_active,ut1)
        i2 = comparing_binsearch_temporal(time_active,ut2)+1
        i1 = max(i1,0)
        i2 = min(i2, time_active.shape[0])
        return Interval(i1,i2)

    def on_save(self):
        if self._event_storage is None:
            return
        filename = TRIGGER_INTERVALS_WORKSPACE.asksaveasfilename(defaultextension="*.h5", filetypes=[("Triggered intervals","*.json")])
        if filename and (self._event_storage is not None):
            self._event_storage: IntervalStorage
            intervals = self._event_storage.get_available()
            data = {
                "outer": self._event_storage.outer.serialize(),
                "events": [self.serialize_interval(x) for x in intervals],
                "empty": [self.serialize_interval(x) for x in self._bg_storage.get_available()]
            }
            with open(filename,"w") as fp:
                json.dump(data, fp)

    def on_load(self):
        if self._event_storage is None:
            return
        filename = TRIGGER_INTERVALS_WORKSPACE.askopenfilename(defaultextension="*.h5",
                                                                 filetypes=[("Triggered intervals", "*.json")])
        if filename:
            with open(filename,"r") as fp:
                data = json.load(fp)

            if isinstance(data["events"][0][0],int):
                outer = Interval.deserialize(data["outer"])
                if not outer.is_same_as(self._event_storage.outer):
                    if not messagebox.askokcancel(title="Loading intervals", message="Intervals lengths mismatch. Continue?"):
                        return
                self.reset_storages()
                for start,end in data["events"]:
                    self._source_storage.try_move_to(self._event_storage, Interval(start, end))
                for start,end in data["empty"]:
                    self._source_storage.try_move_to(self._bg_storage, Interval(start,end))
            else:
                for ev in data["events"]:
                    interval = self.deserialize_interval(*ev)
                    self._source_storage.try_move_to(self._event_storage, interval)
                for ev in data["empty"]:
                    interval = self.deserialize_interval(*ev)
                    self._source_storage.try_move_to(self._bg_storage, interval)
