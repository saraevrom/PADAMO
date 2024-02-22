import pickle
import h5py
from .parallel_signal_job import ParallelJob, ParallelJobHandle


class Exporter(ParallelJob):
    def __init__(self, kwargs):
        super().__init__()
        self.filename = kwargs["filename"]
        self.start_point = kwargs["start"]
        self.end_point = kwargs["end"]
        self.view = pickle.loads(kwargs["signal"])
        self.stepsize = kwargs["stepsize"]

    def get_length(self):
        start = self.start_point
        end = self.end_point
        return end - start

    def run_job(self):
        filename = self.filename
        start = self.start_point
        end = self.end_point
        view = self.view
        stepsize = self.stepsize
        with h5py.File(filename, "w") as fp:
            l0 = end - start
            spatial = fp.create_dataset("pdm_2d_rot_global", (l0,) + view.space.shape()[1:])
            temporal = fp.create_dataset("unixtime_dbl_global", (l0,), dtype=float)
            time_active = view.time.activate()
            space_active = view.space.activate()

            pointer = 0
            print("CYCLE START")
            while pointer < l0 and self.is_working():
                print(f"\r{pointer}/{l0}" + " " * 10, end="")
                self.set_progress(pointer)
                step = l0 - pointer
                step = min(stepsize, step)
                sub_start = pointer + start
                sub_end = sub_start + step
                nbt = time_active[sub_start:sub_end]
                if nbt.shape[0] > 1:
                    assert nbt[1] > nbt[0]
                # print(nbt)
                if len(nbt) != step:
                    print("COMPARE ERROR", len(nbt), step)
                    print("TIME shape", time_active.shape)
                    print("CHECK", type(view.time))
                assert len(nbt) == step
                temporal[pointer:pointer + step] = nbt
                spatial[pointer:pointer + step] = space_active[sub_start:sub_end]
                pointer += step
            print(f"\r{pointer}/{l0}" + " " * 10, end="")
            print()


class ExporterHandle(ParallelJobHandle):
    TITLE = "Exporting..."

    def create_worker(self):
        return Exporter(self.kwargs)
