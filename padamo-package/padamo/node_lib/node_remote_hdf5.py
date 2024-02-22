
from padamo.node_processing import Node, NodeExecutionError, STRING, ARRAY, SIGNAL
from padamo.node_processing.node_canvas import GraphDraggableNode
from padamo.utilities.dual_signal import Signal

class RemoteHDFSource(Node):
    INPUTS = {
        "field":STRING
    }
    OUTPUTS = {
        "array":ARRAY
    }
    REPR_LABEL = "Remote HDF array"
    LOCATION = "/Remote access/Remote HDF array"

    def calculate(self, globalspace:dict) -> dict:
        remote_factory = globalspace["loaded_remote"]
        if remote_factory is None:
            raise NodeExecutionError("Remote file is not loaded")

        field = self.require("field")
        return dict(array=remote_factory(field))


class RemoteHDFSignalSource(Node):
    CONSTANTS = {
        "space_field":"pdm_2d_rot_global",
        "time_field":"unixtime_dbl_global"
    }
    OUTPUTS = {
        "signal":SIGNAL
    }
    REPR_LABEL = "Remote HDF array"
    LOCATION = "/Remote access/Remote HDF signal"

    @classmethod
    def on_constants_update(cls,graphnode:GraphDraggableNode):
        s = graphnode.get_constant("space_field")
        t = graphnode.get_constant("time_field")
        graphnode.set_title(f"Remote HDF array ({s},{t})")

    def calculate(self, globalspace:dict) -> dict:
        remote_factory = globalspace["loaded_remote"]
        if remote_factory is None:
            raise NodeExecutionError("Remote file is not loaded",self.graph_node)

        space_field = self.constants["space_field"]
        time_field = self.constants["time_field"]
        space = remote_factory(space_field)
        time = remote_factory(time_field)
        return dict(signal=Signal(space,time))


# class RemoteMergedHDFSource(Node):
#     INPUTS = {
#         "field":STRING
#     }
#     OUTPUTS = {
#         "array":ARRAY
#     }
#     REPR_LABEL = "Remote HDF directory"
#     LOCATION = "/Remote access/Remote HDF directory"
#
#     def calculate(self, globalspace:dict) -> dict:
#         remote_factory = globalspace["loaded_remote_dir"]
#         if remote_factory is None:
#             raise NodeExecutionError("Remote file is not loaded")
#
#         field = self.require("field")
#         return dict(array=remote_factory(field))


class RemoteMergedHDFSignalSource(Node):
    CONSTANTS = {
        "space_field":"pdm_2d_rot_global",
        "time_field":"unixtime_dbl_global"
    }
    OUTPUTS = {
        "signal":SIGNAL
    }
    REPR_LABEL = "Remote merged HDF directory"
    LOCATION = "/Remote access/Remote merged HDF directory"

    @classmethod
    def on_constants_update(cls,graphnode:GraphDraggableNode):
        s = graphnode.get_constant("space_field")
        t = graphnode.get_constant("time_field")
        graphnode.set_title(f"Remote HDF directory ({s},{t})")

    def calculate(self, globalspace:dict) -> dict:
        remote_factory = globalspace["loaded_remote_dir"]
        if remote_factory is None:
            raise NodeExecutionError("Remote file is not loaded",self.graph_node)

        space_field = self.constants["space_field"]
        time_field = self.constants["time_field"]
        space = remote_factory(space_field)
        time = remote_factory(time_field)
        return dict(signal=Signal(space,time))
