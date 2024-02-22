from .base import Node
from .simple_fields import ValueNode

import collections

class OrderedClassMembers(type):
    @classmethod
    def __prepare__(self, name, bases):
        return collections.OrderedDict()

    def __new__(self, name, bases, classdict):
        classdict['__ordered__'] = [key for key in classdict.keys()
                if key not in ('__module__', '__qualname__')]
        return type.__new__(self, name, bases, classdict)


class OptionNode(Node):
    '''
    Node corresponding to the "option" entry
    '''
    FIELD_TYPE = "option"
    ITEM_TYPE = None

    def __init__(self):
        self.value = None

    def parse_formdata(self, formdata):
        if formdata is None:
            self.value = None
        else:
            self.value = self.ITEM_TYPE()
            self.value.parse_formdata(formdata)

    def recover_formdata(self):
        if self.value is None:
            return None
        else:
            return self.value.recover_formdata

    @classmethod
    def generate_configuration(cls):
        conf = super(OptionNode, cls).generate_configuration()
        conf["subconf"] = cls.ITEM_TYPE.get_config_persistent()
        return conf

    @classmethod
    def fill_configuration(cls):
        if super().fill_configuration():
            cls.ITEM_TYPE.fill_configuration()
            return True
        return False

    def get_data(self):
        sub_data = self.value
        if sub_data is not None:
            return sub_data.get_data()

        return None

    def set_data(self,data):
        if data is None:
            self.value = None
        else:
            if self.value is None:
                self.value = self.ITEM_TYPE()
            self.value.set_data(data)




class ArrayNode(Node):
    '''
    Node corresponding to the "array" entry
    Use ITEM_TYPE for specifying subconf
    '''
    FIELD_TYPE = "array"
    ITEM_TYPE = None

    def __init__(self):
        self.data_list = []

    def parse_formdata(self, formdata):
        self.data_list.clear()
        for item in formdata:
            item_typed = self.ITEM_TYPE()
            item_typed.parse_formdata(item)
            self.data_list.append(item_typed)

    def recover_formdata(self):
        return [item.recover_formdata() for item in self.data_list]

    def get_data(self):
        return [item.get_data() for item in self.data_list]

    def set_data(self,data):
        self.data_list.clear()
        for item in data:
            item_typed = self.ITEM_TYPE()
            item_typed.set_data(item)
            self.data_list.append(item_typed)

    @classmethod
    def generate_configuration(cls):
        conf = super(ArrayNode, cls).generate_configuration()
        conf["subconf"] = cls.ITEM_TYPE.get_config_persistent()
        return conf

    @classmethod
    def fill_configuration(cls):
        if super().fill_configuration():
            cls.ITEM_TYPE.fill_configuration()
            return True
        return False


class AlternatingNode(Node, metaclass=OrderedClassMembers):
    '''
    Node corresponding to "alter" entry
    Use SEL__<name> for specifying selection types
    '''

    FIELD_TYPE = "alter"

    def __init__(self):
        self.value = None

    @classmethod
    def generate_configuration(cls):
        conf = super(AlternatingNode, cls).generate_configuration()
        values = []
        attrs = cls.get_class_attributes_dict_ordered()
        # Using dir() instead of __dict__ allows to use inherited fields. Only cons is reversed order of fields
        for k in attrs.keys():
            if k.startswith("SEL__"):
                name = k[5:]
                attr = attrs[k]
                subconf = attr.get_config_persistent()
                values.append({
                    "name": name,
                    "subconf": subconf
                })
        conf["values"] = values
        if cls.DEFAULT_VALUE is None:
            name0 = values[0]["name"]

            default_value = {
                "selection_type": name0
            }
            conf["default"] = default_value
        return conf

    @classmethod
    def fill_configuration(cls):
        if super().fill_configuration():
            attrs = cls.get_class_attributes_dict_ordered()
            for k in attrs.keys():
                if k.startswith("SEL__"):
                    attr = attrs[k]
                    attr.fill_configuration()
            return True
        return False

    def parse_formdata(self, formdata):
        selection = formdata["selection_type"]
        obj_value = formdata["value"]
        self.value = getattr(self, "SEL__"+selection)()
        self.value.parse_formdata(obj_value)

    def get_data(self):
        return self.value.get_data()

    def set_data(self,data):
        raise NotImplementedError("Alternating node loses selection data when parsed. Implement this method manually.")

    def recover_formdata(self):
        raise NotImplementedError("Alternating node loses selection data when parsed. Implement this method manually.")


class FormNode(Node, metaclass=OrderedClassMembers):
    '''
    Node corresponding to the form itself and "subform" field
    Use FIELD__<name> for specifying fields
    Call get_configuration_root() for getting root form
    '''
    FIELD_TYPE = "subform"
    USE_SCROLLVIEW = False

    def __init__(self):
        self.fields = dict()
        attrs = self.get_attributes_dict_ordered()
        for k in attrs.keys():
            if k.startswith("FIELD__"):
                name = k[7:]
                attr = attrs[k]
                self.fields[name] = attr()

    def parse_formdata(self, formdata: dict):
        for k in self.fields.keys():
            if k in formdata.keys():
                self.fields[k].parse_formdata(formdata[k])
            else:
                self.fields[k].parse_formdata(None)

    def recover_formdata(self):
        formdata = dict()
        for k in self.fields.keys():
            formdata[k] = self.fields[k].recover_formdata()
        return formdata

    def get_data(self):
        res_dict = dict()
        for k in self.fields.keys():
            res_dict[k] = self.fields[k].get_data()
        return res_dict

    def set_data(self,data):
        for k in data.keys():
            self.fields[k].set_data(data[k])

    @classmethod
    def generate_configuration_root(cls):
        res_dict = dict()

        attrs = cls.get_class_attributes_dict_ordered()
        for k in attrs.keys():
            if k.startswith("FIELD__"):
                name = k[7:]
                attr = attrs[k]
                res_dict[name] = attr.get_config_persistent()
        return res_dict

    @classmethod
    def generate_configuration(cls):
        conf = super(FormNode, cls).generate_configuration()
        conf["use_scrollview"] = cls.USE_SCROLLVIEW
        conf["subconf"] = cls.generate_configuration_root()
        return conf

    @classmethod
    def fill_configuration(cls):
        if super().fill_configuration():
            cls.fill_configurations()
            return True
        return False


    @classmethod
    def fill_configurations(cls):
        attrs = cls.get_class_attributes_dict_ordered()
        for k in attrs.keys():
            if k.startswith("FIELD__"):
                attr = attrs[k]
                attr.fill_configuration()

    @classmethod
    def get_configuration_root(cls):
        cls.fill_configurations()
        return cls.generate_configuration_root()
