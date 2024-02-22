import numba as nb
import numpy as np
from padamo.node_processing import Node, ARRAY, SIGNAL, FLOAT, AllowExternal
from padamo.lazy_array_operations import LazyArrayOperation
from padamo.lazy_array_operations.basic_operations import ConstantArray
from padamo.utilities.dual_signal import Signal

SIGMA_TO_MAD_COEFF = 0.6744897501960818


@nb.njit(nb.float64[:,:,:](nb.float64[:,:,:],nb.float64[:,:]))
def ff_divide(a,b):
    r = np.zeros(a.shape)
    for k in range(a.shape[0]):
        for i in range(a.shape[1]):
            for j in range(a.shape[2]):
                if b[i,j] != 0:
                    r[k,i,j] = a[k,i,j]/b[i,j]
    return r


class LazyFFDivider(LazyArrayOperation):
    def __init__(self, source, divider):
        self.source = source
        self.divider = divider.request_all_data().astype(float)
        assert self.divider.shape==source.shape()[1:]

    def shape(self):
        return self.source.shape()

    def request_single(self,i:int):
        src_slice = self.source.request_data(i).astype(float)
        divider = self.divider
        res = np.zeros(src_slice.shape)
        np.divide(src_slice,divider, out=res, where=(divider!=0))
        return res

    def request_slice(self,s:slice):
        src_slice = self.source.request_data(s).astype(float)
        divider = self.divider
        return ff_divide(src_slice, divider)

    # def request_data(self, interesting_slices):
    #     src_slice = self.source.request_data(interesting_slices).astype(float)
    #     divider = self.divider.request_all_data().astype(float)
    #     if src_slice.shape == divider.shape:
    #         res = np.zeros(src_slice.shape)
    #         np.divide(src_slice,divider, out=res, where=(divider!=0))
    #         return res
    #     else:
    #         assert len(src_slice.shape)>len(divider.shape)
    #         return ff_divide(src_slice.astype(float),divider)


@nb.njit(nb.float64[:,:,:](nb.float64[:,:,:],nb.float64[:,:]))
def ff_subtract(a,b):
    r = np.zeros(a.shape)
    for k in range(a.shape[0]):
        for i in range(a.shape[1]):
            for j in range(a.shape[2]):
                if b[i,j] != 0:
                    r[k,i,j] = a[k,i,j]/b[i,j]
    return r


class LazyFFSubtractor(LazyArrayOperation):
    def __init__(self, source, subtractor):
        self.source = source
        self.subtractor = subtractor.request_all_data().astype(float)
        assert self.subtractor.shape==source.shape()[1:]

    def shape(self):
        return self.source.shape()

    def request_single(self,i:int):
        src_slice = self.source.request_data(i).astype(float)
        subtractor = self.subtractor
        return src_slice - subtractor

    def request_slice(self,s:slice):
        src_slice = self.source.request_data(s).astype(float)
        subtractor = self.subtractor
        return ff_subtract(src_slice.astype(float),subtractor)

    # def request_data(self, interesting_slices):
    #     src_slice = self.source.request_data(interesting_slices).astype(float)
    #     subtractor = self.subtractor.request_all_data().astype(float)
    #     if src_slice.shape == subtractor.shape:
    #         return src_slice - subtractor
    #     else:
    #         assert len(src_slice.shape)>len(subtractor.shape)
    #         return ff_subtract(src_slice.astype(float),subtractor)


class FFDividerNode(Node):
    INPUTS = {
        "signal":SIGNAL,
        "divider":ARRAY
    }
    OUTPUTS = {
        "signal":SIGNAL
    }
    LOCATION = "/Flat fielding/Divide signal"
    REPR_LABEL = "Divide signal"

    def calculate(self, globalspace:dict) ->dict:
        signal_in = self.require("signal")
        divider = self.require("divider")
        signal_in_space = signal_in.space
        signal_out_space = LazyFFDivider(signal_in_space,divider)
        return dict(signal=Signal(signal_out_space, signal_in.time, signal_in.trigger))


class FFSubtractNode(Node):
    INPUTS = {
        "signal":SIGNAL,
        "subtractor":ARRAY
    }
    OUTPUTS = {
        "signal":SIGNAL
    }
    LOCATION = "/Flat fielding/Subtract signal"
    REPR_LABEL = "Subtract signal"

    def calculate(self, globalspace:dict) ->dict:
        signal_in = self.require("signal")
        subtractor = self.require("subtractor")
        signal_in_space = signal_in.space
        signal_out_space = LazyFFSubtractor(signal_in_space,subtractor)
        return dict(signal=Signal(signal_out_space, signal_in.time, signal_in.trigger))


class SignalMedian(Node):
    INPUTS = {
        "signal": SIGNAL,
    }
    CONSTANTS = {
        "MAD_mode":False,
        "Normalize":False
    }
    OUTPUTS = {
        "median": ARRAY
    }
    LOCATION = "/Flat fielding/Signal median"
    REPR_LABEL = "Signal median"

    def calculate(self, globalspace:dict) ->dict:
        signal = self.require( "signal")
        spatial = signal.space.request_all_data()
        if self.constants["MAD_mode"]:
            medians = np.median(np.abs(spatial)/SIGMA_TO_MAD_COEFF,axis=0)
        else:
            medians = np.median(spatial,axis=0)

        if self.constants["Normalize"]:
            medians = medians / np.mean(medians)
        medians = ConstantArray(medians)
        return dict(median=medians)


class SignalQuantile(Node):
    INPUTS = {
        "signal": SIGNAL,
    }
    CONSTANTS = {
        "MAD_mode":False,
        "Normalize":False,
        "q":AllowExternal(0.5)
    }
    OUTPUTS = {
        "quantiles": ARRAY
    }
    LOCATION = "/Flat fielding/Signal quantile"
    REPR_LABEL = "Signal quantile"

    def calculate(self, globalspace:dict) ->dict:
        signal = self.require( "signal")
        spatial = signal.space.request_all_data()
        q = self.constants["q"]
        if self.constants["MAD_mode"]:
            quants = np.quantile(np.abs(spatial)/SIGMA_TO_MAD_COEFF,q,axis=0)
        else:
            quants = np.quantile(spatial,q,axis=0)

        if self.constants["Normalize"]:
            quants = quants / np.mean(quants)
        quants = ConstantArray(quants)
        return dict(quantiles=quants)


@nb.njit()
def bin_ff(source, bin_width, threshold, max_signal):
    length = len(source)
    #max_signal = np.max(source)
    bins_count = int(max_signal/bin_width)+1
    bins = np.zeros(shape=(bins_count,))
    for i in range(length):
        if source[i] >= 0:
            bin_id = int(source[i]/bin_width)
            bins[bin_id] += 1
    #print("BINS",bins)
    #accum = 0
    for j in range(bins_count):
        #accum += bins[j]
        if bins[j]/length > threshold:
            return j*bin_width
    return 1.0


@nb.njit(parallel=True)
def bin_ff_3d(source, bin_width, threshold):
    max_signal = np.max(source)
    res = np.zeros(shape=(source.shape[1:]))
    for i in nb.prange(source.shape[1]):
        for j in nb.prange(source.shape[2]):
            res[i,j] = bin_ff(source[:,i,j],bin_width=bin_width,threshold=threshold,max_signal=max_signal)
    return res



class SignalFrequencyFF(Node):
    INPUTS = {
        "signal": SIGNAL,
    }
    CONSTANTS = {
        "bin_width": AllowExternal(1.0),
        "threshold": AllowExternal(0.01)
    }
    OUTPUTS = {
        "ff_coefficients": ARRAY
    }
    LOCATION = "/Flat fielding/Signal Frequency FF"
    REPR_LABEL = "Signal Frequency FF"

    def calculate(self,globalspace:dict) -> dict:
        signal = self.require("signal")
        spatial = signal.space.request_all_data()
        threshold = self.constants["threshold"]
        bin_width = self.constants["bin_width"]
        coeffs = bin_ff_3d(spatial,bin_width,threshold)
        print(coeffs)
        return dict(ff_coefficients=ConstantArray(coeffs))




class SignalMean(Node):
    INPUTS = {
        "signal": SIGNAL,
    }
    CONSTANTS = {
        "Normalize":False
    }
    OUTPUTS = {
        "mean": ARRAY
    }
    LOCATION = "/Flat fielding/Signal mean"
    REPR_LABEL = "Signal mean"

    def calculate(self, globalspace:dict) ->dict:
        signal = self.require( "signal")
        spatial = signal.space.request_all_data()
        means = np.mean(spatial,axis=0)
        if self.constants["Normalize"]:
            means = means/np.mean(means)
        means = ConstantArray(means)
        return dict(mean=means)


class ArrayMultiply(Node):
    INPUTS = {
        "signal" : SIGNAL,
    }
    CONSTANTS = {
        "coeff": AllowExternal(1.0)
    }
    OUTPUTS = {
        "multiplied_signal": SIGNAL
    }

    MIN_SIZE = (100, 100)
    LOCATION = "/Flat fielding/Array multiply"
    REPR_LABEL = "Array multiply"

    def calculate(self, globalspace:dict) -> dict:
        signal = self.require("signal")
        space = signal.space*self.constants["coeff"]
        out = Signal(space, signal.time, signal.trigger)
        return dict(multiplied_signal=out)