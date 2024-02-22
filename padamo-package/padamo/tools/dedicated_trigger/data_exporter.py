import pickle
import zipfile
import datetime

import h5py
import io

from padamo.tools.viewer.parallel_signal_job import ParallelJobHandle, ParallelJob


class TriggerExporter(ParallelJob):
    def __init__(self, filename, intervals, signal_serialized):
        self.filename = filename
        self.intervals = intervals
        self.signal = pickle.loads(signal_serialized)
        super().__init__()

    def get_length(self):
        return len(self.intervals)

    def run_job(self):
        with zipfile.ZipFile(self.filename, 'w') as tgtzip:
            for i, interval in enumerate(self.intervals):
                self.set_progress(i+1)
                if not self.is_working():
                    return
                time = self.signal.time.request_data(interval.to_slice())
                space = self.signal.space.request_data(interval.to_slice())
                starttime = datetime.datetime.fromtimestamp(time[0])
                starttime = starttime.strftime("%y%m%d_%H%M%S")
                h5name = f"event_{starttime}_.h5"

                buf = io.BytesIO()
                h5file = h5py.File(buf,"w")
                h5file.create_dataset("pdm_2d_rot_global",data=space)
                h5file.create_dataset("unixtime_dbl_global",data=time)
                h5file.close()
                tgtzip.writestr(h5name,buf.getvalue())

class TriggerExporterHandle(ParallelJobHandle):
    TITLE = "Exporting..."

    def create_worker(self):
        filename = self.kwargs["filename"]
        signal_serialized = self.kwargs["signal_serialized"]
        intervals = self.kwargs["intervals"]
        return TriggerExporter(filename,intervals,signal_serialized)