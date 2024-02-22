import numpy as np
from padamo.node_processing import Node, FLOAT, INTEGER


class UnaryNode(Node):
    INPUTS = {
        "x": FLOAT
    }
    OUTPUTS = {
        "r": FLOAT
    }

    @staticmethod
    def process(x):
        raise NotImplementedError

    def calculate(self, globalspace:dict) ->dict:
        x = self.require("x")
        return dict(r=self.process(x))


def create_unary(label,processor):
    class Unode(UnaryNode):
        LOCATION = f"/Math/{label}"
        REPR_LABEL = label

        @staticmethod
        def process(x):
            return processor(x)
    return Unode



class RoundNode(Node):
    INPUTS = {
        "x": FLOAT,
        "decimals": FLOAT
    }
    OUTPUTS = {
        "r": FLOAT
    }
    LOCATION = "/Math/Round"
    REPR_LABEL = "Round"

    def calculate(self, globalspace:dict) ->dict:
        x = self.require("x")
        decs = self.require("decimals", optional=True) or 0
        return dict(r=np.round(x, decimals=decs))


SinNode = create_unary("Sin", np.sin)
CosNode = create_unary("Cos", np.cos)
ASinNode = create_unary("Arcsin", np.arcsin)
ACosNode = create_unary("Arccos", np.arccos)
TanNode = create_unary("Tan", np.tan)
ATanNode = create_unary("Arctan", np.arctan)

class ATan2Node(Node):
    INPUTS = {
        "x1": FLOAT,
        "x2": FLOAT
    }
    OUTPUTS = {
        "r": FLOAT
    }
    LOCATION = "/Math/Arctan2"
    REPR_LABEL = "Arctan2"

    def calculate(self, globalspace:dict) ->dict:
        x1 = self.require("x1")
        x2 = self.require("x2")
        return dict(r=np.arctan2(x1,x2))

class PINode(Node):
    OUTPUTS = {
        "pi": FLOAT
    }
    LOCATION = "/Math/PI"
    REPR_LABEL = "PI"

    def calculate(self, globalspace:dict) ->dict:
        return dict(pi=np.pi)