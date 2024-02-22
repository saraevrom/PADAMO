import numpy as np

from padamo.ui_elements.tk_forms_assist import FormNode, IntNode, BoolNode, OptionNode, FloatNode
from padamo.ui_elements.tk_forms_assist.factory import create_value_field, kwarg_builder
from .storage import Interval

class AntiFpCutter(object):
    def __init__(self,min_duration, max_duration,min_positive_amplitude,min_negative_amplitude):
        self.min_duration = min_duration
        self.max_duration = max_duration
        self.min_positive_amplitude = min_positive_amplitude
        self.min_negative_amplitude = min_negative_amplitude

    def __call__(self, signal_part):
        if not self.min_duration<=signal_part.shape[0]<=self.max_duration:
            return False
        max_ = np.max(signal_part)
        min_ = np.min(signal_part)
        if max_<self.min_positive_amplitude:
            return False
        if min_<self.min_negative_amplitude:
            return False
        return True


@kwarg_builder(AntiFpCutter)
class AntiFPCutterForm(FormNode):
    DISPLAY_NAME = "Anti FP cutter parameters"
    FIELD__min_duration = create_value_field(IntNode,"Min duration",128)
    FIELD__max_duration = create_value_field(IntNode,"Max duration",1000)
    FIELD__min_positive_amplitude = create_value_field(FloatNode, "Min positive amplitude", 10.0)
    FIELD__min_negative_amplitude = create_value_field(FloatNode, "Min negative amplitude", -6.0)


class AntiFPOption(OptionNode):
    DISPLAY_NAME = "Anti FP cutter"
    DEFAULT_VALUE = None
    ITEM_TYPE = AntiFPCutterForm


class TriggerForm(FormNode):
    FIELD__chunk_size = create_value_field(IntNode,"Chunk size", 10000)
    FIELD__anti_fp_cutter = AntiFPOption
