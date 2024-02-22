import datetime
import io
import os
import pickle

import PIL.Image
import imageio as iio
import numpy as np
import tqdm

from .parallel_signal_job import ParallelJob, ParallelJobHandle
from .controllable_lc_plotter import LCPlotter
from .detached_plotter import DetachedPlotter


DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S.%f"

def insert_number(fn,n):
    filename, ext = os.path.splitext(fn)
    return filename+f"-{n}"+ext


class Animator(ParallelJob):
    def __init__(self, kwargs):
        super().__init__()
        self.signal = pickle.loads(kwargs["signal"])
        self.filename = kwargs["filename"]
        self.insert_lc = kwargs["insert_lc"]
        self.low_frame = kwargs["low_frame"]
        self.high_frame = kwargs["high_frame"]
        self.step = kwargs["step"]
        self.fps = kwargs["fps"]
        self.show_time = kwargs["show_time"]
        self.time_format = kwargs["time_format"]
        self.trigger_only = kwargs["trigger_only"]
        self.png_dpi = kwargs["png_dpi"]
        parent_plotter = kwargs["parent_plotter"]
        min_, max_ = parent_plotter.get_bounds()
        self.plotter = DetachedPlotter(fig_size=(4, 4), autoscale=parent_plotter.autoscale(), min_=min_, max_=max_,dpi=self.png_dpi)
        parent_plotter.copy_conf_to(self.plotter)

    def get_view(self):
        a, b = self.low_frame, self.high_frame
        cur_view = self.signal
        views = cur_view.space.request_data(slice(a, b))
        return views

    def get_length(self):
        low_frame = self.low_frame
        high_frame = self.high_frame
        skip = self.step
        return len(range(low_frame, high_frame, skip))

    def run_job(self):
        filename = self.filename
        insert_lc = self.insert_lc
        fps = self.fps
        low_frame = self.low_frame
        high_frame = self.high_frame
        skip = self.step
        if filename.endswith(".png"):
            writer = None
        elif filename.endswith(".gif"):
            writer = iio.get_writer(filename, duration=1000 / fps)
        else:
            writer = iio.get_writer(filename, fps=fps)

        if insert_lc:
            view = self.get_view()
            if view is None:
                bottom = None
            else:
                figsize = self.plotter.figure.get_size_inches()
                bottom = LCPlotter(view, (figsize[0], 1),dpi=self.png_dpi)
        else:
            bottom = None

        start_index = 0

        for i in tqdm.tqdm(range(low_frame, high_frame, skip)):
            if not self.is_working():
                break
            self.set_progress((i-low_frame)//skip)
            # self.on_player_ctrl_frame(i)
            # self.plotter.draw(False)
            if self.trigger_only:
                trig = self.signal.request_trigger_data(i)
                if not(trig is None or np.logical_or.reduce(trig)):
                    continue
            frame = self.signal.space.request_data(i)
            time_ = self.signal.time.request_data(i)
            #dt = datetime.datetime.utcfromtimestamp(float(time_))
            self.plotter.buffer_matrix = frame
            self.plotter.update_matrix_plot(True)
            if self.show_time:
                print("ANIM", frame, time_)
                self.plotter.axes.set_title(self.time_format.format_time(i, float(time_)))
            else:
                self.plotter.axes.set_title("")
            self.plotter.draw()

            buf = io.BytesIO()
            frame = self.plotter.get_frame()
            if bottom is not None:
                bottom.set_frame(i - low_frame)
                frame2 = bottom.get_frame()
                w = max(frame.size[0], frame2.size[0])
                h = frame.size[1] + frame2.size[1]
                result_frame = PIL.Image.new("RGB", (w, h))
                result_frame.paste(frame, (0, 0))
                result_frame.paste(frame2, (0, frame.size[1]))
            else:
                result_frame = frame

            if writer is None:
                fn = insert_number(filename, i)
                result_frame.save(fn)
            else:
                result_frame.save(buf, format="png")
                buf.seek(0)
                frame_iio = iio.v3.imread(buf)
                writer.append_data(frame_iio)
        if writer is not None:
            writer.close()


class AnimationHandle(ParallelJobHandle):
    TITLE = "Rendering..."

    def create_worker(self):
        return Animator(self.kwargs)
