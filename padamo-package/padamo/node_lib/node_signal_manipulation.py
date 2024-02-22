from datetime import timedelta, datetime

import numpy as np
import numba as nb

from padamo.lazy_array_operations import LazyArrayOperation
from padamo.lazy_array_operations.slice_combination import normalize_slice
from padamo.node_lib.disabled_node_arrays import DummyArray
from padamo.node_processing import Node, SIGNAL, STRING, INTEGER, ARRAY, AllowExternal,Optional

from padamo.ui_elements.searching import comparing_binsearch
from padamo.ui_elements.datetime_parser import parse_datetimes_dt, datetime_to_unixtime
from padamo.utilities.dual_signal import Signal
from padamo.lazy_array_operations.base import ArrayBinaryOperation


def unixtime_to_datetime(ut):
    ut_integer = int(ut)
    ut_float = ut-ut_integer
    dt_0 = datetime.utcfromtimestamp(ut_integer)
    dt_0 = dt_0 + timedelta(seconds=ut_float)
    return dt_0


class SignalCutTimeNode(Node):
    INPUTS = {
        "signal": SIGNAL,
        "start": STRING,
        "end": STRING
    }

    CONSTANTS = {
        "count_from_end":False
    }

    OUTPUTS = {
        "signal": SIGNAL,
    }

    REPR_LABEL = "Cut signal (time)"
    LOCATION = "/Signal manipulation/Cut signal (time)"

    def calculate(self, globalspace:dict) ->dict:
        signal = self.require("signal")
        start = self.require( "start", optional=True) or ""
        end = self.require( "end", optional=True) or ""
        src_time = signal.time.activate()
        if len(src_time.shape)!=1:
            print("TIME WARNING", src_time.shape)
        if self.constants["count_from_end"]:
            init_dt = float(src_time[-1])
        else:
            init_dt = float(src_time[0])
        print("INIT DT:", init_dt)
        init_dt = unixtime_to_datetime(init_dt)

        start_dt = parse_datetimes_dt(start,init_dt)
        end_dt = parse_datetimes_dt(end,start_dt)

        start_dt = datetime_to_unixtime(start_dt)
        end_dt = datetime_to_unixtime(end_dt)
        if end_dt <= start_dt:
            end_dt = start_dt+1
        start_i = comparing_binsearch(src_time,start_dt)
        end_i = comparing_binsearch(src_time, end_dt)
        return dict(signal=signal[start_i:end_i])

class SignalCutNode(Node):
    INPUTS = {
        "signal": SIGNAL,
        #"start":INTEGER,
        #"end":INTEGER
    }

    CONSTANTS = {
        "start":Optional(AllowExternal(0)),
        "end":Optional(AllowExternal(1))
    }

    OUTPUTS = {
        "signal": SIGNAL,
    }

    REPR_LABEL = "Cut signal"
    LOCATION = "/Signal manipulation/Cut signal"

    def calculate(self, globalspace:dict) ->dict:
        signal = self.require("signal")
        # start = self.require( "start", optional=True)
        # end = self.require( "end", optional=True)
        start = self.constants["start"]
        end = self.constants["end"]
        return dict(signal=signal[start:end])


def get_reach_index_low(signal_a:Signal,signal_b:Signal):
    a_start_time = signal_a.time.request_data(0)
    b_start_time = signal_b.time.request_data(0)
    if b_start_time>a_start_time:
        return 0

    for b_index in range(signal_b.length()):
        b_new_start_time = signal_b.time.request_data(b_index)
        if a_start_time==b_new_start_time:
            return b_index

    return 0

def get_reach_index_high(signal_a:Signal,signal_b:Signal):
    a_start_time = signal_a.time.request_data(-1)
    b_start_time = signal_b.time.request_data(-1)
    if a_start_time>b_start_time:
        return None

    for b_index in range(signal_b.length()-1,-1,-1):
        b_new_start_time = signal_b.time.request_data(b_index)
        #print(a_start_time,b_new_start_time)
        if a_start_time == b_new_start_time:
            return b_index+1
        elif a_start_time>b_new_start_time:
            raise ValueError("Cannot sync data")
    return None

def get_ratio_indices_low(signal_a:Signal,signal_b:Signal):
    b_offset = get_reach_index_low(signal_a,signal_b)
    #print("---")
    a_offset = get_reach_index_low(signal_b,signal_a)
    return a_offset, b_offset

def get_ratio_indices_high(signal_a:Signal,signal_b:Signal):
    b_offset = get_reach_index_high(signal_a,signal_b)
    a_offset = get_reach_index_high(signal_b,signal_a)
    return a_offset, b_offset


class TriggerExchangeNode(Node):
    INPUTS = {
        "main_signal":SIGNAL,
        "trigger_provider":SIGNAL
    }
    OUTPUTS = {
        "result_signal":SIGNAL
    }

    REPR_LABEL = "Trigger exchange"
    LOCATION = "/Signal manipulation/Trigger exchange"

    def calculate(self,globalspace:dict) ->dict:
        primary = self.require("main_signal")
        provider = self.require("trigger_provider")

        a_start, b_start = get_ratio_indices_low(primary,provider)
        primary = primary[a_start:]
        provider = provider[b_start:]
        assert primary.time.request_data(0)==provider.time.request_data(0)

        a_end, b_end = get_ratio_indices_high(primary,provider)
        primary = primary[:a_end]
        provider = provider[:b_end]

        assert primary.time.request_data(0)==provider.time.request_data(0)

        synth = Signal(primary.space, primary.time, provider.trigger)
        return dict(result_signal=synth)


class LazyTriggerInverter(LazyArrayOperation):
    def __init__(self, source:LazyArrayOperation):
        self.source = source

    @staticmethod
    def mux_none(item):
        if item is None:
            return None
        return LazyTriggerInverter(item)

    def shape(self):
        return self.source.shape()

    def request_data(self, interesting_slice):
        src = self.source.request_data(interesting_slice)
        src = np.logical_not(src)
        return src


class InvertedTriggerNode(Node):
    INPUTS = {
        "signal":SIGNAL
    }
    OUTPUTS = {
        "signal_inv":SIGNAL
    }

    LOCATION = "/Signal manipulation/Invert trigger"
    REPR_LABEL = "Invert trigger"

    def calculate(self,globalspace:dict) ->dict:
        signal = self.require("signal")
        t = LazyTriggerInverter.mux_none(signal.trigger)
        return dict(signal_inv=Signal(signal.space, signal.time,t))



class LazyTriggerMarginalize(LazyArrayOperation):
    def __init__(self, src):
        self.src = src

    def shape(self):
        return self.src.shape()[0],

    def request_single(self, i):
        data = self.src.request_data(i)
        return np.logical_or.reduce(data)

    def request_slice(self,s:slice):
        data = self.src.request_data(s)
        s = len(self.src.shape())
        axes = tuple(range(1,s))
        dat = np.logical_or.reduce(data,axis=axes)
        return dat


class LazyTriggersAnd(LazyArrayOperation):
    def __init__(self,a: LazyArrayOperation,b: LazyArrayOperation, b_is_first=False):
        assert a.shape() == b.shape()
        self.a = a
        self.b = b
        self.b_is_first = b_is_first

    def shape(self):
        return self.a.shape()

    def request_data(self, interesting_slices):
        if self.b_is_first:
            a_src = self.b
            b_src = self.a
        else:
            a_src = self.a
            b_src = self.b

        a_res = a_src.request_data(interesting_slices)
        if not a_res.any():
            return a_res
        b_res = b_src.request_data(interesting_slices)
        return np.logical_and(a_res,b_res)


class TriggersAnd(Node):
    INPUTS = {
        "primary":SIGNAL,
        "secondary":SIGNAL,
    }
    CONSTANTS = {
        "swap_arguments":False
    }
    OUTPUTS = {
        "and_triggered":SIGNAL
    }

    LOCATION = "/Signal manipulation/Combine triggers"
    REPR_LABEL = "Combine triggers"

    def calculate(self,globalspace:dict) ->dict:
        a = self.require("primary")
        b = self.require("secondary")
        assert a.time.request_data(0) == b.time.request_data(0)
        assert a.time.request_data(-1) == b.time.request_data(-1)

        if a.trigger is None or b.trigger is None:
            trig = None
        else:
            trig_a = LazyTriggerMarginalize(a.trigger)
            trig_b = LazyTriggerMarginalize(b.trigger)
            trig = LazyTriggersAnd(trig_a,trig_b,self.constants["swap_arguments"])
        space = a.space
        time = a.time
        synth = Signal(space,time,trig)
        return dict(and_triggered=synth)


@nb.njit
def deconvolve(x,window):
    res = np.full(shape=x.shape,fill_value=False)
    for i in range(x.shape[0]):
        start = i-window//2
        start = max(start,0)
        end = start+window
        end = min(end,x.shape[0])
        res[i] = x[start:end].any()
    return res


class LazyTriggerExpander(LazyArrayOperation):
    def __init__(self, source:LazyArrayOperation,window):
        assert len(source.shape())==1
        self.source = source
        self.window = window

    def shape(self):
        return self.source.shape()

    def request_single(self,i:int):
        start = i-self.window//2
        end = start+self.window
        start = max(start, 0)
        end = min(end, self.shape()[0])
        data = self.source.request_data(slice(start,end))
        return np.logical_or.reduce(data,axis=0)

    def request_slice(self,s:slice):
        shape = self.shape()
        start,end,step = normalize_slice(shape[0],s)

        desired_start = start-self.window//2
        desired_end = end-self.window//2+self.window
        actual_start = max(desired_start,0)
        actual_end = min(desired_end,shape[0])
        start_cut = self.window//2-(actual_start-desired_start)
        end_cut = self.window-self.window//2-(desired_end-actual_end)
        if end_cut==0:
            end_cut = None
        else:
            end_cut = -end_cut

        data = self.source.request_data(slice(actual_start,actual_end))
        deconvolved = deconvolve(data,self.window)
        res = deconvolved[start_cut:end_cut:step]
        assert len(res) == len(range(start,end,step ))
        return res

class TriggerExpand(Node):
    INPUTS = {
        "signal_in":SIGNAL,
    }
    CONSTANTS = {
        "window":AllowExternal(128)
    }
    OUTPUTS = {
        "signal_out":SIGNAL
    }

    LOCATION = "/Signal manipulation/Expand trigger"
    REPR_LABEL = "Expand trigger"

    def calculate(self,globalspace:dict) ->dict:
        signal = self.require("signal_in")
        res = signal.clone()
        if res.trigger is not None:
            res.trigger = LazyTriggerExpander(res.trigger,self.constants["window"])
        return dict(signal_out=res)


@nb.njit()
def signal_mask(src, mask):
    res = np.zeros(shape=src.shape)
    for i in range(res.shape[0]):
        for j in range(res.shape[1]):
            for k in range(res.shape[2]):
                if mask[j,k]:
                    res[i,j,k] = src[i,j,k]
    return res


class LazySilencer(LazyArrayOperation):
    def __init__(self, source, mask):
        self.source = source
        self.mask = mask.request_all_data().astype(float)
        pix = source.shape()[1:]
        # if mask.shape != pix:
        #     raise ValueError(f"Shapes mismatch {mask.shape}!= {pix}")
        assert self.mask.shape==source.shape()[1:]

    def shape(self):
        return self.source.shape()

    def request_single(self,i:int):
        src_slice = self.source.request_data(i).astype(float)[:]
        mask = self.mask
        src_slice[np.logical_not(mask)] = 0
        return src_slice

    def request_slice(self,s:slice):
        src_slice = self.source.request_data(s).astype(float)
        mask = self.mask
        return signal_mask(src_slice.astype(float), mask)


class SilencerNode(Node):
    INPUTS = {
        "signal":SIGNAL,
        "mask":ARRAY,
    }
    OUTPUTS = {
        "signal":SIGNAL
    }

    LOCATION = "/Signal manipulation/Mask signals"
    REPR_LABEL = "Mask signals"

    def calculate(self,globalspace:dict) ->dict:
        signal = self.require("signal")
        mask = self.require("mask")
        signal = signal.clone()
        signal.space = LazySilencer(signal.space,mask)
        return dict(signal=signal)
