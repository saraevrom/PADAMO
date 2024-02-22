import datetime
from .time_formats import UnixTimeFormat,UTCTimeFormat,FrameFormat
from padamo.ui_elements.tk_forms_assist import FormNode, StringNode, BoolNode, ComboNode, IntNode
from padamo.ui_elements.tk_forms_assist.factory import create_value_field


class TimeProcessor(object):
    def __init__(self, mode):
        self.mode = mode

    def __call__(self, t):
        if self.mode == "UTC":
            return datetime.datetime.utcfromtimestamp(float(t))
        else:
            return float(t)


class TimeFormatOld(ComboNode):
    DISPLAY_NAME = "Time format"
    SELECTION_READONLY = True
    VALUES = ["UTC", "unixtime"]
    DEFAULT_VALUE = "UTC"

    def get_data(self):
        mode = super().get_data()
        return TimeProcessor(mode)

    def set_data(self, data):
        super().set_data(data.mode)


class TimeFormat(ComboNode):
    DISPLAY_NAME = "Time format"
    SELECTION_READONLY = True
    VALUES = ["UTC", "unixtime", "frames"]
    MAPPING = [UTCTimeFormat, UnixTimeFormat, FrameFormat]
    DEFAULT_VALUE = "UTC"

    def get_data(self):
        data = super().get_data()
        i = self.VALUES.index(data)
        return self.MAPPING[i]



class AnimationParameters(FormNode):
    DISPLAY_NAME = "Animation"
    FIELD__fps = create_value_field(IntNode, "FPS", 10)
    FIELD__skip = create_value_field(IntNode, "Frame skip", 1)
    FIELD__lc_insert = create_value_field(BoolNode, "Lightcurve", False)
    FIELD__trigger_only = create_value_field(BoolNode, "Trigger only", False)
    FIELD__png_dpi = create_value_field(IntNode, "DPI", 100)

class ViewerFrame(FormNode):
    FIELD__show_time = create_value_field(BoolNode, "Show time in frame", True)
    FIELD__time_format = TimeFormat
    FIELD__animation = AnimationParameters
    FIELD__toi_start = create_value_field(StringNode, "Time of interest start", "")
    FIELD__toi_end = create_value_field(StringNode, "Time of interest end", "")
    FIELD__popup_safeguard = create_value_field(IntNode, "Plot safeguard [frames]", 10000)
