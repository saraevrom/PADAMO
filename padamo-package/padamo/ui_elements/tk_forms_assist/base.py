import inspect

PERSISTENT_CONFIGS = dict()

class Node(object):
    '''
    Base node class
    Contains some data about field
    DEFAULT_VALUE: default value set for field. Set as None to skip
    DISPLAY_NAME: string that will be displayed in GUI.
    '''
    FIELD_TYPE = "FIXME"
    DEFAULT_VALUE = None
    DISPLAY_NAME = "Generic"
    LOCKED = False

    def parse_formdata(self, formdata):
        raise NotImplementedError()

    def get_data(self):
        raise NotImplementedError()

    def set_data(self,data):
        raise NotImplementedError()

    def recover_formdata(self):
        raise NotImplementedError()

    @classmethod
    def generate_configuration(cls):
        conf =  {
            "display_name": cls.DISPLAY_NAME,
            "type": cls.FIELD_TYPE
        }
        if cls.DEFAULT_VALUE is not None:
            conf["default"] = cls.DEFAULT_VALUE
        conf["lock"] = cls.LOCKED
        return conf


    @classmethod
    def get_config_persistent(cls):
        key = cls
        if key not in PERSISTENT_CONFIGS:
            PERSISTENT_CONFIGS[key] = dict()
        return PERSISTENT_CONFIGS[key]


    @classmethod
    def fill_configuration(cls):
        cls.get_config_persistent()
        key = cls
        if not PERSISTENT_CONFIGS[key]:
            PERSISTENT_CONFIGS[key].update(cls.generate_configuration())
            return True
        return False

    @classmethod
    def get_configuration(cls):
        cls.fill_configuration()
        key = cls
        return PERSISTENT_CONFIGS[key]

    @classmethod
    def get_class_attributes_dict_ordered(cls):
        res = dict(cls.__dict__)
        for base in inspect.getmro(cls):
            if base != cls:
                if hasattr(base, "get_class_attributes_dict_ordered"):
                    res.update(base.get_class_attributes_dict_ordered())
        return res

    def get_attributes_dict_ordered(self):
        return type(self).get_class_attributes_dict_ordered()