import numba as nb
import numpy as np
from padamo.node_processing import Node, FLOAT, INTEGER, ARRAY, SIGNAL
from padamo.lazy_array_operations import LazyArrayOperation
from padamo.utilities.dual_signal import Signal
from padamo.lazy_array_operations.basic_operations import ConstantArray


def find_start(src:LazyArrayOperation, thresh):
    print()
    l1 = src.shape()[0]
    for i in range(src.shape()[0]):
        print("\r",i,"/",l1,end="")
        if src.request_data(i)>=thresh:
            print()
            return i
    print()
    return src.shape()[0]-1

def find_end(src:LazyArrayOperation, thresh):
    print()
    l1 = src.shape()[0]
    for i in range(src.shape()[0]-1,-1,-1):
        print("\r",i,"/",l1,end="")
        if src.request_data(i)>=thresh:
            print()
            return i
    print()
    return 0

class TriggerLine(Node):
    INPUTS = {
        "lightcurve":SIGNAL,
        "threshold":FLOAT,
        "margin":INTEGER
    }
    OUTPUTS = {
        "start":INTEGER,
        "end":INTEGER
    }
    REPR_LABEL = "Threshold trigger"
    LOCATION = "/Triggers/Threshold trigger"

    def calculate(self, globalspace:dict) ->dict:
        source:Signal = self.require( "lightcurve")
        threshold = self.require( "threshold")
        margin = self.require( "margin", optional=True) or 0
        signal = source.space
        start = find_start(signal,threshold)
        if start == signal.shape()[0]-1:
            end = start
        else:
            end = find_end(signal,threshold)+1

        start = max(0, start-margin)
        end = min(signal.shape()[0], end+margin)
        return dict(start=start,end=end)



class TriggerLineAsymmetrical(Node):
    INPUTS = {
        "lightcurve":SIGNAL,
        "threshold":FLOAT,
        "margin_left":INTEGER,
        "margin_right":INTEGER
    }
    OUTPUTS = {
        "start":INTEGER,
        "end":INTEGER
    }
    REPR_LABEL = "Threshold trigger (Asymmetrical)"
    LOCATION = "/Triggers/Threshold trigger (Asymmetrical)"

    def calculate(self, globalspace:dict) ->dict:
        source:Signal = self.require( "lightcurve")
        threshold = self.require( "threshold")
        margin_left = self.require( "margin_left", optional=True) or 0
        margin_right = self.require( "margin_right", optional=True) or 0
        signal = source.space
        start = find_start(signal,threshold)
        if start == signal.shape()[0]-1:
            end = start
        else:
            end = find_end(signal,threshold)+1

        start = max(0, start-margin_left)
        end = min(signal.shape()[0], end+margin_right)
        return dict(start=start,end=end)

class LazyLC(LazyArrayOperation):
    def __init__(self, source:LazyArrayOperation, maxmode,pixelmap=None):
        self.source = source
        if maxmode:
            print("LC uses max")
            self.lcfunc = np.max
        else:
            print("LC uses sum")
            self.lcfunc = np.sum
        if pixelmap is None:
            self.pixelmap = None
        else:
            self.pixelmap = pixelmap.request_all_data()

    def request_data(self, interesting_slices):
        src = self.source.request_data(interesting_slices)
        if self.pixelmap is not None:
            src[:,np.logical_not(self.pixelmap)] = 0
        if src.shape==self.shape():
            axes = tuple(range(1,len(self.shape())))
            return self.lcfunc(src,axis=axes)
        else:
            return self.lcfunc(src)

    def shape(self):
        return self.source.shape()

class LightCurveNode(Node):
    INPUTS = {
        "signal": SIGNAL,
        "pixelmap":ARRAY
    }

    CONSTANTS = {
        "use_max":(bool,False)
    }


    OUTPUTS = {
        "lightcurve":SIGNAL
    }

    REPR_LABEL = "Lightcurve"
    LOCATION = "/Signal processing/Lightcurve"

    def calculate(self, globalspace:dict) ->dict:
        signal = self.require("signal")
        pixelmap = self.require("pixelmap", optional=True)
        spatial = signal.space
        temporal = signal.time
        maxmode = self.constants["use_max"]
        spatial_lc = LazyLC(spatial,maxmode,pixelmap)
        return dict(lightcurve=Signal(spatial_lc,temporal))




class TriggerMatrix(Node):
    INPUTS = {
        "signal": SIGNAL,
        "threshold": FLOAT,
    }
    OUTPUTS = {
        "map": ARRAY
    }

    REPR_LABEL = "Threshold map"
    LOCATION = "/Triggers/Threshold map"

    def calculate(self, globalspace:dict) ->dict:
        signal = self.require("signal")
        threshold = self.require("threshold")
        signal_space = signal.space.request_all_data()
        if len(signal_space.shape)==2:
            maxes = signal_space
        else:
            maxes = np.max(signal_space, axis=0)
        matrix = maxes>threshold
        return dict(map=ConstantArray(matrix))


@nb.njit(nb.int64[:](nb.float64[:],nb.int64))
def find_n_biggest_indices(x:np.ndarray,n:int):
    items = np.zeros(shape=(n,))
    indices = np.arange(n)
    items[:] = x[:n]
    # Insertion sort of first batch of elements
    for i in range(1,n):
        j = i
        while j>0 and items[j]<items[j-1]:
            items[j],items[j-1] = items[j-1],items[j]
            indices[j], indices[j-1] = indices[j-1], indices[j]
            j -= 1

    m = x.shape[0]
    for i in range(n,m):
        if x[i]>items[0]:
            items[0] = x[i]
            indices[0] = i
            j = 0
            while j<n-1 and items[j]>items[j+1]:
                items[j], items[j+1] = items[j+1], items[j]
                indices[j], indices[j+1] = indices[j+1], indices[j]
                j += 1
    return indices


def trigger_amount(maxes:np.ndarray, n:int)->np.ndarray:
    flat_maxes = maxes.flatten()
    if n>flat_maxes.shape[0]:
        raise ValueError(f"Cannot take {n} items from array of length {flat_maxes.shape[0]}")
    requested_indices = find_n_biggest_indices(flat_maxes.astype(float),n)
    res = np.full(shape=flat_maxes.shape,fill_value=False)
    res[requested_indices] = True
    return res.reshape(maxes.shape)


class TriggerMatrixNumber(Node):
    INPUTS = {
        "signal": SIGNAL,
        "amount": INTEGER,
    }
    OUTPUTS = {
        "map": ARRAY
    }

    REPR_LABEL = "Brightest pixels"
    LOCATION = "/Triggers/Brightest pixels"

    def calculate(self, globalspace:dict) ->dict:
        signal = self.require("signal")
        n = self.require("amount")
        signal_space = signal.space.request_all_data()
        if len(signal_space.shape)==2:
            maxes = signal_space
        else:
            maxes = np.max(signal_space, axis=0)
        matrix = trigger_amount(maxes,n)
        return dict(map=ConstantArray(matrix))

