import scipy.io as scipy_io
import numpy as np

from padamo.lazy_array_operations.basic_operations import ConstantArray
from padamo.node_processing import Node, STRING, ARRAY, AllowExternal
from padamo.node_processing.node_canvas import GraphDraggableNode


def read_mat(path, field):
    return ConstantArray(np.flip(scipy_io.loadmat(path)[field]))


class TrueMatReaderNode(Node):
    INPUTS = {
        "file_path": STRING
    }
    CONSTANTS = {
        "field": AllowExternal("field")
    }
    OUTPUTS = {
        "array": ARRAY
    }

    REPR_LABEL = "Matlab array"
    LOCATION = "/MAT/Matlab array"

    @classmethod
    def on_constants_update(cls,graphnode:GraphDraggableNode):
        graphnode.set_title(f'{cls.REPR_LABEL} ({graphnode.get_constant("field")})')

    def calculate(self, env):
        path = self.require("file_path")
        field = self.constants["field"]
        return dict(array=read_mat(path, field))

