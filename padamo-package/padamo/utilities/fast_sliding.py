import numpy as np
import numba as nb

ring_spec = [
    ("array", nb.float64[:]),
    ("_length", nb.int64),
    ("postitions", nb.int64[:]),
    ("_start", nb.int64)
]


@nb.experimental.jitclass(ring_spec)
class OrderedRing:
    def __init__(self, array):
        self.array = array
        self._length = array.shape[0]
        self.positions = np.arange(self._length)
        self._start = 0

    def _remap_index(self, i):
        return (i+self._start) % self._length

    def get_item(self, i):
        i1 = self._remap_index(i)
        return self.array[i1]

    def set_item(self, i, v):
        i1 = self._remap_index(i)
        self.array[i1] = v

    def swap_items(self,i,j):
        i1 = self._remap_index(i)
        j1 = self._remap_index(j)
        self.array[i1], self.array[j1] = self.array[j1], self.array[i1]
