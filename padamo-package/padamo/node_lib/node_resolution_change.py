import os
import sys

import numpy as np
import psutil

from padamo.lazy_array_operations import LazyArrayOperation
from padamo.lazy_array_operations.slice_combination import normalize_slice
from padamo.node_processing import Node, SIGNAL, INTEGER, AllowExternal
from padamo.utilities.dual_signal import Signal
import numba as nb


@nb.njit()
def reduce_mean0(src, use_sum=False):
    res = np.zeros(shape=(src.shape[1],src.shape[2]))
    for i in range(src.shape[1]):
        for j in range(src.shape[2]):
            if use_sum:
                res[i,j] = np.sum(src[:,i,j])
            else:
                res[i,j] = np.mean(src[:,i,j])
    return res

@nb.njit()
def reduce_resolution(src, scale, use_sum=False):
    tgt_len = src.shape[0]//scale
    res = np.zeros(shape=(tgt_len,src.shape[1],src.shape[2]))
    for i in range(tgt_len):
        res[i] = reduce_mean0(src[i*scale:(i+1)*scale], use_sum)
        #res[i] = np.mean(src[i*scale:(i+1)*scale], axis=0)
    return res


class LazyResolutionChange(LazyArrayOperation):
    def __init__(self, source_array:LazyArrayOperation, scale, use_low_ram=True, use_sum=False):
        self.source = source_array
        self.scale = scale
        self.single_size = None
        self.use_low_ram = use_low_ram
        self.use_sum = use_sum
        if (source_array.shape()[0]%scale)!=0:
            raise ValueError(f"Source array length ({source_array.shape()[0]}) must be dividable by scale ({scale})")

    def _get_max_chunk_size(self):
        if self.single_size is None:
            if not self.shape():
                raise ValueError("Trying to change resolution of empty array.")
            sample = self.source.request_data(0)
            if hasattr(sample, "nbytes"):
                self.single_size = sample.nbytes
            else:
                self.single_size = sys.getsizeof(sample)

        available_mem_bytes = psutil.virtual_memory().available
        available_chunks = max(1, available_mem_bytes//(self.single_size*self.scale))
        return available_chunks

    def request_single(self,i:int):
        start = i * self.scale
        end = start + self.scale
        src = self.source.request_data(slice(start, end))
        if self.use_sum:
            return np.sum(src, axis=0)
        else:
            return np.mean(src, axis=0)

    def request_slice(self,s:slice):
        start, end, step = normalize_slice(self.shape()[0], s)
        length = len(range(start, end, step))
        res = np.zeros(shape=(length,) + self.shape()[1:])
        if step==1:
            # Gallop optimization
            #print("Reduce time speeding up")
            cnt = 0
            if self.use_low_ram:
                max_available_chunks = self._get_max_chunk_size()
            else:
                max_available_chunks = end-start
            #max_available_samples = max_available_chunks*self.scale
            i = start
            while i < end:
                #print(f"\r{i-start}/{end-start}      ", end="")
                i_step = min(end-i,max_available_chunks)
                i_start = i
                i_end = i_start+i_step
                data_part = self.source.request_data(slice(i_start*self.scale,i_end*self.scale))
                reduced = reduce_resolution(data_part,self.scale,self.use_sum)
                cnt_step = reduced.shape[0]
                assert cnt_step == i_step
                res[cnt:cnt+cnt_step] = reduced
                cnt += cnt_step
                i = i_end
                if self.use_low_ram:
                    max_available_chunks = self._get_max_chunk_size()
            #print()
            return res
        else:
            cnt = 0
            for i in range(start, end, step):
                c_start = i * self.scale
                c_end = c_start + self.scale
                src = self.source.request_data(slice(c_start, c_end))
                if self.use_sum:
                    res[cnt] = np.sum(src, axis=0)
                else:
                    res[cnt] = np.mean(src, axis=0)
                cnt += 1
            return res

    def shape(self):
        src_shape = self.source.shape()
        l0 = src_shape[0]//self.scale
        return (l0,)+src_shape[1:]


class ResolutionReductionNode(Node):
    INPUTS = {
        "signal":SIGNAL
    }
    CONSTANTS = {
        "scale":AllowExternal(1000),
        "use_low_ram":True,
        "use_sum":False
    }
    OUTPUTS = {
        "signal":SIGNAL
    }


    REPR_LABEL = "Reduce temporal resolution"
    LOCATION = "/Signal processing/Reduce temporal resolution"

    def calculate(self, globalspace:dict) -> dict:
        signal = self.require("signal")
        scale = self.constants["scale"]
        src_len = signal.length()
        if src_len%scale !=0:
            actual_len = src_len//scale*scale
            print("Signal is misaligned to reduce resolution.")
            print(f"{src_len-actual_len} samples will be cut off.")
            signal = signal[:actual_len]
        spatial = signal.space
        temporal = signal.time
        s_lowered = LazyResolutionChange(spatial, scale, use_low_ram=self.constants["use_low_ram"], use_sum=self.constants["use_sum"])
        t_lowered = temporal[::scale]
        return dict(signal=Signal(s_lowered, t_lowered, signal.get_trigger()[::scale]))
