from .plotter import Plotter
from .datetime_parser import parse_datetimes
import tkinter as tk
from .modified_base import EntryWithEnterKey
from datetime import datetime
from tkinter.simpledialog import askstring
from matplotlib.patches import Rectangle
from .utilities import set_vlines_position
from .searching import comparing_binsearch

MARK_LOW = 0
MARK_HIGH = 1
MARK_PTR = 2

class ValueWrapper(tk.Frame):
    def __init__(self, master, validator, mark, color=None):
        super().__init__(master)
        self.mark = mark
        self.display_value = tk.StringVar(self)
        self.display_value.set("0")
        self.actual_value = 0
        self.utc_explorer = None
        self.entry = EntryWithEnterKey(self, textvariable=self.display_value, justify=tk.CENTER)
        self.entry.on_commit = self.on_entry_commit
        self.entry.grid(row=0, column=0, sticky="nsew")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        btn = tk.Button(self, text="Datetime entry", command=self.on_datetime_entry)
        btn.grid(row=1, column=0, sticky="nsew")
        if color is not None:
            self.entry.configure(fg=color)
            btn.configure(fg=color)
        self.rowconfigure(1, weight=1)
        self.validator = validator

    def on_entry_commit(self):
        v = self.display_value.get()
        try:
            self.set_value(int(v)) # For convenience
        except ValueError:
            self.display_value.set(str(self.actual_value))

    def on_datetime_entry(self):
        if self.utc_explorer is not None:
            ans = askstring(title="Datetime entry",
                           prompt="Enter datetime")
            self.align_datetime_str(ans)

    def align_datetime_str(self,ans):
        if ans:
            print(self.utc_explorer, self.get_value())
            starttime = float(self.utc_explorer[self.get_value()])
            print(starttime)
            start_dt = datetime.utcfromtimestamp(starttime)
            ut0 = parse_datetimes(ans, start_dt)

            frame = comparing_binsearch(self.utc_explorer, ut0)

            print("INTERVAL OK")
            self.set_value(frame)

    def link_time(self, utc_explore):
        self.utc_explorer = utc_explore

    def set_value(self, v, validate=True):
        self.actual_value = v
        self.display_value.set(str(v))
        if self.validator and validate:
            self.validator(self.mark)

    def get_value(self):
        return self.actual_value

    def clamp(self, low, high):
        '''
        clamps stored value between two values (inclusive)
        :param low: Lowest value
        :param high: Highest value
        :return: Has value changed
        '''
        v = self.get_value()
        if v < low:
            self.set_value(low, validate=False)
            return True
        if v > high:
            self.set_value(high, validate=False)
            return True
        return False

    def clamp_lower(self, reference):
        '''
        sets own value lower or equal to value of reference
        :param reference: instance of ValueWrapper to refer on
        :return: Has value changed
        '''
        v = self.get_value()
        v_ref = reference.get_value()
        if v > v_ref:
            self.set_value(v_ref, validate=False)
            return True
        return False

    def clamp_higher(self, reference):
        '''
        sets own value higher or equal to value of reference
        :param reference: instance of ValueWrapper to refer on
        :return: Has value changed
        '''
        v = self.get_value()
        v_ref = reference.get_value()
        if v < v_ref:
            self.set_value(v_ref, validate=False)
            return True
        return False

    def sync_to(self, reference):
        '''
        Sets own value to reference
        :param reference:
        :return:
        '''
        v_ref = reference.get_value()
        self.set_value(v_ref)




class PlayingPosition(Plotter):
    def __init__(self, master):
        super().__init__(master)
        self.axes.set_axis_off()
        self.axes.set_ylim(-1, 1)
        self.mpl_canvas.get_tk_widget().configure(height=100)
        self.figure.tight_layout()
        self.toolbar.pack_forget()

        subframe = tk.Frame(self)
        subframe.pack(side="bottom", fill="x")

        starter = tk.Button(subframe, text="Set start", command=self.on_lcut)
        starter.grid(row=0, column=0, sticky="ew")

        rewinder = tk.Button(subframe, text="Jump to start", command=self.on_ljump)
        rewinder.grid(row=1, column=0, sticky="ew")

        self.min_cutter = ValueWrapper(subframe, self.validate_intervals, MARK_LOW)
        self.min_cutter.grid(row=0, column=1, sticky="nsew", rowspan=2)
        self.pointer = ValueWrapper(subframe, self.validate_intervals, MARK_PTR, color="#CC0000")
        self.pointer.grid(row=0, column=2, sticky="nsew", rowspan=2)
        self.max_cutter = ValueWrapper(subframe, self.validate_intervals, MARK_HIGH)
        self.max_cutter.grid(row=0, column=3, sticky="nsew", rowspan=2)

        resetter = tk.Button(subframe, text="Reset", command=self.on_reset_view)
        resetter.grid(row=2, column=1, sticky="ew", columnspan=3)

        ender = tk.Button(subframe, text="Set end", command=self.on_rcut)
        ender.grid(row=0, column=4, sticky="ew")

        fast_forwarder = tk.Button(subframe, text="Jump to end", command=self.on_rjump)
        fast_forwarder.grid(row=1, column=4, sticky="ew")

        self._range_patch = Rectangle((0, -1), 1, 2, color="gray", alpha=0.25)
        self.axes.add_patch(self._range_patch)
        self._mouse_pointer = self.axes.vlines(0, -1, 1, color="black")
        self._frame_pointer = self.axes.vlines(0, -1, 1, color="red")
        self._mouse_pointer_position = 0
        self.figure.canvas.mpl_connect("motion_notify_event", self.on_motion)
        self.figure.canvas.mpl_connect('button_press_event', self.on_mouse_button_press)

        self._low = 0
        self._high = 0
        self.callback = None
        self.range_change_callback = None
        self.set_range(0, 100)


    def on_lcut(self):
        self.min_cutter.sync_to(self.pointer)

    def on_rcut(self):
        self.max_cutter.sync_to(self.pointer)

    def on_ljump(self):
        self.pointer.sync_to(self.min_cutter)

    def on_rjump(self):
        self.pointer.sync_to(self.max_cutter)

    def on_reset_view(self):
        self.min_cutter.set_value(self._low)
        self.max_cutter.set_value(self._high)

    def set_mouse_pointer(self, new_x):
        self._mouse_pointer_position = new_x
        set_vlines_position(self._mouse_pointer, new_x)
        self.draw()

    def on_motion(self, event):
        if (event.xdata is not None):
            x = int(round(event.xdata))
            self.set_mouse_pointer(x)
            self.figure.canvas.draw_idle()
            if event.button == 1:
                self.set_frame(x)

    def on_mouse_button_press(self, event):
        if (event.xdata is not None):
            x = self._mouse_pointer_position
            if event.button == 1:
                self.set_frame(x)

    def update_interval(self):
        low_v = self.min_cutter.get_value()
        high_v = self.max_cutter.get_value()
        self._range_patch.set_x(low_v)
        self._range_patch.set_width(high_v-low_v)

    def set_range(self, low, high):
        self._low = low
        self._high = high
        self.axes.set_xlim(low, high)
        self.min_cutter.set_value(low)
        self.max_cutter.set_value(high)

    def get_range_full(self):
        return self._low, self._high

    def get_range_selected(self):
        return self.min_cutter.get_value(), self.max_cutter.get_value()

    def get_frame(self):
        return self.pointer.get_value()

    def set_frame(self, v):
        self.pointer.set_value(v)

    def validate_intervals(self, asker):
        forced_change = False
        forced_change |= self.min_cutter.clamp(self._low, self._high)
        forced_change |= self.max_cutter.clamp(self._low, self._high)
        if asker == MARK_LOW:
            forced_change |= self.max_cutter.clamp_higher(self.min_cutter)
        elif asker == MARK_HIGH:
            forced_change |= self.min_cutter.clamp_lower(self.max_cutter)

        if asker == MARK_PTR:
            v_min = self.min_cutter.get_value()
            v_max = self.max_cutter.get_value()
            width = v_max - v_min
            v = self.pointer.get_value()
            if v > v_max:
                self.max_cutter.set_value(v, False)
                forced_change = True
                #self.min_cutter.set_value(v-width, False)
            if v < v_min:
                #self.max_cutter.set_value(v+width, False)
                forced_change = True
                self.min_cutter.set_value(v, False)
        else:
            self.pointer.clamp(self._low, self._high)
            self.pointer.clamp_higher(self.min_cutter)
            self.pointer.clamp_lower(self.max_cutter)

        set_vlines_position(self._frame_pointer, self.pointer.get_value())
        self.update_interval()
        self.draw()
        if self.callback:
            self.callback()

        if self.range_change_callback is not None:
            if forced_change or asker==MARK_LOW or asker==MARK_HIGH:
                self.range_change_callback()

    def link_time(self, utc_explorer):
        self.min_cutter.link_time(utc_explorer)
        self.max_cutter.link_time(utc_explorer)
        self.pointer.link_time(utc_explorer)

    def set_time_range_bookmark_str(self, ts):
        start,end = ts.split(";")
        self.min_cutter.align_datetime_str(start)
        self.max_cutter.align_datetime_str(end)