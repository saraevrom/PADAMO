import inspect
import os
from padamo.node_processing import Node, FLOAT, INTEGER, STRING, ARRAY, SIGNAL, DETECTOR
from padamo.editing import ANYFILE

class BindedGetterNode(Node):
    BINDKEY = ""

    def calculate(self, globalspace: dict) -> dict:
        key = self.BINDKEY
        if key in globalspace.keys():
            v = globalspace[key]
        else:
            v = None
        return dict(value=v)

    @classmethod
    def get_identifier(cls):
        return cls.get_namespace() + "." + cls.BINDKEY


class BindedSetterNode(Node):
    BINDKEY = ""
    IS_FINAL = True
    OPTIONAL = False

    def calculate(self, globalspace: dict) -> dict:
        globalspace[self.BINDKEY] = self.require( "value", optional=self.OPTIONAL)
        return dict()

    @classmethod
    def get_identifier(cls):
        return cls.get_namespace() +  "." + cls.BINDKEY


def create_getter(tab, node_type,key, label):
    class GetterNode(BindedGetterNode):
        BINDKEY = key
        OUTPUTS = {
            "value":node_type
        }
        LOCATION = "/"+tab+"/"+label
        REPR_LABEL = label



    return GetterNode


def create_setter(tab, node_type, key, label, optional=False):
    class SetterNode(BindedSetterNode):
        BINDKEY = key
        OPTIONAL = optional
        INPUTS = {
            "value":node_type
        }
        LOCATION = "/"+tab+"/" + label
        REPR_LABEL = label

    return SetterNode

# self.globals["current_frame"] = 0
# self.globals["total_frames"] = 100
# self.globals["current_view"] = None
# self.globals["loaded_file"] = ""

#CurrentFrameNode = create_getter(INTEGER, "current_frame", "Selected frame")
#TotalFramesNode = create_setter(INTEGER, "total_frames", "Total frames")

APP_TAB = "Application"

VIEWER_TAB = APP_TAB+"/Viewer"

ViewNode = create_setter(VIEWER_TAB, SIGNAL, "current_view", "View")
CurrentFileNode = create_getter(VIEWER_TAB, STRING, "loaded_file", "Loaded file")
AlivePixelsNode = create_getter(VIEWER_TAB, ARRAY, "alive_pixels", "Alive pixels")
TimeKeyNode = create_setter(VIEWER_TAB, STRING, "time_field", "Set time field")
TOIStart = create_getter(VIEWER_TAB, STRING, "toi_start", "Interest time start")
TOIEnd = create_getter(VIEWER_TAB, STRING, "toi_end", "Interest time end")
#SelectedDetector = create_getter(VIEWER_TAB, DETECTOR, "choosen_detector_config", "Detector")