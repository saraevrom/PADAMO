
from padamo.utilities.workspace import Workspace


EXAMPLE_ADDON = '''
from node_processing import Node, INTEGER

# Remove prefix example_ to make addon active
 
class LCDNode(Node):
    INPUTS = {
        "a": INTEGER,
        "b": INTEGER,
    }
    OUTPUTS={
        "c": INTEGER
    }
    MIN_SIZE = (100, 100)
    LOCATION = "/LCD"
    IS_FINAL = True
    REPR_LABEL = "LCD"

    def calculate(self, globalspace:dict) ->dict:
        a = self.require("a")
        b = self.require("b")
        while a!=0 and b!=0:
            if a>b:
                a = a%b
            else:
                b = b%a

        return dict(c=a+b)

'''

class AddonWorkspace(Workspace):
    def populate(self):
        s = self.get_file("example_addon_hello.py")
        if s:
            with open(s,"w") as fp:
                fp.write(EXAMPLE_ADDON)


ADDONS_WORKSPACE = AddonWorkspace("viewer_addons")
