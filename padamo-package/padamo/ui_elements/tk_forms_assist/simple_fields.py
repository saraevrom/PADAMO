from .base import Node

class ValueNode(Node):
    '''
    Node corresponding to fields that store value (base class)
    '''
    def __init__(self):
        self.value = self.DEFAULT_VALUE

    def parse_formdata(self, formdata):
        if formdata is not None:
            self.value = formdata

    def get_data(self):
        return self.value

    def set_data(self,data):
        self.value = data

    def recover_formdata(self):
        return self.value


class IntNode(ValueNode):
    '''
    Node corresponding to "int" field
    '''
    FIELD_TYPE = "int"
    DEFAULT_VALUE = 0


class FloatNode(ValueNode):
    '''
    Node corresponding to "float" field
    '''
    FIELD_TYPE = "float"
    DEFAULT_VALUE = 0.0


class StringNode(ValueNode):
    '''
    Node corresponding to "str" field
    '''
    FIELD_TYPE = "str"
    DEFAULT_VALUE = ""


class LabelNode(ValueNode):
    '''
    Node corresponding to "label" field
    Just set its DISPLAY_NAME for displayment
    '''
    FIELD_TYPE = "label"
    FANCY = False

    @classmethod
    def generate_configuration(cls):
        conf = super().generate_configuration()
        conf["fancy"] = cls.FANCY
        return conf

class BoolNode(ValueNode):
    '''
    Node corresponding to "bool" field
    '''
    FIELD_TYPE = "bool"
    DEFAULT_VALUE = False


class RadioNode(ValueNode):
    '''
    Node corresponding to "radio" field (select an option in radio buttons)
    '''
    FIELD_TYPE = "radio"
    VALUES = []

    @classmethod
    def generate_configuration(cls):
        conf = super(RadioNode, cls).generate_configuration()
        conf["values"] = cls.VALUES
        return conf


class ComboNode(RadioNode):
    '''
    Node corresponding to "combo" field (select an option in combobox)
    '''
    FIELD_TYPE = "combo"
    SELECTION_READONLY = False

    @classmethod
    def generate_configuration(cls):
        conf = super(ComboNode, cls).generate_configuration()
        conf["readonly"] = cls.SELECTION_READONLY
        return conf


class FileNode(ValueNode):
    '''
    Node corresponding to "file" field (choose a filename)
    '''
    FIELD_TYPE = "file"
    ASK_MODE = "saveas"
    FILE_TYPES = []
    INITIAL_DIR = ""

    @classmethod
    def generate_configuration(cls):
        conf = super(FileNode, cls).generate_configuration()
        conf["ask_mode"] = cls.ASK_MODE
        conf["filetypes"] = cls.FILE_TYPES
        conf["initialdir"] = cls.INITIAL_DIR
        return conf
