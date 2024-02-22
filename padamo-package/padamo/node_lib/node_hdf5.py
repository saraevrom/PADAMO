import os
import numpy as np
import h5py
import h5pickle
from padamo.lazy_array_operations import LazyArrayOperation
from padamo.lazy_array_operations.slice_combination import normalize_slice
from padamo.node_processing import Node, NodeExecutionError, STRING, ARRAY, SIGNAL, AllowExternal
from padamo.utilities.dual_signal import Signal

def create_signal(filename, spatial_key, temporal_key):
    reader_s = LazyHDF5reader(filename, spatial_key)
    reader_t = LazyHDF5reader(filename, temporal_key)
    return Signal(reader_s, reader_t)

class LazyHDF5reader(LazyArrayOperation):
    def __init__(self, filename, field):
        self.filename = filename
        self.field = field
        self._file = None
        self.ensure_file()

    def ensure_file(self):
        if not self.filename:
            raise ValueError("Filename is not set")
        if not os.path.isfile(self.filename):
            raise FileNotFoundError(f"File {self.filename} is not found")
        if self._file is None:
            self._file = h5pickle.File(self.filename, "r")

    def request_data(self, interesting_slices):
        #print("H5",interesting_slices)
        self.ensure_file()
        res = np.array(self._file[self.field][interesting_slices])
        return res

    def shape(self):
        return self._file[self.field].shape


class H5SourceArray(Node):
    INPUTS = {
        "filename":STRING
    }
    CONSTANTS = {
        "field": AllowExternal("field")
    }
    OUTPUTS = {
        "array": ARRAY
    }
    REPR_LABEL = "Local HDF5 source"
    LOCATION = "/HDF5/Local HDF5 source"

    @classmethod
    def on_constants_update(cls, graphnode):
        field = graphnode.get_constant("field")
        graphnode.set_title(cls.REPR_LABEL+ f"({field})")

    def calculate(self, globalspace:dict) -> dict:
        filename = self.require( "filename")
        field = self.constants["field"]
        try:
            reader = LazyHDF5reader(filename, field)
        except ValueError or FileNotFoundError as e:
            raise NodeExecutionError(str(e), self)
        return dict(array=reader)


class SimpleH5SourceArray(Node):
    INPUTS = {
        "filename":STRING,
    }
    CONSTANTS = {
        "spatial_field":AllowExternal("pdm_2d_rot_global"),
        "temporal_field":AllowExternal("unixtime_dbl_global"),
    }
    OUTPUTS = {
        "signal": SIGNAL
    }
    REPR_LABEL = "Local HDF5 source"
    LOCATION = "/HDF5/Local HDF5 source (fixed fields)"

    @classmethod
    def on_constants_update(cls,graphnode):
        space = graphnode.get_constant('spatial_field')
        time = graphnode.get_constant('temporal_field')
        graphnode.set_title(cls.REPR_LABEL + f"({space}, {time})")

    def calculate(self, globalspace:dict) -> dict:
        filename = self.require( "filename")
        try:
            reader = create_signal(filename,
                                   self.constants["spatial_field"],
                                   self.constants["temporal_field"]
                                   )
        except Exception as e:
            raise NodeExecutionError(str(e), self)
        return dict(signal=reader)


def generate_old_t(ngtu_global, start, end,step, mul, mul2):
    res = np.zeros(shape=len(range(start,end,step)))
    for i in range(start,end,step):
        res[i-start] = (ngtu_global[i//128]*mul2 + (i%128)*mul)*2.5e-6
    return res

class LazyOldGTU(LazyArrayOperation):
    def __init__(self,ngtu_global:LazyArrayOperation, multiplier,multiplier2, control_length):
        self.multiplier = multiplier
        self.multiplier2 = multiplier2
        self.input_data = ngtu_global
        self.control_length = control_length

    def request_data(self, interesting_slices):
        if isinstance(interesting_slices, tuple):
            if len(interesting_slices)==1:
                interesting_slices = interesting_slices[0]
            else:
                raise IndexError("Time is 1D only")
        if isinstance(interesting_slices,int):
            i = interesting_slices
            return (self.input_data.request_data(i // 128)*self.multiplier2 + (i % 128) * self.multiplier) * 2.5e-6
        else:
            start, end, step = normalize_slice(self.control_length,interesting_slices)
            return generate_old_t(self.input_data.activate(),start,end,step,self.multiplier, self.multiplier2)

    def shape(self):
        return (self.control_length,)


class D1DataNormalizer(Node):
    INPUTS = {
        "spatial":ARRAY,
        "time":ARRAY,
    }
    CONSTANTS = {
        "is_d3":False
    }
    OUTPUTS = {
        "signal":SIGNAL
    }
    REPR_LABEL = "Old time remapper"
    LOCATION = "/HDF5/Tuloma old remapper"

    def calculate(self, globalspace:dict) -> dict:
        spatial = self.require("spatial")
        time = self.require("time")
        if len(time.shape())==2:
            print("MATLAB TIME DETECTED", time.shape())
            time = time[:,0]
        if self.constants["is_d3"]:
            multiplier = 16384
            multiplier2 = 1
        else:
            multiplier = 1
            multiplier2 = 128
        ctrl_len = spatial.shape()[0]
        new_time = LazyOldGTU(time, multiplier,multiplier2,ctrl_len)
        return dict(signal=Signal(spatial, new_time))


class LocalHDF5Directory(Node):
    INPUTS = {
        "src_dir":STRING,
    }
    CONSTANTS = {
        "spatial_field": AllowExternal("pdm_2d_rot_global"),
        "temporal_field": AllowExternal("unixtime_dbl_global"),
    }
    OUTPUTS = {
        "signal":SIGNAL
    }
    REPR_LABEL = "Local HDF5 directory"
    LOCATION = "/HDF5/Local HDF5 directory"

    def calculate(self, globalspace:dict) -> dict:
        src_dir = self.require("src_dir")
        time_key = self.constants["temporal_field"]
        space_key = self.constants["spatial_field"]
        if not os.path.isdir(src_dir):
            raise NodeExecutionError(f"No such directory {src_dir}", self.graph_node)
        signal = None
        files = map(lambda x: os.path.join(src_dir,x),
                    os.listdir(src_dir))

        def allowed(k):
            if not (k.endswith(".h5") or k.endswith(".mat")):
                return False
            try:
                with h5py.File(k,"r") as fp:
                    return time_key in fp.keys()
            except:
                return False

        def sortkey(k):
            with h5py.File(k,"r") as fp:
                return fp[time_key][0]

        files = filter(allowed,files)
        files = map(lambda x: (x, sortkey(x)),files)
        files = list(files)
        files.sort(key=lambda x: x[1])
        files = list(map(lambda x: x[0],files))
        for filename in files:
            new_part = create_signal(filename,space_key, time_key)
            if signal is None:
                signal = new_part
            else:
                signal = signal.extend(new_part)

        if signal is None:
            raise NodeExecutionError("Suitable signals not found",self.graph_node)

        return dict(signal=signal)


class WriteHDF5ArrayNode(Node):
    INPUTS = {
        "array": ARRAY,
        "filename": STRING
    }
    CONSTANTS = {
        "field":AllowExternal("output_field")
    }
    REPR_LABEL = "HDF writer"
    LOCATION = "/HDF5/HDF5 Writer"
    IS_FINAL = True

    def calculate(self,globalspace:dict) -> dict:
        array = self.require("array")
        field = self.constants["field"]
        filepath = self.require("filename")
        os.makedirs(os.path.dirname(filepath),exist_ok=True)
        with h5py.File(filepath,"a") as fp:
            if field in fp.keys():
                del fp[field]
            fp.create_dataset(name=field, data=array.activate())
        return dict()