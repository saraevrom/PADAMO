import os
import tkinter as tk
from tkinter import ttk
from multiprocessing import Queue, Process, Value

from padamo.tools.remote_explorer.login_form import PersistentConnection


class ProgressDisplay(tk.Toplevel):
    def __init__(self, parent, length, close_callback, title):
        super().__init__(parent)
        self.title(title)
        self.length = length
        self.display_var = tk.StringVar()
        label = tk.Label(self, textvariable=self.display_var)
        label.pack(side="top",fill="x", expand=True)

        self.progressbar = ttk.Progressbar(self,orient='horizontal',maximum=length, length=300)
        self.progressbar.pack(side="top",fill="x", expand=True)


        self.offswitch_var = tk.IntVar()
        self.offswitch = tk.Checkbutton(self, text="Switch off computer after operation",variable=self.offswitch_var)
        self.offswitch.pack(side="top",fill="x", expand=True)

        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.close_callback = close_callback
        self._alive = True
        self.set_value(0)

    def on_close(self, *args):
        self.close_callback()
        self._alive = False
        print("Progress watcher closed")
        self.destroy()

    def set_value(self,value):
        if self._alive:
            self.display_var.set(f"{value}/{self.length}")
            self.progressbar['value'] = value


class ParallelJob(Process):
    def __init__(self):
        super().__init__()
        self.working = Value('i',1)
        self.queue = None
        self.progress = Value('i',0)

    def get_length(self):
        raise NotImplementedError

    def set_queue(self,queue):
        self.queue = queue

    def return_result(self,res):
        self.queue.put(res)
        self.stop_normal()

    def stop_with_no_result(self):
        with self.working.get_lock():
            if self.working.value != 0:
                self.working.value = 2

    def set_progress(self, i):
        with self.progress.get_lock():
            self.progress.value = i

    def is_working(self):
        return self.working.value == 1

    def stop_normal(self):
        with self.working.get_lock():
            self.working.value = 0

    def run_job(self):
        raise NotImplementedError

    def run(self):
        PersistentConnection.reset()
        try:
            self.run_job()
        finally:
            self.stop_with_no_result()


class ParallelJobHandle(object):
    TITLE = "Job is running"

    def __init__(self, parent):
        self.parent = parent
        self.parent.after(100, self.tick_update)
        self._worker = None
        self._progress_display = None
        self._queue = None
        self.callback = None
        self.kwargs = dict()

    def set_callback(self,callback):
        self.callback = callback

    def tick_update(self):
        self.watcher()
        self.parent.after(100, self.tick_update)

    def stop(self):
        self._stop_worker()

    def _stop_worker(self):
        if self._worker is None:
            return
        self._worker.stop_normal()
        self._worker.join()
        self._worker = None
        if self._progress_display is not None:
            self._progress_display.destroy()
            self._progress_display = None

    def watcher(self):
        if self._worker is not None:
            if self._progress_display is not None:
                val = self._worker.progress.value
                self._progress_display.set_value(val)
            if not self._worker.is_working():
                #self._worker.join()
                if self._worker.working.value==0:
                    res = self._queue.get()
                    print("GOT IT")
                    if self.callback is not None:
                        self.callback(res)
                else:
                    print("No result available")

                if self._progress_display is not None:
                    should_poweroff = self._progress_display.offswitch_var.get()
                else:
                    should_poweroff = False
                self._stop_worker()

                if should_poweroff:
                    os.system("poweroff")


    def start(self, **kwargs):
        if self._worker is not None:
            return
        self.kwargs = kwargs
        self._initiate()

    def create_worker(self):
        raise NotImplementedError

    def _initiate(self):
        self._stop_worker()
        self._queue = Queue()
        self._worker = self._worker = self.create_worker()
        self._worker.set_queue(self._queue)
        self._progress_display = ProgressDisplay(self.parent,self._worker.get_length(), self._stop_worker, self.TITLE)
        self._worker.start()
