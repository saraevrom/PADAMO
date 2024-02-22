import matplotlib.pyplot as plt
import numpy as np
from numpy.fft import fft, fftfreq
from matplotlib.colors import Normalize
from numpy.lib.stride_tricks import sliding_window_view

from padamo.lazy_array_operations import LazyArrayOperation
from padamo.utilities.dual_signal import Signal
from padamo.ui_elements.plotter import Plotter, PLOT_COLORMAP
from padamo.ui_elements.plotter import LOWER_EDGES, PIXEL_SIZE
from mpl_toolkits.axes_grid1 import make_axes_locatable


class SpectraPlotter(Plotter):
    def __init__(self,master):
        super().__init__(master)
        self.colorbar = None
        self.norm = None
        self.axes.set_title("Spectra")
        self.colorbar = None
        self.norm = None

    def plot_spectra(self,spatial, temporal , channels, levels):
        self.axes: plt.Axes
        self.axes.clear()
        self.axes.set_title("Spectra")
        lightcurve = np.sum(spatial, axis=(1, 2)).astype(float)
        spectra_source = sliding_window_view(lightcurve,channels)
        print("SPECTRA SOURCE", spectra_source.shape)
        times = temporal[channels//2: -channels + channels//2 + 1]
        #times = signal.time.request_data(slice(channels//2, -channels + channels//2 + 1))
        #print("TIME (SP) raw", times)
        if len(times.shape)>1:
            times = times[:,0]

        print("TIME (SP)", times)
        resolution = times[1]-times[0]
        print("RESOLUTION", resolution)
        spectra = np.abs(fft(spectra_source, axis=-1))*2/channels
        freqs = fftfreq(channels, resolution)


        freqs_sort = np.argsort(freqs)
        freqs = freqs[freqs_sort]
        spectra = spectra[:,freqs_sort]

        sel = freqs>=0
        freqs = freqs[sel]
        spectra = spectra[:,sel]

        # plt.plot(freqs, spectra[0, :])
        # plt.show()

        low = np.min(spectra)
        high = np.max(spectra)

        if self.norm is None:
            self.norm = Normalize(low, high)
        else:
            # Magic: pyplot requires to assign twice
            self.norm.vmin = low
            self.norm.vmin = low
            self.norm.vmax = high
            self.norm.vmax = high

        if self.colorbar is None:
            self.colorbar = self.figure.colorbar(plt.cm.ScalarMappable(norm=self.norm, cmap=PLOT_COLORMAP),
                                                 orientation='vertical', ax=self.axes)

        times = (1000*times).astype('datetime64[ms]')
        X, Y = np.meshgrid(times, freqs, indexing="ij")
        self.axes.contourf(X, Y, spectra, levels=levels)
        self.axes.relim()
        self.toolbar.update()
        self.draw()
        print("Spectrograph ready")
