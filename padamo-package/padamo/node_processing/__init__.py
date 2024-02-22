from .node_canvas import NodeCanvas, NodeExecutionError, Node, AllowExternal, Optional
from padamo.canvas_drawing.port_types import *

ARRAY = PortType.create_porttype("array", "#FF5500")
SIGNAL = PortType.create_porttype("signal", "#AAFF00")
PLOT = PortType.create_porttype("plot", "#AA00FF")
DETECTOR = PortType.create_porttype("detector","#AA557F")

TypedNode.ADDITIONAL_ALLOW.append((INTEGER,FLOAT))
