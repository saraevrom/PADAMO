from .connections import TypedNode
from padamo.lazy_array_operations.base import LazyArrayOperation

PORT_WIDTH=15
PORT_HEIGHT=15

class PortType(object):
    def __init__(self, name, color):
        self.name = name
        self.color = color

    def __eq__(self, other):
        return self.name == other.name

    def build_node(self,canvas, is_output,x,y):
        return TypedNode(canvas,self,is_output,x,y,x+PORT_WIDTH,y+PORT_HEIGHT, fill=self.color)

    @staticmethod
    def create_porttype(name, color):
        pt = PortType(name,color)
        TypedNode.ADDITIONAL_ALLOW.append((pt,ANY))
        return pt

    #TypedNode.ADDITIONAL_ALLOW.append((b,a))



ANY = PortType("any", "#000000")

STRING = PortType.create_porttype("string", "#FF0000")
BOOLEAN = PortType.create_porttype("boolean", "#00FF00")
FLOAT = PortType.create_porttype("float", "#0000FF")
INTEGER = PortType.create_porttype("int", "#00AABB")