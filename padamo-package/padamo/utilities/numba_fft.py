import matplotlib.pyplot as plt
import numpy as np
import numba as nb
from numpy.fft import fft, ifft, fftfreq
from numpy.lib.stride_tricks import sliding_window_view
from .dual_signal import Signal

@nb.njit()
def multiply_signal(freqs, mods):
    res = np.full(shape=freqs.shape, fill_value=0j)
    for k in range(freqs.shape[0]):
        for i in range(freqs.shape[1]):
            for j in range(freqs.shape[2]):
                res[k,i,j] = freqs[k,i,j]*mods[k]
    return res

@nb.njit()
def multiply_signal_last(freqs, mods):
    res = np.full(shape=freqs.shape, fill_value=0j)
    for k in range(freqs.shape[0]):
        for i in range(freqs.shape[1]):
            for j in range(freqs.shape[2]):
                res[k,i,j] = freqs[k,i,j]*mods[j]
    return res

@nb.njit()
def multiply_slided(freqs, mods):
    res = np.full(shape=freqs.shape, fill_value=0j)
    for k in range(freqs.shape[0]):
        for i in range(freqs.shape[1]):
            for j in range(freqs.shape[2]):
                for w in range(freqs.shape[3]):
                    res[k,i,j,w] = freqs[k,i,j,w]*mods[w]
    return res

def singular_calculate(signal:Signal,i,window, filter_):
    src_spatial = signal.space.request_data(slice(i, i + window))
    src_temporal = signal.time.request_data(slice(i, i + window))
    resolution = src_temporal[1]-src_temporal[0]
    src_spectrum = fft(src_spatial, axis=0)
    freqs = fftfreq(src_temporal.shape[0],resolution)
    modulator = filter_.build(freqs)
    # plt.plot(freqs,modulator)
    # plt.show()
    mod_spectrum = multiply_signal(src_spectrum, modulator)
    new_spatial = ifft(mod_spectrum, axis=0)
    return np.real(new_spatial[window//2])

def multiple_calculate(source_signal:Signal, filter_, window, start,src_end):
    signal_arr = source_signal.space.request_data(slice(start, src_end))
    src_temporal = source_signal.time.request_data(slice(start, src_end))
    resolution = src_temporal[1]-src_temporal[0]
    slided = sliding_window_view(signal_arr,window,axis=0)
    res = np.zeros(slided.shape[:-1])
    freqs = fftfreq(window, resolution)
    modulator = filter_.build(freqs)
    # plt.plot(freqs,modulator)
    # plt.show()
    for i in range(slided.shape[0]):
        spectrum = fft(slided[i],axis=-1)
        mod_spectrum = multiply_signal_last(spectrum,modulator)
        r1 = ifft(mod_spectrum,axis=-1)
        res[i] = r1[:,:,window//2]
    return np.real(res)

    # src_spectral = fft(slided, axis=-1)
    # freqs = fftfreq(src_temporal.shape[0], resolution)
    # modulator = filter_.build(freqs)
    # mod_freqs = multiply_slided(src_spectral,modulator)
    # new_spatial = ifft(mod_freqs, axis=-1)
    # new_spatial = new_spatial[:,:,:,window//2]
    # return np.real(new_spatial)