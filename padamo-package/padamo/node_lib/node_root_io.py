import os
import numpy as np
import h5py
import uproot

from padamo.lazy_array_operations import LazyArrayOperation
from padamo.lazy_array_operations.slice_combination import normalize_slice
from padamo.node_processing import Node, NodeExecutionError, STRING, ARRAY, SIGNAL, AllowExternal, Optional
from padamo.utilities.dual_signal import Signal


def parse_tree(root_dataset, root_path):
    root_path_split = root_path.split("/")
    for item in root_path_split:
        root_dataset = root_dataset[item]
    return root_dataset

class LazyRootReader(LazyArrayOperation):
    def __init__(self, file_path:str, root_path:str, field=""):
        self.file_path = file_path
        self.root_path = root_path
        self.field = field
        self._initialize()

    def _initialize(self):
        self.root_dataset = uproot.open(self.file_path)
        self.root_dataset = parse_tree(self.root_dataset, self.root_path)
        self.length = self.root_dataset.num_entries
        aux_array = np.squeeze(self.root_dataset.array(library="np",entry_stop=1))
        self.add_shape = aux_array.shape

    def shape(self):
        return (self.length,)+self.add_shape

    def request_slice(self,s:slice):
        start,stop, step = normalize_slice(self.length,s)
        subarray = self.root_dataset.array(library="np", entry_start=start, entry_stop=stop)
        if not self.field:
            return np.squeeze(subarray[::step])
        else:
            return np.squeeze(subarray[::step][self.field])

    def request_single(self,i:int):
        start = i
        stop = i+1
        subarray = self.root_dataset.array(library="np", entry_start=start, entry_stop=stop)
        if not self.field:
            return np.squeeze(subarray)
        else:
            return np.squeeze(subarray[self.field])

    def __getstate__(self):
        return {
            "file_path":self.file_path,
            "root_path":self.root_path
        }

    def __setstate__(self, state):
        self.file_path = state["file_path"]
        self.root_path = state["root_path"]
        self._initialize()


class EagerRootReader(LazyArrayOperation):
    def __init__(self, file_path:str, root_path:str,field=""):
        self.file_path = file_path
        self.root_path = root_path
        root_dataset = uproot.open(self.file_path)
        root_dataset = parse_tree(root_dataset, self.root_path)
        self.array = np.squeeze(root_dataset.array(library="numpy"))
        self.field = field

    def shape(self):
        return self.array.shape

    def request_data(self,d):
        if self.field:
            return self.array[d][self.field]
        else:
            return self.array[d]


class RootTreeNode(Node):
    INPUTS = {
        "filename":STRING,
    }
    CONSTANTS = {
        "spatial_root_tree_path": AllowExternal("tevent/photon_count_data"),
        "spatial_field": AllowExternal(""),
        "temporal_root_tree_path": AllowExternal("tevent/timestamp_unix"),
        "temporal_field": AllowExternal(""),
        "eager":True
    }
    OUTPUTS = {
        "signal":SIGNAL
    }
    LOCATION = "/RootTTrees/Local Root TTree Signal"
    REPR_LABEL="Local Root TTree Signal"

    def calculate(self, globals):
        file_path = self.require("filename")
        if self.constants["eager"]:
            cls = EagerRootReader
        else:
            cls = LazyRootReader
        spatial = cls(file_path=file_path, root_path=self.constants["spatial_root_tree_path"],
                      field=self.constants["spatial_field"])
        temporal = cls(file_path=file_path, root_path=self.constants["temporal_root_tree_path"],
                       field=self.constants["temporal_field"])
        return dict(signal=Signal(spatial,temporal))