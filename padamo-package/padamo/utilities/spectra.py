import numpy as np
from numpy.fft import fft, ifft, fftfreq
from .dual_signal import Signal
from typing import Union
from padamo.lazy_array_operations import LazyArrayOperation
from padamo.lazy_array_operations.slice_combination import normalize_slice
from .numba_fft import singular_calculate, multiple_calculate
from .plot import LazyPlotter

class SpectralFilter(object):
    def build(self, frequencies):
        raise NotImplementedError

    def __mul__(self, other):
        return CombinedFilter(self,other)

    def __invert__(self):
        return InvertedFilter(self)

    def __add__(self, other):
        if isinstance(other, float) or isinstance(other,float):
            return OffsetFilter(self,other)
        else:
            raise TypeError("Filter can be offsetted only by float or int")

    def __radd__(self, other):
        return self.__add__(other)

    def __sub__(self, other):
        return self.__add__(-other)


class OffsetFilter(SpectralFilter):
    def __init__(self, inner:SpectralFilter, offset):
        self.inner = inner
        self.offset = offset

    def build(self, frequencies):
        off_freq = frequencies+self.offset
        return self.inner.build(off_freq)


class InvertedFilter(SpectralFilter):
    def __init__(self, a:SpectralFilter):
        self.inner = a

    def build(self, frequencies):
        non_negated = self.inner.build(frequencies)
        return (1-non_negated ** 2) ** 0.5


class CombinedFilter(SpectralFilter):
    def __init__(self,a:SpectralFilter,b:SpectralFilter):
        self.a = a
        self.b = b

    def build(self, frequencies):
        return self.a.build(frequencies)*self.b.build(frequencies)


class ButterworthFilter(SpectralFilter):
    def __init__(self, cutoff_frequency, order=1):
        self.cutoff_frequency = cutoff_frequency
        self.order = order

    def build(self, frequencies):
        normed = frequencies / self.cutoff_frequency
        return 1.0 / (1 + normed**(2*self.order)) ** 0.5


class HardLowPassFilter(SpectralFilter):
    def __init__(self, cutoff_frequency):
        self.cutoff_frequency = cutoff_frequency

    def build(self, frequencies):
        return np.where(np.abs(frequencies) < self.cutoff_frequency,1.0,0.0)


class HardBandPassFilter(SpectralFilter):
    def __init__(self,lower,upper,cutoff=1.0):
        self.lower = lower
        self.upper = upper
        self.cutoff = cutoff

    def build(self, frequencies):
        f = np.abs(frequencies)
        return np.where((f <= self.upper) & (f >= self.lower), self.cutoff, 0.0)

    @staticmethod
    def band(band_frequency, band_width,cutoff=1.0):
        return HardBandPassFilter(band_frequency-band_width/2,band_frequency+band_width/2, cutoff=cutoff)


class DualButterworthBandFilter(SpectralFilter):
    def __init__(self, frequency_l, frequency_r, order_l, order_r):
        left_filter = ButterworthFilter(frequency_l,order_l)
        right_filter = ~ButterworthFilter(frequency_r,order_r)
        self.inner = left_filter*right_filter

    def build(self, frequencies):
        return self.inner.build(frequencies)

    @staticmethod
    def symmetrical_band_filter(frequency, band_width,order):
        frequency_l = frequency-band_width/2
        frequency_r = frequency+band_width/2
        return DualButterworthBandFilter(frequency_l, frequency_r, order, order)


class LazyFilter(LazyArrayOperation):
    def __init__(self,input_signal:Signal, filter_obj:SpectralFilter, window:int):
        self.input_signal = input_signal
        self.filter_obj = filter_obj
        self.window = window

    def request_single(self,i:int):
        return singular_calculate(self.input_signal, i, self.window, self.filter_obj)

    def request_slice(self, interesting_slice):
        shape = self.shape()
        #print("MM source shape", shape)
        l = shape[0]
        start, end, step = normalize_slice(l, interesting_slice)
        src_end = end + self.window-1
        #src_part = self.source.request_data(slice(start, src_end))
        #mm = moving_median_3d(src_part.astype(float), self.window)
        mm = multiple_calculate(self.input_signal,self.filter_obj,self.window,start,src_end)
        res = mm[0:end - start:step]
        return res

    def shape(self):
        src_shape = self.input_signal.space.shape()
        l = src_shape[0]-self.window+1
        if l<=0:
            raise ValueError("Sliding window size cannot be larger than array length")
        return (l,)+src_shape[1:]


class LazyFilterPlotter(LazyPlotter):
    def __init__(self, filter_:LazyFilter, window:int, resolution:float):
        self.filter_ = filter_
        self.window = window
        self.resolution = resolution

    def apply(self,figure, axes):
        freqs = fftfreq(self.window, self.resolution)
        freqs.sort()
        pass_ = self.filter_.build(freqs)
        axes.plot(freqs, pass_)
