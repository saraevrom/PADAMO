import pickle
from .parallel_signal_job import ParallelJob, ParallelJobHandle

def normalize_frame(frame):
    if hasattr(frame,"shape"):
        return frame.any()
    return frame

class EventFinder(ParallelJob):
    def __init__(self,trigger_src, start_i):
        super().__init__()
        self.trigger_src = trigger_src
        self.start_i = start_i

    def get_length(self):
        return self.trigger_src.shape[0]

    def run_job(self) -> None:
        i = self.start_i
        trigger = self.trigger_src
        length = trigger.shape[0]
        print("START", i)
        while i < length and normalize_frame(trigger[i]):
            if not self.is_working():
                print("Aborted trigger")
                return
            with self.progress.get_lock():
                self.progress.value = i
            i += 1
        if i >= length:
            return
        print("Reached triggerless area", i)
        while i < length and not normalize_frame(trigger[i]):
            if not self.is_working():
                print("Aborted trigger")
                return
            with self.progress.get_lock():
                self.progress.value = i
            i += 1
        if i >= length:
            return
        print("Reached triggerred index", i)
        self.return_result(i)


class EventFinderHandle(ParallelJobHandle):
    TITLE = "Triggering in process"


    def create_worker(self):
        trigger = pickle.loads(self.kwargs["trigger"]).activate()
        start_i = self.kwargs["start_i"]
        return EventFinder(trigger,start_i)