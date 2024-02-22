from padamo.ui_elements.tk_forms_assist import FormNode, StringNode, IntNode, FloatNode, ArrayNode, BoolNode
from padamo.ui_elements.tk_forms_assist.factory import create_value_field
from padamo.ui_elements.configurable_gridplotter import DeviceParameters, CellLayer


def create_dual(ty):
    class DualEntry(FormNode):
        FIELD__x = create_value_field(ty, "x", 1)
        FIELD__y = create_value_field(ty, "y", 1)

        def get_data(self):
            data = super().get_data()
            return data["x"], data["y"]

        def set_data(self,data):
            x,y = data
            super().set_data({"x":x, "y":y})

    return DualEntry


DualInt = create_dual(IntNode)
DualFloat = create_dual(FloatNode)


class MaskArray(ArrayNode):
    DISPLAY_NAME = "Mask"
    ITEM_TYPE = create_value_field(DualInt, "Masked part")


class SuperCell(FormNode):
    DISPLAY_NAME = "Supercell"
    FIELD__layer_name = create_value_field(StringNode, "Name", "Cell")
    FIELD__gap = create_value_field(DualFloat, "Gaps", {"x": 4.0, "y": 4.0})
    FIELD__shape = create_value_field(DualInt, "Shape", {"x": 2, "y": 2})
    FIELD__mask = MaskArray


class SupercellArray(ArrayNode):
    DISPLAY_NAME = "Supercells"
    ITEM_TYPE = SuperCell


class DetectorParser(FormNode):
    FIELD__name = create_value_field(StringNode,"Name","detector")
    FIELD__flipped_x = create_value_field(BoolNode,"Invert x", False)
    FIELD__flipped_y = create_value_field(BoolNode,"Invert y", False)
    FIELD__pixel_size = create_value_field(DualFloat, "Pixel size", {"x": 2.85, "y": 2.85})
    FIELD__pixels_shape = create_value_field(DualInt, "MAPMT pixel shape", {"x": 8, "y": 8})
    FIELD__supercells = SupercellArray

    def get_data(self):
        formdata = super().get_data()
        return DeviceParameters.from_dict(formdata)

    def set_data(self, data: DeviceParameters):
        formdata = data.to_dict()
        super().set_data(formdata)
