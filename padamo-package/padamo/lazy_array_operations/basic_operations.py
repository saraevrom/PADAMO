from .base import LazyArrayOperation, slice_t

class ConstantArray(LazyArrayOperation):
    def __init__(self, source):
        self.source = source

    def request_data(self, interesting_slices:slice_t):
        return self.source[interesting_slices]

    def shape(self):
        return self.source.shape
