import os.path

import h5py
import numpy as np
from padamo.node_processing import Node, FLOAT, INTEGER, STRING, ARRAY, ANY, NodeExecutionError
from padamo.lazy_array_operations import LazyArrayOperation
from padamo.lazy_array_operations.basic_operations import ConstantArray
from padamo.lazy_array_operations.base import normalize_slice, ArrayUnaryOperation, ArrayBinaryOperation


class SliceArrayNode(Node):
    INPUTS = {
        "array_in": ARRAY,
        "start": INTEGER,
        "end":INTEGER
    }
    OUTPUTS = {
        "array_out": ARRAY,
    }
    REPR_LABEL = "Slice axis 0"
    LOCATION = "/Arrays/Slice 1D"

    def calculate(self, globalspace:dict) ->dict:
        array_in = self.require("array_in")
        assert isinstance(array_in, LazyArrayOperation)
        start = self.require("start",optional=True)
        end = self.require("end",optional=True)
        s = slice(start, end)
        print(s)
        return dict(array_out=array_in[s])


class ShapeGetterNode(Node):
    INPUTS = {
        "array_in": ARRAY,
    }
    CONSTANTS = {
        "axis": 0
    }
    OUTPUTS = {
        "length":INTEGER
    }
    LOCATION = "/Arrays/Length"
    REPR_LABEL = "Length"

    def calculate(self, globalspace:dict) ->dict:
        arr = self.require("array_in")
        assert isinstance(arr, LazyArrayOperation)
        ax = self.constants["axis"]
        l = arr.shape()[ax]
        return dict(length=l)

    @classmethod
    def on_constants_update(cls, graphnode):
        graphnode.set_title(cls.REPR_LABEL + f"(axis={graphnode.get_constant('axis')})")


class IndexNode(Node):
    INPUTS = {
        "array_in": ARRAY,
        "index":INTEGER
    }
    OUTPUTS = {
        "element_out": ANY
    }

    LOCATION = "/Arrays/Get element"
    REPR_LABEL = "Element with index"

    def calculate(self, globalspace:dict) ->dict:
        array_in = self.require("array_in")
        array_in:LazyArrayOperation
        index = self.require("index")
        elem_out = array_in[index]
        return dict(element_out=elem_out)


class DummyArray(LazyArrayOperation):
    def __init__(self, src:LazyArrayOperation):
        assert len(src.shape())==1
        self.src = src

    def request_data(self, interesting_slices):
        shape = self.src.shape()[0]
        if isinstance(interesting_slices, tuple) and len(interesting_slices) == 1:
            interesting_slices = interesting_slices[0]
        if isinstance(interesting_slices,int):
            return interesting_slices
        elif isinstance(interesting_slices,slice):
            start,end,step = normalize_slice(shape,interesting_slices)
            return np.arange(start,end,step)
        else:
            raise ValueError("Wrong slice", interesting_slices)

    def shape(self):
        return self.src.shape()


# class DummyTimeReplacerNode(Node):
#     INPUTS = {
#         "time":ARRAY
#     }
#     OUTPUTS = {
#         "dummy_time":ARRAY
#     }
#
#     LOCATION = "/Arrays/Dummy time"
#     REPR_LABEL = "Dummy time"
#
#     def calculate(self, globalspace:dict) ->dict:
#         time = self.require("time")
#         return dict(dummy_time=DummyArray(time))


class MaxNode(Node):
    INPUTS = {
        "array":ARRAY
    }
    CONSTANTS = {
        "whole":True,
        "axis":0
    }
    OUTPUTS = {
        "value":FLOAT
    }

    LOCATION = "/Arrays/Max"
    REPR_LABEL = "Max (array)"

    @classmethod
    def on_constants_update(cls,graphnode):
        if graphnode.get_constant("whole"):
            graphnode.replace_output("value",FLOAT)
        else:
            graphnode.replace_output("value", ARRAY)

    def calculate(self, globalspace:dict) ->dict:
        arr:LazyArrayOperation = self.require("array")
        arr1 = arr.request_all_data()
        if self.constants["whole"]:
            m = np.max(arr1)
        else:
            m = ConstantArray(np.max(arr1,axis=self.constants["axis"]))
        return dict(value=m)

class MinNode(Node):
    INPUTS = {
        "array":ARRAY
    }
    CONSTANTS = {
        "whole":True,
        "axis":0
    }
    OUTPUTS = {
        "value":FLOAT
    }


    @classmethod
    def on_constants_update(cls, graphnode):
        if graphnode.get_constant("whole"):
            graphnode.change_output("value",FLOAT)
        else:
            graphnode.change_output("value", ARRAY)

    LOCATION = "/Arrays/Min"
    REPR_LABEL = "Min (array)"

    def calculate(self, globalspace:dict) ->dict:
        arr:LazyArrayOperation = self.require("array")
        arr1 = arr.request_all_data()
        if self.constants["whole"]:
            m = np.min(arr1)
        else:
            m = ConstantArray(np.min(arr1,axis=self.constants["axis"]))
        return dict(value=m)

class LazyLogicOR(ArrayBinaryOperation):
    def perform(self,a,b):
        return np.logical_or(a,b)


class LazyLogicAND(ArrayBinaryOperation):
    def perform(self,a,b):
        return np.logical_and(a,b)


class LazyLogicNOT(ArrayUnaryOperation):
    def perform(self, a):
        return np.logical_not(a)


class ArrayOrNode(Node):
    INPUTS = {
        "array1":ARRAY,
        "array2":ARRAY
    }
    OUTPUTS = {
        "value":ARRAY
    }

    LOCATION = "/Arrays/Logic/Logic Or"
    REPR_LABEL = "Logic Or"

    def calculate(self, globalspace:dict) ->dict:
        arr1:LazyArrayOperation = self.require("array1")
        arr2:LazyArrayOperation = self.require("array2")
        return dict(value=LazyLogicOR(arr1,arr2))


class ArrayAndNode(Node):
    INPUTS = {
        "array1":ARRAY,
        "array2":ARRAY
    }
    OUTPUTS = {
        "value":ARRAY
    }

    LOCATION = "/Arrays/Logic/Logic And"
    REPR_LABEL = "Logic And"

    def calculate(self, globalspace:dict) ->dict:
        arr1:LazyArrayOperation = self.require("array1")
        arr2:LazyArrayOperation = self.require("array2")
        return dict(value=LazyLogicAND(arr1,arr2))


class ArrayNotNode(Node):
    INPUTS = {
        "array_in": ARRAY,
    }
    OUTPUTS = {
        "value": ARRAY
    }

    LOCATION = "/Arrays/Logic/Logic Not"
    REPR_LABEL = "Logic Not"

    def calculate(self, globalspace:dict) ->dict:
        arr1:LazyArrayOperation = self.require("array_in")
        return dict(value=LazyLogicNOT(arr1))
