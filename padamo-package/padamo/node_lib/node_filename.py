import os
import os.path
from padamo.node_processing import Node, FLOAT, INTEGER, STRING, BOOLEAN


class SplitFilenameNode(Node):
    INPUTS = {
        "full_path":STRING
    }
    OUTPUTS = {
        "dirname":STRING,
        "basename":STRING
    }
    LOCATION = "/File path manipulation/Split file path"
    REPR_LABEL = "Split file path"

    def calculate(self, globalspace:dict) ->dict:
        full_path = self.require( "full_path")
        dirname = os.path.dirname(full_path)
        basename = os.path.basename(full_path)
        return dict(dirname=dirname, basename=basename)


class FilePathJoinNode(Node):
    INPUTS = {
        "a":STRING,
        "b":STRING
    }
    OUTPUTS = {
        "joined":STRING
    }

    LOCATION = "/File path manipulation/Join path"
    REPR_LABEL = "Join path"

    def calculate(self, globalspace:dict) ->dict:
        a = self.require("a")
        b = self.require("b")
        return dict(joined=os.path.join(a,b))
