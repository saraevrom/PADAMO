from .simple_fields import LabelNode
from .base import Node

def create_value_field(form_t, display_name, default_value=None):
    class FieldClass(form_t):
        DISPLAY_NAME = display_name

    if default_value is not None:
        FieldClass.DEFAULT_VALUE = default_value

    return FieldClass

def create_label(label, fancy=False):
    class LabelClass(LabelNode):
        DISPLAY_NAME = label
        FANCY = fancy

    return LabelClass


def kwarg_builder(ret_cls):
    def decorator(base_cls:Node):
        class WrappedCreatorNode(base_cls):
            def get_data(self):
                data = super().get_data()
                return ret_cls(**data)
        return WrappedCreatorNode
    return decorator

def dict_arg_builder(ret_cls):
    def decorator(base_cls:Node):
        class WrappedCreatorNode(base_cls):
            def get_data(self):
                data = super().get_data()
                return ret_cls(data)
        return WrappedCreatorNode
    return decorator