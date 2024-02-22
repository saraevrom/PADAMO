from padamo.node_processing import Node, FLOAT, INTEGER, NodeExecutionError
from padamo.node_processing.node_canvas import GraphDraggableNode
from .node_math import UnaryNode

class BinaryNode(Node):
    INPUTS = {
        "a": FLOAT,
        "b": FLOAT,
    }
    CONSTANTS = {
        "integer":False
    }
    OUTPUTS = {
        "result": FLOAT
    }

    @classmethod
    def on_constants_update(cls,graphnode:GraphDraggableNode):
        integer = graphnode.get_constant("integer")
        if integer:
            graphnode.replace_output("result",INTEGER)
            graphnode.replace_input("a",INTEGER)
            graphnode.replace_input("b",INTEGER)
        else:
            graphnode.replace_output("result", FLOAT)
            graphnode.replace_input("a", FLOAT)
            graphnode.replace_input("b", FLOAT)

    @staticmethod
    def operation(a,b):
        raise NotImplementedError

    def calculate(self, globalspace:dict) ->dict:
        a = self.require("a")
        b = self.require("b")
        res = self.operation(a, b)
        return {"result": res}

class UnaryDualNode(UnaryNode):
    CONSTANTS = {
        "integer":False
    }

    @classmethod
    def on_constants_update(cls, graphnode: GraphDraggableNode):
        integer = graphnode.get_constant("integer")
        if integer:
            graphnode.replace_output("r", INTEGER)
            graphnode.replace_input("x", INTEGER)
        else:
            graphnode.replace_output("r", FLOAT)
            graphnode.replace_input("x", FLOAT)

class FloatAdd(BinaryNode):
    REPR_LABEL = "Add"
    LOCATION = "/Arithmetic/Add"

    @staticmethod
    def operation(a,b):
        return a+b


class FloatSub(BinaryNode):
    REPR_LABEL = "Subtract"
    LOCATION = "/Arithmetic/Subtract"

    @staticmethod
    def operation(a, b):
        return a - b


class FloatMul(BinaryNode):
    REPR_LABEL = "Multiply"
    LOCATION = "/Arithmetic/Multiply"

    @staticmethod
    def operation(a, b):
        return a * b


class FloatDiv(BinaryNode):
    REPR_LABEL = "Divide"
    LOCATION = "/Arithmetic/Divide"

    @staticmethod
    def operation(a, b):
        if isinstance(a,int) and isinstance(b,int):
            return a // b
        return a / b

class FloatMax(BinaryNode):
    REPR_LABEL = "Max"
    LOCATION = "/Arithmetic/Max"

    @staticmethod
    def operation(a,b):
        return max(a,b)


class FloatMin(BinaryNode):
    REPR_LABEL = "Min"
    LOCATION = "/Arithmetic/Min"

    @staticmethod
    def operation(a, b):
        return min(a, b)

class NegNode(UnaryDualNode):
    REPR_LABEL = "Negate"
    LOCATION = "/Arithmetic/Negate"

    @staticmethod
    def process(x):
        return -x