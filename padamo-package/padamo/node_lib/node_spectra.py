from padamo.node_processing import Node, FLOAT, INTEGER, SIGNAL, PLOT, AllowExternal

from padamo.utilities.plot import LazyPlotter
from padamo.utilities.spectra import DualButterworthBandFilter, ButterworthFilter, LazyFilter, HardLowPassFilter, HardBandPassFilter
from padamo.utilities.spectra import LazyFilterPlotter
from padamo.utilities.dual_signal import Signal
from padamo.node_processing import PortType


FILTER = PortType.create_porttype("filter", "#FFFF00")

class ButterworthPassNode(Node):
    INPUTS = {
        "cutoff_frequency": FLOAT,
        "order": INTEGER
    }

    OUTPUTS = {
        "filter": FILTER
    }
    REPR_LABEL = "Butterworth low pass filter"
    LOCATION = "/Spectral Filters/Butterworth low pass filter"

    def calculate(self, globalspace:dict) ->dict:
        freq = self.require( "cutoff_frequency")
        order = self.require( "order", optional=True) or 1
        return dict(filter=ButterworthFilter(freq, order))


class HardLowPassNode(Node):
    INPUTS = {
        "cutoff_frequency": FLOAT,
    }

    OUTPUTS = {
        "filter": FILTER
    }
    REPR_LABEL = "Hard cutoff low pass filter"
    LOCATION = "/Spectral Filters/Hard cutoff low pass filter"

    def calculate(self, globalspace: dict) -> dict:
        freq = self.require( "cutoff_frequency")
        return dict(filter=HardLowPassFilter(freq))

class HardBandPassNode(Node):
    INPUTS = {
        "frequency": FLOAT,
        "band_width": FLOAT,
        "cutoff": FLOAT
    }

    OUTPUTS = {
        "filter": FILTER
    }
    REPR_LABEL = "Hard band pass"
    LOCATION = "/Spectral Filters/Hard Band Pass filter"

    def calculate(self, globalspace: dict) -> dict:
        freq = self.require( "frequency")
        band = self.require( "band_width")
        cutoff = self.require("cutoff",True) or 1.0
        return dict(filter=HardBandPassFilter.band(freq, band,cutoff))

class FilterNegatorNode(Node):
    INPUTS = {
        "input_filter":FILTER
    }
    OUTPUTS = {
        "output_filter":FILTER
    }
    REPR_LABEL = "Filter negate"
    LOCATION = "/Spectral Filters/Filter negate"

    def calculate(self, globalspace:dict) ->dict:
        filter_ = self.require("input_filter")
        return dict(output_filter=~filter_)


class CombineFilterNode(Node):
    INPUTS = {
        "a": FILTER,
        "b": FILTER,
    }
    OUTPUTS = {
        "combined": FILTER
    }
    REPR_LABEL = "Combine filters"
    LOCATION = "/Spectral Filters/Combine filters"

    def calculate(self, globalspace:dict) ->dict:
        a = self.require("a")
        b = self.require("b")
        return dict(combined=a*b)


class ButterworthBandPassNode(Node):
    INPUTS = {
        "frequency":FLOAT,
        "band_width":FLOAT,
        "order":INTEGER
    }

    OUTPUTS = {
        "filter":FILTER
    }
    REPR_LABEL = "Butterworth band pass"
    LOCATION = "/Spectral Filters/Dual Butterworth Band Pass filter"

    def calculate(self, globalspace:dict) ->dict:
        freq = self.require("frequency")
        band = self.require("band_width")
        order = self.require("order", optional=True) or 1
        return dict(filter=DualButterworthBandFilter.symmetrical_band_filter(freq, band, order))

class FreqFilterNode(Node):
    INPUTS = {
        "signal":SIGNAL,
        "filter":FILTER,
        "window":INTEGER
    }
    CONSTANTS = {
        "block": False
    }
    OUTPUTS = {
        "filtered":SIGNAL
    }

    REPR_LABEL = "Frequency filter"
    LOCATION = "/Spectral Filters/Frequency filter"

    def calculate(self, globalspace:dict) ->dict:
        signal = self.require( "signal")
        filter_ = self.require( "filter")
        if self.constants["block"]:
            filter_ = ~filter_
        window = self.require( "window")
        filtered_spatial = LazyFilter(signal, filter_, window)
        length = signal.time.shape()[0]
        filtered_temporal = signal.time[window//2: length-window+window//2+1]
        return dict(filtered=Signal(filtered_spatial, filtered_temporal))


class FilterCurve(Node):
    INPUTS = {
        "filter":FILTER
    }
    CONSTANTS = {
        "window":AllowExternal(10),
        "resolution":AllowExternal(0.001)
    }
    OUTPUTS = {
        "plot":PLOT
    }
    LOCATION = "/Spectral Filters/IO/Plot frequency curve"
    REPR_LABEL = "Plot frequency curve"

    def calculate(self,globalspace:dict) ->dict:
        filter_ = self.require("filter")
        resolution = self.constants["resolution"]
        window = self.constants["window"]
        return dict(plot=LazyFilterPlotter(filter_,window,resolution))