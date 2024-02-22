from padamo.node_processing import Node, FLOAT, INTEGER, ANY, STRING, BOOLEAN, NodeExecutionError, ARRAY, SIGNAL
from padamo.lazy_array_operations import LazyArrayOperation
from padamo.utilities.dual_signal import Signal

CONVERSION_BRANCH = "/Conversion/"

def create_caster(t1, t2, caster, label):
    class CasterClass(Node):
        REPR_LABEL = label
        LOCATION = CONVERSION_BRANCH+label
        INPUTS = {
            "value":t1
        }
        OUTPUTS = {
            "value":t2
        }


        def calculate(self, globalspace:dict) ->dict:
            v = self.require("value")
            try:
                v1 = caster(v)
                return dict(value=v1)
            except:
                raise NodeExecutionError(f"Failed to cast {label}", self)


    return CasterClass


AnyToIntCaster = create_caster(ANY, INTEGER, int, "Cast Int")
AnyToFloatCaster = create_caster(ANY, FLOAT, int, "Cast Float")
AnyToStrCaster = create_caster(ANY, STRING, str, "Cast String")
AnyToBoolCaster = create_caster(ANY, BOOLEAN, bool, "Cast Boolean")


def cast_lazy_op(x):
    if isinstance(x, LazyArrayOperation):
        return x
    else:
        raise ValueError("element is not lazy array op")


AnyToSliceCaster = create_caster(ANY, ARRAY, cast_lazy_op, "Cast Array")

