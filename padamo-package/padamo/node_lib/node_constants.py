import os
from padamo.node_processing import Node, FLOAT, INTEGER, STRING, BOOLEAN, Optional
from padamo.editing import ANYFILE, SelectableOptions, Default
from padamo.utilities.workspace import Workspace


class Constant(Node):
    GRAPH_KWARGS = dict(fill="#FFFFFF")

    def calculate(self, globalspace:dict) ->dict:
        return dict(value=self.constants["value"])

    @classmethod
    def on_constants_update(cls, graphnode):
        graphnode.set_title(cls.REPR_LABEL + f"({graphnode.get_constant('value')})")


class FloatConstant(Constant):
    OUTPUTS = {
        "value": FLOAT
    }
    CONSTANTS = {
        "value": 0.0
    }
    MIN_SIZE = (100, 100)
    REPR_LABEL = "Constant F"
    REMOVABLE = True
    LOCATION = "/Constants/Float"


class StringConstant(Constant):
    OUTPUTS = {
        "value": STRING
    }
    CONSTANTS = {
        "value": ""
    }
    MIN_SIZE = (100, 100)
    REPR_LABEL = "Constant S"
    REMOVABLE = True
    LOCATION = "/Constants/String"


class IntConstant(Constant):
    OUTPUTS = {
        "value": INTEGER
    }
    CONSTANTS = {
        "value": 0
    }
    MIN_SIZE = (100, 100)
    REPR_LABEL = "Constant T"
    REMOVABLE = True
    LOCATION = "/Constants/Int"


class BoolConstant(Constant):
    OUTPUTS = {
        "value": BOOLEAN
    }
    CONSTANTS = {
        "value": False
    }
    MIN_SIZE = (100, 100)
    REPR_LABEL = "Constant B"
    REMOVABLE = True
    LOCATION = "/Constants/Boolean"

    @classmethod
    def on_constants_update(cls, graphnode):
        v = graphnode.get_constant('value')
        if v:
            graphnode.set_title(cls.REPR_LABEL + f"(1)")
        else:
            graphnode.set_title(cls.REPR_LABEL + f"(0)")


class FilenameConstant(Constant):
    OUTPUTS = {
        "value": STRING
    }
    CONSTANTS = {
        "value": (ANYFILE,"")
    }
    MIN_SIZE = (100, 100)
    REPR_LABEL = "File name"
    REMOVABLE = True
    LOCATION = "/Constants/Filename"

    @classmethod
    def on_constants_update(cls, graphnode):
        v = graphnode.get_constant('value')
        v = os.path.basename(v)
        graphnode.set_title(cls.REPR_LABEL + f"({v})")


class WorkspaceSelection(SelectableOptions):
    @classmethod
    def get_options(cls):
        wdir = Workspace.get_workspace_dir()
        r = os.listdir(wdir)
        r.sort()
        return r

class WorkspaceSelectionConstant(Node):
    OUTPUTS = {
        "value": STRING
    }

    CONSTANTS = {
        "subspace": (WorkspaceSelection, WorkspaceSelection.get_default),
        "file_name": ".",
    }

    REPR_LABEL = "Workspace file"
    LOCATION = "/Constants/Workspace file"

    @classmethod
    def on_constants_update(cls,graphnode):
        s_space = graphnode.get_constant("subspace")
        f_name = graphnode.get_constant("file_name")
        graphnode.set_title(cls.REPR_LABEL + f": {f_name} in workspace {s_space}")

    def calculate(self,globalspace:dict) ->dict:
        s_space = self.constants["subspace"]
        f_name = self.constants["file_name"]
        res = os.path.join(Workspace.get_workspace_dir(),s_space,f_name)
        return dict(value=res)
