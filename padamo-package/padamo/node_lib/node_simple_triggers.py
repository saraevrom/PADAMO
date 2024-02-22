import sys
from datetime import datetime
from datetime import timedelta

import numba as nb
import numpy as np
import psutil
from padamo.node_processing import Node, FLOAT, INTEGER, STRING, SIGNAL, AllowExternal
from padamo.lazy_array_operations import LazyArrayOperation
from padamo.lazy_array_operations.base import normalize_slice
from padamo.lazy_array_operations.base import AutoRequest
from padamo.utilities.dual_signal import Signal
from .disabled_node_arrays import DummyArray

class LazyLCThresholdTrigger(LazyArrayOperation):
    def __init__(self, source: LazyArrayOperation, threshold):
        self.source = source
        self.threshold = threshold

    def shape(self):
        src_shape = self.source.shape()
        return (src_shape[0],)

    def request_single(self,i:int):
        frame = self.source.request_data(i)
        return np.sum(frame)>self.threshold

    def request_slice(self, s: slice):
        frames = self.source.request_data(s)
        #mask = frames > self.threshold
        #print(mask)
        srclen = len(self.source.shape())
        srcrange = range(1,srclen)
        axes = tuple(srcrange)
        res = np.sum(frames, axis=axes)>self.threshold
        #print(res)
        return res


class LazyThresholdTrigger(LazyArrayOperation):
    def __init__(self, source: LazyArrayOperation, threshold):
        self.source = source
        self.threshold = threshold

    def shape(self):
        src_shape = self.source.shape()
        return (src_shape[0],)

    def request_single(self,i:int):
        frame = self.source.request_data(i)
        return (frame>self.threshold).any()

    def request_slice(self, s: slice):
        frames = self.source.request_data(s)
        mask = frames > self.threshold
        #print(mask)
        srclen = len(self.source.shape())
        srcrange = range(1,srclen)
        axes = tuple(srcrange)
        res = np.logical_or.reduce(mask, axis=axes)
        #print(res)
        return res

@nb.njit
def deconvolve(x, window):
    length = x.shape[0]+(window-1)
    res = np.full(shape=(length,), fill_value=False)
    for i in range(x.shape[0]):
        for j in range(window):
            res[i+j] |= x[i]
    return res


class LazyMedianThresholdTrigger(LazyArrayOperation):
    def __init__(self, source: LazyArrayOperation, threshold):
        self.source = source
        self.threshold = threshold

    def shape(self):
        src_shape = self.source.shape()
        return (src_shape[0],)

    def request_single(self,i:int):
        frame = self.source.request_data(i)
        med = np.median(frame)
        return med>self.threshold

    def request_slice(self, s: slice):
        frames = self.source.request_data(s)
        return np.median(frames,axis=(1,2)) > self.threshold


class TresholdTriggerNode(Node):
    INPUTS = {
        "signal":SIGNAL
    }
    CONSTANTS = {
        "threshold":AllowExternal(1.0)
    }
    OUTPUTS = {
        "signal_with_trigger":SIGNAL
    }
    LOCATION = "/Triggers/Pixel threshold trigger"
    REPR_LABEL = "Pixel threshold trigger"
    MIN_SIZE = (150,15)

    def calculate(self,globalspace:dict) -> dict:
        signal = self.require("signal")
        threshold = self.constants["threshold"]

        signal_out = signal.clone()
        signal_out.trigger = LazyThresholdTrigger(signal.space, threshold)
        return dict(signal_with_trigger=signal_out)


class LCTresholdTriggerNode(Node):
    INPUTS = {
        "signal":SIGNAL
    }
    CONSTANTS = {
        "threshold":AllowExternal(1.0)
    }
    OUTPUTS = {
        "signal_with_trigger":SIGNAL
    }
    LOCATION = "/Triggers/Lightcurve threshold trigger"
    REPR_LABEL = "Lightcurve threshold trigger"
    MIN_SIZE = (150,15)

    def calculate(self,globalspace:dict) -> dict:
        signal = self.require("signal")
        threshold = self.constants["threshold"]

        signal_out = signal.clone()
        signal_out.trigger = LazyLCThresholdTrigger(signal.space, threshold)
        return dict(signal_with_trigger=signal_out)


class MedianTresholdTriggerNode(Node):
    INPUTS = {
        "signal":SIGNAL
    }
    CONSTANTS = {
        "threshold":AllowExternal(1.0)
    }
    OUTPUTS = {
        "signal_with_trigger":SIGNAL
    }
    LOCATION = "/Triggers/Median threshold trigger"
    REPR_LABEL = "Median threshold trigger"
    MIN_SIZE = (150,15)

    def calculate(self,globalspace:dict) -> dict:
        signal = self.require("signal")
        threshold = self.constants["threshold"]

        signal_out = signal.clone()
        signal_out.trigger = LazyMedianThresholdTrigger(signal.space, threshold)
        return dict(signal_with_trigger=signal_out)

