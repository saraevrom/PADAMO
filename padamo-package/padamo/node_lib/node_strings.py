from padamo.node_processing import Node, STRING, NodeExecutionError, INTEGER, AllowExternal, BOOLEAN
import re


class ConcatenateNode(Node):
    INPUTS = {
        "a": STRING,
        "b": STRING,
    }
    OUTPUTS = {
        "result": STRING
    }


    REPR_LABEL = "Concatenate"
    LOCATION = "/String/Concatenate"

    def calculate(self, globalspace:dict) ->dict:
        a = self.require( "a")
        b = self.require( "b")
        return {"result": a+b}


class ReplicateNode(Node):
    INPUTS = {
        "a": STRING,
        "b": INTEGER,
    }
    OUTPUTS = {
        "result": STRING
    }

    REPR_LABEL = "Replicate"
    LOCATION = "/String/Replicate"

    def calculate(self, globalspace:dict) ->dict:
        a = self.require( "a")
        b = self.require( "b")
        return {"result": a*b}


class ReplaceNode(Node):
    INPUTS = {
        "a": STRING,
    }
    CONSTANTS = {
        "regex":False,
        "pattern": AllowExternal(""),
        "replace": AllowExternal(""),
    }
    OUTPUTS = {
        "result": STRING
    }

    REPR_LABEL = "Replace"
    LOCATION = "/String/Replace"

    def calculate(self, globalspace:dict) ->dict:
        a:str = self.require("a")
        pattern = self.constants["pattern"]
        repl = self.constants["replace"]
        if self.constants["regex"]:
            return {"result": re.sub(pattern, repl,a)}
        else:
            return {"result": a.replace(pattern,repl)}


class FindNode(Node):
    INPUTS = {
        "a": STRING,
    }
    CONSTANTS = {
        "regex": False,
        "error_if_not_found":False,
        "entry_number":AllowExternal(0),
        "pattern": AllowExternal(""),
    }
    OUTPUTS = {
        "result": STRING,
        "found":BOOLEAN
    }

    REPR_LABEL = "Find"
    LOCATION = "/String/Find"

    def calculate(self,globalspace:dict) ->dict:
        a: str = self.require("a")
        pattern = self.constants["pattern"]
        entry_number = self.constants["entry_number"]
        found = False
        data = ""
        if self.constants["regex"]:
            matches = re.findall(pattern,a)
            print(matches)
            if matches and len(matches)>entry_number:
                mat = matches[entry_number]
                if not isinstance(mat,str):
                    raise NodeExecutionError(f"Match {mat} is not string",self.graph_node)
                data = mat
                found = True
        else:
            if pattern in a:
                found = True
                data = pattern
        if self.constants["error_if_not_found"] and not found:
            raise NodeExecutionError(f"No match in \"{a}\"", self.graph_node)
        return {"result": data, "found":found}


# class ReplaceRegexNode(Node):
#     INPUTS = {
#         "a": STRING,
#         "pattern": STRING,
#         "replace": STRING,
#     }
#     OUTPUTS = {
#         "result": STRING
#     }
#
#     REPR_LABEL = "Replace (regex)"
#     LOCATION = "/String/Replace (regex)"
#
#     def calculate(self, globalspace:dict) ->dict:
#         a:str = self.require( "a")
#         pattern = self.require( "pattern")
#         repl = self.require( "replace")
#         return {"result": re.sub(pattern,repl,a)}