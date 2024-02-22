import tkinter as tk
from datetime import datetime
from tkinter import ttk
from .playing_position import PlayingPosition
from padamo.bookmarking import Bookmark

FAST_FWD_SKIP = 1
FRAME_DELAY = 250 #ms



class ControlButtons(ttk.Frame):
    PAUSE = 0
    PLAYING = 1
    PLAYING_INV = 2
    FAST_FWD = 3
    REWIND = 4
    STEP_R = 5
    STEP_L = 6
    MUL_TABLE = [0, 1, -1, FAST_FWD_SKIP, -FAST_FWD_SKIP, 1, -1]
    def __init__(self, master):
        super(ControlButtons, self).__init__(master)
        self.playing_state = self.PAUSE
        self.multiplier = 1
        tk.Button(self, text="<<", command=lambda: self.on_button_press(self.REWIND))\
            .grid(row=0, column=0, sticky="nsew")
        tk.Button(self, text="<", command=lambda: self.on_button_press(self.PLAYING_INV))\
            .grid(row=0, column=1, sticky="nsew")
        tk.Button(self, text="<|", command=lambda: self.on_button_press(self.STEP_L)) \
            .grid(row=0, column=2, sticky="nsew")
        tk.Button(self, text="||", command=lambda: self.on_button_press(self.PAUSE))\
            .grid(row=0, column=3, sticky="nsew")
        tk.Button(self, text="|>", command=lambda: self.on_button_press(self.STEP_R)) \
            .grid(row=0, column=4, sticky="nsew")
        tk.Button(self, text=">", command=lambda: self.on_button_press(self.PLAYING))\
            .grid(row=0, column=5, sticky="nsew")
        tk.Button(self, text=">>", command=lambda: self.on_button_press(self.FAST_FWD))\
            .grid(row=0, column=6, sticky="nsew")
        self.button_callback = None

        self.rowconfigure(0, weight=1)

    def on_button_press(self, btn):
        if self.playing_state == btn == self.REWIND:
            self.multiplier *= 2
        elif self.playing_state == btn == self.FAST_FWD:
            self.multiplier *= 2
        else:
            self.multiplier = 1
        self.playing_state = btn
        if self.button_callback is not None:
            self.button_callback()

    def get_frame_step(self):
        return self.MUL_TABLE[self.playing_state]*self.multiplier

    def stop_playing(self):
        self.playing_state = self.PAUSE

    def step_single_check(self):
        if self.playing_state==self.STEP_L or self.playing_state==self.STEP_R:
            self.stop_playing()

class PlayerControls(ttk.Frame):
    def __init__(self, master, frame_callback, click_callback):
        super(PlayerControls, self).__init__(master)
        self.ut0 = None
        #self.play_slider = ValuedSlider(self)
        #self.play_slider.pack(side=tk.TOP,expand=True, fill=tk.X)
        self.playing_position = PlayingPosition(self)
        self.playing_position.pack(side=tk.TOP, expand=True, fill=tk.X)
        self.playing_position.callback = self.on_control_update
        self.control_btns = ControlButtons(self)
        self.control_btns.pack(side=tk.BOTTOM)
        self.upper_limit = 0  # To keep it consistent
        self.control_btns.button_callback = self.on_control_update
        #self.play_slider.set_slider_callback(self.on_control_update)
        self.playing = False
        self.frame_callback = frame_callback
        self.click_callback = click_callback
        self.set_limit(100)

    def set_limit(self, upper):
        #self.play_slider.set_limit(upper)
        self.upper_limit = upper
        self.playing_position.set_range(0, upper)


    def on_range_limit_change(self):
        pass

    def on_control_update(self):
        self.click_callback()
        self.start_play_checked()

    def start_play_checked(self):
        if not self.playing:
            self.playing = True
            self.playcycle()

    def draw_frame(self):
        frame_step = self.control_btns.get_frame_step()
        #low, high = self.play_slider.get_limits()
        #frame_num = self.play_slider.get_value() + frame_step
        low, high = self.playing_position.get_range_selected()
        frame_num = self.playing_position.get_frame() + frame_step
        if frame_num >= high:
            frame_num = high
            self.control_btns.stop_playing()
        if frame_num < low:
            frame_num = low
            self.control_btns.stop_playing()
        self.frame_callback(frame_num)
        self.playing_position.set_frame(frame_num)
        #self.play_slider.set_value(frame_num)
        self.control_btns.step_single_check()

    def playcycle(self):
        self.draw_frame()
        if self.control_btns.playing_state != ControlButtons.PAUSE:
            self.after(FRAME_DELAY, self.playcycle)
        else:
            self.playing = False


    def get_selected_range(self):
        return self.playing_position.get_range_selected()
        # return self.play_slider.get_limits()

    def get_time_range(self):
        if self.ut0 is None:
            return None
        start, end = self.get_selected_range()
        ut_start = float(self.ut0[start])
        ut_end = float(self.ut0[end])
        return datetime.utcfromtimestamp(ut_start),datetime.utcfromtimestamp(ut_end)

    def create_bookmark(self):
        timerange = self.get_time_range()
        if timerange is None:
            return None
        start,end = timerange
        return Bookmark(start,end)

    def link_time(self, ut0):
        self.playing_position.link_time(ut0)
        self.ut0 = ut0
        # self.play_slider.ut0_explorer = ut0

    def set_time_range_bookmark_str(self, ts):
        self.playing_position.set_time_range_bookmark_str(ts)