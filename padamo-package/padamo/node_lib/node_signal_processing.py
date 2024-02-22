import sys
from datetime import datetime
from datetime import timedelta

import numba as nb
import numpy as np
from padamo.node_processing import Node, FLOAT, INTEGER, STRING, SIGNAL, AllowExternal
from padamo.lazy_array_operations import LazyArrayOperation
from padamo.lazy_array_operations.base import normalize_slice
from padamo.lazy_array_operations.base import AutoRequest
from padamo.utilities.dual_signal import Signal
from .disabled_node_arrays import DummyArray


@nb.njit(nb.float64[:](nb.float64[:], nb.int64, nb.float64))
def moving_quantile_1d(src, window, quant):
    l_ = src.shape[0]
    res = np.zeros((l_-window+1,))
    for i in range(l_-window+1):
        res[i] = np.quantile(src[i:i+window], quant)
    return res


@nb.njit(nb.float64[:, :, :](nb.float64[:, :, :], nb.int64, nb.float64), parallel=True)
def moving_quantile_3d(src, window, quant):
    l, w, h = src.shape
    res = np.zeros((l-window+1, w, h))
    for i in nb.prange(w):
        for j in nb.prange(h):
            res[:, i, j] = moving_quantile_1d(src[:, i, j], window, quant)
    return res


@nb.njit(nb.float64[:](nb.float64[:], nb.int64))
def moving_mean_1d(src, window):
    l_ = src.shape[0]
    res = np.zeros((l_-window+1,))
    for i in range(l_-window+1):
        res[i] = np.mean(src[i:i+window])
    return res


@nb.njit(nb.float64[:, :, :](nb.float64[:, :, :], nb.int64), parallel=True)
def moving_mean_3d(src, window):
    l, w, h = src.shape
    res = np.zeros((l-window+1, w, h))
    for i in nb.prange(w):
        for j in nb.prange(h):
            res[:, i, j] = moving_mean_1d(src[:, i, j], window)
    return res


class LazyMovingQuantile(LazyArrayOperation):
    def __init__(self, source: LazyArrayOperation, window: int, quantile=0.5):
        self.source = source
        self.window = window
        self.quantile = quantile

    def request_single(self, i: int):
        src_data = self.source.request_data(slice(i, i + self.window))
        return np.quantile(src_data, self.quantile, axis=0)

    def request_slice(self, interesting_slice):
        shape = self.shape()
        # print("MM source shape", shape)
        l_ = shape[0]
        start, end, step = normalize_slice(l_, interesting_slice)
        src_end = end + self.window-1
        src_part = self.source.request_data(slice(start, src_end))
        mm = moving_quantile_3d(src_part.astype(float), self.window, self.quantile)
        res = mm[0:end - start:step]
        return res

    def shape(self):
        src_shape = self.source.shape()
        l_ = src_shape[0]-self.window+1
        if l_ <= 0:
            raise ValueError("Sliding window size cannot be larger than array length")
        return (l_,)+src_shape[1:]


class LazyMovingMean(LazyArrayOperation):
    def __init__(self, source: LazyArrayOperation, window: int):
        self.source = source
        self.window = window

    def request_single(self, i: int):
        src_data = self.source.request_data(slice(i, i + self.window))
        return np.mean(src_data, axis=0)

    def request_slice(self, interesting_slice):
        shape = self.shape()
        # print("MM source shape", shape)
        l_ = shape[0]
        start, end, step = normalize_slice(l_, interesting_slice)
        src_end = end + self.window-1
        src_part = self.source.request_data(slice(start, src_end))
        mm = moving_mean_3d(src_part.astype(float), self.window)
        res = mm[0:end - start:step]
        return res

    def shape(self):
        src_shape = self.source.shape()
        l_ = src_shape[0]-self.window+1
        if l_ <= 0:
            raise ValueError("Sliding window size cannot be larger than array length")
        return (l_,)+src_shape[1:]


class LazyAbs(LazyArrayOperation):
    def __init__(self, source: LazyArrayOperation):
        self.source = source

    def request_data(self, interesting_slices):
        return np.abs(self.source.request_data(interesting_slices))

    def shape(self):
        return self.source.shape()



class MovingMeanNode(Node):
    INPUTS = {
        "source": SIGNAL,
        #"window": INTEGER
    }

    CONSTANTS = {
        "window":AllowExternal(10)
    }

    OUTPUTS = {
        "background": SIGNAL,
        "detail": SIGNAL
    }
    REPR_LABEL = "Moving mean"
    LOCATION = "/Signal processing/Moving mean"

    @classmethod
    def on_constants_update(cls,graphnode):
        win = graphnode.get_constant("window")
        graphnode.set_title(cls.REPR_LABEL+ f" ({win})")

    def calculate(self, globalspace: dict) -> dict:
        source: Signal = self.require("source")
        window = self.constants["window"]
        offset = window//2
        back_cut = window-offset
        source_space = source.space
        source_time = source.time

        moving_median_space = LazyMovingMean(source_space, window)
        cutoff = source_space[offset:-back_cut+1]
        print("OFFSET", offset, back_cut)
        print("CUTOFF", cutoff.shape())
        # assert cutoff.shape()==moving_median.shape()
        detail_space = cutoff - moving_median_space

        time_ = source_time[offset:-back_cut+1]
        trigger_ = source.get_trigger()[offset:-back_cut+1]

        detail = Signal(detail_space,time_,trigger_)
        moving_median = Signal(moving_median_space,time_,trigger_)

        return dict(detail=detail, background=moving_median)


class MovingMedianNode(Node):
    INPUTS = {
        "source": SIGNAL,
        #"window": INTEGER
    }

    CONSTANTS = {
        "window":AllowExternal(10),
        "quantile":0.5
    }

    OUTPUTS = {
        "background": SIGNAL,
        "detail": SIGNAL
    }
    REPR_LABEL = "Moving quantile"
    LOCATION = "/Signal processing/Moving quantile"

    @classmethod
    def on_constants_update(cls,graphnode):
        win = graphnode.get_constant("window")
        graphnode.set_title(cls.REPR_LABEL+ f" ({win})")

    def calculate(self, globalspace: dict) -> dict:
        source: Signal = self.require("source")
        window = self.constants["window"]
        offset = window//2
        back_cut = window-offset
        source_space = source.space
        source_time = source.time

        moving_median_space = LazyMovingQuantile(source_space, window, self.constants["quantile"])
        cutoff = source_space[offset:-back_cut+1]
        print("OFFSET", offset, back_cut)
        print("CUTOFF", cutoff.shape())
        # assert cutoff.shape()==moving_median.shape()
        detail_space = cutoff - moving_median_space

        time_ = source_time[offset:-back_cut+1]
        trigger_ = source.get_trigger()[offset:-back_cut+1]

        detail = Signal(detail_space,time_,trigger_)
        moving_median = Signal(moving_median_space,time_,trigger_)

        return dict(detail=detail, background=moving_median)

SIGMA_TO_MAD_COEFF = 0.6744897501960818


class MovingMADNormalizeNode(Node):
    INPUTS = {
        "source": SIGNAL,
        #"window": INTEGER
    }

    CONSTANTS = {
        "window": AllowExternal(10),
        "gauss_mode":True
    }

    OUTPUTS = {
        "normalized": SIGNAL,
    }

    @classmethod
    def on_constants_update(cls,graphnode):
        win = graphnode.get_constant("window")
        graphnode.set_title(cls.REPR_LABEL + f" ({win})")

    REPR_LABEL = "Moving median normalize"
    LOCATION = "/Signal processing/Moving median normalize"

    def calculate(self, globalspace:dict) ->dict:
        source:Signal = self.require("source")
        source_space = source.space
        source_time = source.time

        window = self.constants["window"]
        offset = window // 2
        back_cut = window - offset
        absed = LazyAbs(source_space)
        moving_median_space = LazyMovingQuantile(absed, window)

        time_ = source_time[offset:-back_cut+1]
        trigger_ = source.get_trigger()[offset:-back_cut+1]

        cutoff = source_space[offset:-back_cut + 1]
        if self.constants["gauss_mode"]:
            coeff = SIGMA_TO_MAD_COEFF
        else:
            coeff = 1.0
        norm_space = coeff * cutoff/moving_median_space
        norm = Signal(norm_space,time_,trigger_)
        return dict(normalized=norm)

class LazyFlashSuppressor(LazyArrayOperation):
    def __init__(self, source:LazyArrayOperation):
        self.source = source

    def request_single(self,i:int):
        raw = self.source.request_data(i)
        corr = np.median(raw)
        return raw - corr

    def request_slice(self,s:slice):
        raw = self.source.request_data(s)
        full_dim = len(self.shape())
        axes = list(range(1, full_dim))
        flashes = np.median(raw, axis=tuple(axes))
        flashes = np.expand_dims(flashes, axis=(1, 2))
        return raw-flashes

    def shape(self):
        return self.source.shape()


@nb.njit()
def block_median(src,wb,hb):
    w,h = src.shape
    res = np.zeros(shape=src.shape)
    for i in range(0,w,wb):
        for j in range(0, h, hb):
            median = np.median(src[i:i+wb, j:j+hb])
            res[i:i+wb, j:j+hb] = median
    return res
    

class FlashSuppressorNode(Node):
    INPUTS = {
        "signal":SIGNAL
    }
    OUTPUTS = {
        "filtered": SIGNAL
    }
    REPR_LABEL = "Flash suppress"
    LOCATION = "/Signal processing/Flash suppression"

    def calculate(self, globalspace:dict) ->dict:
        #globalspace["chosen_detector_config"]
        signal:Signal = self.require( "signal")
        signal_space = signal.space
        signal_time = signal.time
        filtered_space = LazyFlashSuppressor(signal_space)
        return dict(filtered=Signal(filtered_space,signal_time,signal.trigger))


class LazyMinSuppressor(LazyArrayOperation):
    def __init__(self, source:LazyArrayOperation, thresh):
        self.source = source
        self.thresh = thresh

    def request_data(self, interesting_slices):
        raw = self.source.request_data(interesting_slices)
        return np.where(raw > self.thresh, raw,0)

    def shape(self):
        return self.source.shape()

class LazyWindowCutter(LazyArrayOperation):
    def __init__(self, window, centers, length):
        self.centers = centers
        self.window = window
        self._add_dims = tuple(i+1 for i in range(len(centers.shape)))
        self._start = np.expand_dims(self.centers-window//2,0)
        self._end = np.expand_dims(self.centers+window-window//2,0)
        self.length = length

    def shape(self):
        return (self.length,)+self.centers.shape

    def request_single(self,i:int):
        res = (i <= self._end[0]) & (i >= self._start[0])
        res = res.astype(int)
        res: np.ndarray
        # print(res)
        return res

    def request_slice(self,s:slice):
        start, end, step = normalize_slice(self.shape()[0], s)
        x = np.arange(start, end, step)
        x = np.expand_dims(x, self._add_dims)
        res = (x <= self._end) & (x >= self._start)
        # print(res)
        return res.astype(int)


class SinglePeakWindowNode(Node):
    INPUTS = {
        "signal":SIGNAL,
        "window":INTEGER
    }
    OUTPUTS = {
        "signal":SIGNAL
    }
    LOCATION = "/Signal processing/Single peak Window"
    REPR_LABEL = "Single peak Window"

    def calculate(self, globalspace:dict) ->dict:
        signal_in = self.require("signal")
        window = self.require("window")
        centers = np.argmax(signal_in.space.request_all_data(),axis=0)
        length = signal_in.space.shape()[0]
        cutter = LazyWindowCutter(window=window, centers=centers,length=length)

        signal_out_space = signal_in.space*cutter
        return dict(signal=Signal(signal_out_space, signal_in.time, signal_in.trigger))


class ThresholdSuppresorNode(Node):
    INPUTS = {
        "signal":SIGNAL,
        "threshold":FLOAT
    }
    OUTPUTS = {
        "signal":SIGNAL
    }
    LOCATION = "/Signal processing/Threshold suppression"
    REPR_LABEL = "Threshold suppress"

    def calculate(self, globalspace:dict) ->dict:
        signal_in = self.require("signal")
        thresh = self.require("threshold")
        signal_in_space = signal_in.space
        signal_out_space = LazyMinSuppressor(signal_in_space, thresh)
        return dict(signal=Signal(signal_out_space,signal_in.time,signal_in.trigger))




class LazyTimeSubtractor(LazyArrayOperation):
    def __init__(self, src:LazyArrayOperation, value:float):
        self.src = src
        self.value = value

    def shape(self):
        return self.src.shape()

    def request_data(self, interesting_slices):
        x = self.src.request_data(interesting_slices)
        return x-self.value


class LazyTimeMultiplier(LazyArrayOperation):
    def __init__(self, src:LazyArrayOperation, value:float):
        self.src = src
        self.value = value

    def shape(self):
        return self.src.shape()

    def request_data(self, interesting_slices):
        x = self.src.request_data(interesting_slices)
        return x*self.value


class TimeSubtractorNode(Node):
    INPUTS = {
        "signal": SIGNAL,
        "value": FLOAT
    }
    OUTPUTS = {
        "signal": SIGNAL
    }

    LOCATION = "/Signal processing/Time subtract"
    REPR_LABEL = "Time subtract"

    def calculate(self, globalspace: dict) -> dict:
        signal = self.require( "signal")
        value = self.require("value")
        s1 = Signal(signal.space, LazyTimeSubtractor(signal.time,value), signal.trigger)
        return dict(signal=s1)


class TimeMultiplierNode(Node):
    INPUTS = {
        "signal": SIGNAL,
        "value": FLOAT
    }
    OUTPUTS = {
        "signal": SIGNAL
    }

    LOCATION = "/Signal processing/Time multiply"
    REPR_LABEL = "Time Multiply"

    def calculate(self, globalspace: dict) -> dict:
        signal = self.require( "signal")
        value = self.require("value")
        s1 = Signal(signal.space, LazyTimeMultiplier(signal.time,value),signal.trigger)
        return dict(signal=s1)


@nb.njit(nb.float64[:,:](nb.float64[:,:],nb.int64,nb.int64))
def conv_median(a,span_x, span_y):
    res = np.zeros(a.shape)
    for i in range(a.shape[0]):
        i_start = max(i-span_x,0)
        i_end = min(i+span_x,a.shape[0])
        for j in range(a.shape[1]):
            j_start = max(j-span_y,0)
            j_end = min(j+span_y,a.shape[1])
            res[i,j] = np.median(a[i_start:i_end,j_start:j_end])
    return res


@nb.njit(nb.float64[:,:,:](nb.float64[:,:,:],nb.int64,nb.int64),parallel=True)
def conv_median_t(a,span_x, span_y):
    res = np.zeros(a.shape)
    for i in nb.prange(a.shape[0]):
        res[i] = conv_median(a[i],span_x,span_y)
    return res


class LazyMedianConv(LazyArrayOperation):
    def __init__(self, src, span_x, span_y):
        self.src = src
        self.span_x = span_x
        self.span_y = span_y

    def shape(self):
        return self.src.shape()

    def request_single(self,i:int):
        src_i = self.src.request_data(i)
        return conv_median(src_i,self.span_x, self.span_y)

    def request_slice(self,s:slice):
        src_s = self.src.request_data(s)
        return conv_median_t(src_s,self.span_x, self.span_y)

class MedianConvNode(Node):
    INPUTS = {
        "signal": SIGNAL,
    }
    CONSTANTS = {
        "span_x":AllowExternal(1),
        "span_y":AllowExternal(1)
    }
    OUTPUTS = {
        "background":SIGNAL,
        "detail":SIGNAL
    }

    LOCATION = "/Signal processing/Median conv filter"
    REPR_LABEL = "Median conv filter"

    def calculate(self,globalspace:dict) ->dict:
        signal = self.require("signal")
        span_x = self.constants["span_x"]
        span_y = self.constants["span_y"]
        sp = signal.space
        bg = LazyMedianConv(sp, span_x, span_y)
        background = Signal(bg, signal.time)
        detail = Signal(sp-bg, signal.time)
        return dict(background=background,detail=detail)