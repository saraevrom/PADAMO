import os
import numpy as np
import h5py
import h5pickle
from padamo.lazy_array_operations import LazyArrayOperation
from padamo.lazy_array_operations.slice_combination import normalize_slice
from padamo.node_processing import Node, NodeExecutionError, STRING, ARRAY, SIGNAL, AllowExternal
from padamo.utilities.dual_signal import Signal

#CACHE_WORKSPACE =

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
