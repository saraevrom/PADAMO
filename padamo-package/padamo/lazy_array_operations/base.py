import typing
import inspect
import warnings

import numpy as np

from .slice_combination import *
from padamo.lazy_array_operations.slice_combination import normalize_slice


class AutoRequest(object):
    def __init__(self, accessor):
        self.accessor = accessor

    def __getitem__(self, item):
        return self.accessor.request_data(item)

    def __len__(self):
        return self.accessor.shape()[0]

    @property
    def shape(self):
        return self.accessor.shape()

class LazyArrayOperation(object):
    def request_data(self, interesting_slices:slice_t):
        if isinstance(interesting_slices,int):
            return self.request_single(interesting_slices)
        elif isinstance(interesting_slices,slice):
            return self.request_slice(interesting_slices)
        elif isinstance(interesting_slices,tuple):
            return self.request_tuple(interesting_slices)
        else:
            raise IndexError(f"Unknown index type {type(interesting_slices)}")

    def request_single(self,i:int):
        raise NotImplementedError

    def request_slice(self,s:slice):
        warnings.warn(message="Request slice should be implemented manually for better performance.")
        start,end,step = normalize_slice(self.shape()[0], s)
        x = [None]*len(range(start,end,step))
        for i in range(start,end,step):
            x[i] = self.request_single(i)
        return np.array(x)

    def request_tuple(self, s:tuple):
        x0 = s[0]
        rest = s[1:]
        s1 = self.request_data(x0)
        if rest:
            if not isinstance(x0, int):
                rest = (slice(None),)+rest
            return s1[rest]
        else:
            return s1

    def shape(self):
        raise NotImplementedError

    def extend(self, other):
        return LazyArrayConcat(self,other)

    def __add__(self, other):
        return ArrayAdd(self,other)

    def __sub__(self, other):
        return ArraySub(self,other)

    def __mul__(self, other):
        if isinstance(other, LazyArrayOperation):
            return ArrayMul(self,other)
        else:
            return ConstantMultiply(self,other)

    def __rmul__(self, other):
        return self.__mul__(other)

    def __truediv__(self, other):
        return ArrayDiv(self,other)

    def __getitem__(self, item):
        new_shape = shape_transform(self.shape(),item)
        if not new_shape:
            return self.request_data(item)
        # curframe = inspect.currentframe()
        # calframe = inspect.getouterframes(curframe, 2)
        # print('caller name:', calframe[1][3])
        return ConstantSlice(self,item)

    def request_all_data(self):
        return self.request_data(slice(None,None,None))

    def __repr__(self):
        return f"LazyOp({type(self).__name__})"

    def activate(self):
        return AutoRequest(self)

    def squeeze_left(self):
        workon = self
        for dim in self.shape():
            if dim==1:
                workon = workon[0]
            else:
                return workon

class LazyArrayConcat(LazyArrayOperation):
    def __init__(self, left:LazyArrayOperation, right:LazyArrayOperation):
        s1 = left.shape()[1:]
        s2 = right.shape()[1:]
        if s1 != s2:
            raise ValueError("Shapes mismatch")
        self.left = left
        self.right = right

    def shape(self):
        lshape = self.left.shape()
        rshape = self.right.shape()
        full_len = lshape[0]+rshape[0]
        return (full_len,)+lshape[1:]

    def request_single(self, i:int):
        lshape = self.left.shape()
        full_shape = self.shape()
        if i < 0:
            i = full_shape[0] - i
        if i < lshape[0]:
            return self.left.request_data(i)
        else:
            return self.right.request_data(i - lshape[0])

    def request_slice(self, s:slice):
        lshape = self.left.shape()
        full_shape = self.shape()
        start, end, step = normalize_slice(full_shape[0], s)
        if end <= lshape[0]:
            #print("Left case",s)
            res = self.left.request_data(s)
            #print("LDATA",res)
            return res
        elif start >= lshape[0]:
            subslice = slice(start - lshape[0], end - lshape[0], step)
            #print("Right case",subslice, self.right)
            res = self.right.request_data(subslice)
            #print("RDATA",res)
            return res
        else:
            if (lshape[0] - start) % step == 0:
                border_arr1 = lshape[0] - start - step
            else:
                border_arr1 = (lshape[0] - start) // step * step

            assert border_arr1<lshape[0]
            border = border_arr1 + step+start
            subslice1 = slice(start, border, step)
            subslice2 = slice(border - lshape[0], end - lshape[0], step)
            assert border >= lshape[0]
            #print("Hard case", subslice1,subslice2)
            subarray1 = self.left.request_data(subslice1)
            subarray2 = self.right.request_data(subslice2)
            return np.concatenate([subarray1, subarray2], axis=0)

class ArrayUnaryOperation(LazyArrayOperation):
    def __init__(self, a):
        self.a = a

    def perform(self, a):
        raise NotImplementedError

    def request_data(self, interesting_slices:slice_t):
        a = self.a.request_data(interesting_slices)
        return self.perform(a)

    def shape(self):
        return self.a.shape()

    def __repr__(self):
        return f"{type(self).__name__}({self.a})"




class ArrayBinaryOperation(LazyArrayOperation):
    def __init__(self,a,b):
        self.a = a
        self.b = b

    def perform(self,a,b):
        raise NotImplementedError

    def shape(self):
        s1 = self.a.shape()
        s2 = self.b.shape()
        if s1!=s2:
            raise IndexError(f"Shapes mismatch {s1} and {s2}")
        return s1


    def request_data(self, interesting_slices:slice_t):
        #print(f"SLICES for {type(self).__name__}", interesting_slices)
        a = self.a.request_data(interesting_slices)
        b = self.b.request_data(interesting_slices)
        return self.perform(a,b)

    def __repr__(self):
        return f"{type(self).__name__}({self.a}, {self.b})"


class ArrayAdd(ArrayBinaryOperation):
    def perform(self,a,b):
        return a+b


class ArraySub(ArrayBinaryOperation):
    def perform(self,a,b):
        return a-b


class ArrayMul(ArrayBinaryOperation):
    def perform(self,a, b):
        return a * b


class ArrayDiv(ArrayBinaryOperation):
    def perform(self, a, b):
        result = np.zeros(a.shape)
        np.divide(a, b, out=result, where=(b != 0))
        return result




class ConstantSlice(LazyArrayOperation):
    def __init__(self, source:LazyArrayOperation, slices:slice_t):
        self.source = source
        self.slices = slices
        #print("Created lazy slice", slices)

    def request_data(self, interesting_slices:slice_t):
        #print(self.source)
        combined_slices = combine_slices(self.source.shape(), self.slices, interesting_slices)
        #print("COMBINED", combined_slices)
        res =  self.source.request_data(combined_slices)
        #print("DATA",res)
        return res
        # src = self.source.request_data(self.slices)
        # #print("REQUESTED FOR ARRAY", interesting_slices)
        # return src[interesting_slices]

    def shape(self):
        src_shape = self.source.shape()
        #print("SRC_SHAPE",src_shape)
        #print(self.slices)
        return shape_transform(src_shape, self.slices)


class ConstantMultiply(LazyArrayOperation):
    def __init__(self, array, constant):
        self.array = array
        self.constant = constant

    def request_data(self, interesting_slices:slice_t):
        x = self.array.request_data(interesting_slices)
        return x*self.constant

    def shape(self):
        return self.array.shape()