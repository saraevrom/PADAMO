from padamo.ui_elements.tk_forms_assist import FormNode, IntNode, OptionNode
from padamo.ui_elements.tk_forms_assist.factory import create_value_field

class LevelOptions(OptionNode):
    DISPLAY_NAME = "Contour levels"
    ITEM_TYPE = create_value_field(IntNode,"Value",10)
    DEFAULT_VALUE = None

class RightForm(FormNode):
    FIELD__freq_space = create_value_field(IntNode, "Frequencies amount", 10)
    FIELD__levels = LevelOptions
