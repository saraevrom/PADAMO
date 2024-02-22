import gc
import weakref
import typing
import inspect

import toposort

from padamo.canvas_drawing import CanvasWrapper
from padamo.canvas_drawing.linkable_nodes import DraggableNode
from padamo.canvas_drawing.port_types import PortType
from padamo.editing.editor_frame import VolatileEditorWindow


class NodeExecutionError(Exception):
    def __init__(self, msg, node_to_focus):
        super().__init__(msg)
        self.node = node_to_focus

class ConstRemapper(object):
    def __init__(self, ref):
        self.ref = ref

    def __getitem__(self, item):
        return self.ref.get_constant(item)


class ConstWrapper(object):
    def __init__(self, wrapped):
        self.wrapped = wrapped

    def mod_part(self,env:dict):
        pass

    def unwrap(self, env):
        self.mod_part(env)
        wrapped = self.wrapped
        while isinstance(wrapped, ConstWrapper):
            wrapped = wrapped.unwrap(env)
        return wrapped


class AllowExternal(ConstWrapper):
    def mod_part(self,env:dict):
        env["allow_external"] = True


class Optional(ConstWrapper):
    def mod_part(self,env:dict):
        env["optional"] = True


class Node(object):
    INPUTS: dict[str, PortType] = {}
    OUTPUTS: dict[str, PortType] = {}
    CONSTANTS:dict[str, typing.Any] = {}
    MIN_SIZE = (100,100)
    GRAPH_ARGS: list = []
    GRAPH_KWARGS = dict(fill="#FFFFFF")
    REPR_LABEL="Node"
    REMOVABLE=True
    IS_FINAL=False
    LOCATION=""

    @classmethod
    def get_namespace(cls):
        return inspect.getmodule(cls).__name__

    @classmethod
    def get_identifier(cls):
        return cls.get_namespace()+"."+cls.__name__

    @classmethod
    def on_constants_update(cls,graphnode):
        pass

    @property
    def constants(self):
        return ConstRemapper(self)

    def get_constant(self, key):
        if self.inner_constants[key].externally_driven:
            return self.require("const_"+key, optional=self.inner_constants[key].optional)
        else:
            return self.inner_constants[key].value

    @classmethod
    def add_graphnode(cls, canvas_wrapper):
        node = GraphDraggableNode(canvas_wrapper, cls.MIN_SIZE[0], cls.MIN_SIZE[1], *cls.GRAPH_ARGS, **cls.GRAPH_KWARGS)
        for k in cls.INPUTS.keys():
            node.add_input(cls.INPUTS[k], k)
        for k in cls.OUTPUTS.keys():
            node.add_output(cls.OUTPUTS[k], k)
        for k in cls.CONSTANTS:
            v = cls.CONSTANTS[k]
            env = dict(allow_external=False, optional=False)
            if isinstance(v,ConstWrapper):
                v = v.unwrap(env)
            if isinstance(v,tuple):
                t,v = v
            else:
                t = type(v)
            if callable(v):
                v = v()
            node.add_constant(t,k,v, **env)
        canvas_wrapper.add_node(node)
        node.bound_class = cls
        node.set_title(cls.REPR_LABEL)
        node.removable = cls.REMOVABLE
        node.on_constants_update()
        return node

    def __init__(self, gnode=None):
        self.inputs = dict()
        self.outputs = dict()
        self.inner_constants = dict()
        self._graph_node = gnode
        self._order = None
        self._last_inputs = None

    @property
    def graph_node(self):
        if self._graph_node is None:
            return None
        gnode = self._graph_node()
        if gnode is None:
            self._graph_node = None
        return gnode

    def require(self, key, optional=False):
        inputs = self._last_inputs
        if key not in inputs.keys():
            raise NodeExecutionError(f"No input {key} for {self.REPR_LABEL}",self)
        if inputs[key] is None and not optional:
            raise NodeExecutionError(f"Port {key} is has None value in {self.REPR_LABEL}", self)
        return inputs[key]

    def _get_in_repr(self,k):
        if self.inputs[k] is None:
            return "None"
        else:
            a, b = self.inputs[k]
            return f"{a.REPR_LABEL}.{b}"

    def _get_out_reprs(self,k):
        res = []
        for v in self.outputs[k]:
            a,b = v
            res.append(f"{a.REPR_LABEL}.{b}")
        return "(" + ", ".join(res) + ")"

    def __repr__(self):
        ins = ", ".join([f"{k}={self._get_in_repr(k)}" for k in self.inputs.keys()])
        outs = "; ".join([f"{k}={self._get_out_reprs(k)}" for k in self.outputs.keys()])
        return self.REPR_LABEL+"(inputs: "+ins+"; outputs: "+outs+")"

    def calculate_with_inputs(self, inputs, globalspace:dict):
        self._last_inputs = inputs
        return self.calculate(globalspace)

    def calculate(self,globalspace:dict)->dict:
        raise NotImplementedError

    def apply_on_env(self, env:dict, globalspace):
        inputs = dict()
        for k in self.inputs.keys():
            inp = self.inputs[k]
            if inp is not None:
                node, port = inp
                inp = env[node][port]
            inputs[k] = inp
        outputs = {k: None for k in self.outputs.keys()}
        try:
            calculated = self.calculate_with_inputs(inputs, globalspace)
            if not isinstance(calculated, dict):
                raise NodeExecutionError("Node returned not dict", self)
        except Exception as e:
            raise NodeExecutionError(str(e), self)
        outputs.update(calculated)
        env[self] = dict()
        for k in outputs.keys():
            env[self][k] = outputs[k]

    def alive(self):
        return self._graph_node.is_alive()


class GraphDraggableNode(DraggableNode):
    last_clicked = None

    def __init__(self, node_canvas, min_w, min_h,*args,**kwargs):
        kwargs["outline"] = "#000000"
        kwargs["width"] = 1
        super().__init__(node_canvas.canvas, min_w, min_h,*args,**kwargs)
        self._container = node_canvas
        self.bound_class = None
        self.removable=True

    def on_click(self, event):
        super().on_click(event)
        if GraphDraggableNode.last_clicked != self:
            if GraphDraggableNode.last_clicked is not None:
                GraphDraggableNode.last_clicked.set_properties(width=1)
            self.set_properties(width=3)
            self._container.show_in_inspector(weakref.ref(self))
            GraphDraggableNode.last_clicked = self

    def on_canvas_click(self, event):
        super().on_canvas_click(event)
        self.deselect()

    def deselect(self):
        if GraphDraggableNode.last_clicked == self:
            GraphDraggableNode.last_clicked.set_properties(width=1)
            self._container.show_in_inspector(None)
            GraphDraggableNode.last_clicked = None

    def on_keypress(self, event):
        if event.keycode == 119:
            self._pressed_delete()

    def _pressed_delete(self):
        if self._container.winfo_toplevel().focus_get() is self._container.canvas:
            if GraphDraggableNode.last_clicked == self and self.removable:
                GraphDraggableNode.last_clicked = None
                self._container.show_in_inspector(None)
                self._container.remove_node(self)

    @staticmethod
    def remove_selected():
        if GraphDraggableNode.last_clicked is not None:
            last_clicked: GraphDraggableNode = GraphDraggableNode.last_clicked
            last_clicked._pressed_delete()

    def on_constants_update(self):
        for k in self.constants.keys():
            v = self.constants[k]
            if v.externally_driven and v.associated_link is not None:
                self.add_input(v.associated_link, "const_"+k)
            else:
                self.remove_input("const_"+k)

        self.bound_class.on_constants_update(self)

    def on_node_modified(self):
        self._container.on_any_node_modified()

    def get_constant(self,key):
        if key not in self.constants.keys():
            raise NodeExecutionError(f"No constant {key} for {self}",None)
        if self.constants[key].externally_driven:
            return "<externally driven>"
        return self.constants[key].value

    def serialize(self):
        constants = {k: self.constants[k].state() for k in self.constants.keys()}
        position = self.position
        return {
            "constants": constants,
            "bound_class": self.bound_class.get_identifier(),
            "position": [position[0], position[1]]
        }

    @staticmethod
    def deserialize(data, canvas):
        from padamo.node_lib.index import NODE_DICT
        bound_class = NODE_DICT[data["bound_class"]]
        graphnode = bound_class.add_graphnode(canvas)
        graphnode.position = tuple(data["position"])
        graphnode.set_constants(data["constants"])
        return graphnode


class NodeCanvas(CanvasWrapper):
    def __init__(self, master, inspector:VolatileEditorWindow, *args,**kwargs):
        super().__init__(master, *args,**kwargs)
        self.inspector = inspector
        self.graph_nodes = []
        self._node_cache = None
        self.on_modify_callback = None

    def on_any_node_modified(self):
        self._node_cache = None
        if self.on_modify_callback:
            self.on_modify_callback()

    def invalidate_cache(self):
        self._node_cache = None

    def show_in_inspector(self, node):
        self.inspector.linked_node = node
        self.inspector.update_editable_list()

    def add_node(self, node:GraphDraggableNode):
        self.graph_nodes.append(node)
        x = self.canvas.canvasx(0)
        y = self.canvas.canvasy(0)
        node.position = x,y
        self.on_any_node_modified()

    def gather_nodes(self):
        nodes = [node.bound_class(weakref.ref(node)) for node in self.graph_nodes]
        for i in range(len(self.graph_nodes)):
            gnode = self.graph_nodes[i]
            gnode:GraphDraggableNode
            output_links = gnode.get_output_links()
            for k in output_links.keys():
                nodes[i].outputs[k] = []
                for (output_gnode, input_name) in output_links[k]:
                    tgti = self.graph_nodes.index(output_gnode)
                    nodes[i].outputs[k].append((nodes[tgti], input_name))
            input_links = gnode.get_input_links()
            for k in input_links.keys():
                if input_links[k] is None:
                    nodes[i].inputs[k] = None
                else:
                    inp_gnode, port = input_links[k]
                    tgti = self.graph_nodes.index(inp_gnode)
                    nodes[i].inputs[k] = (nodes[tgti], port)
            consts = gnode.get_constants()
            for k in consts.keys():
                nodes[i].inner_constants[k] = consts[k]
        return nodes

    def remove_node(self, node):
        node.disconnect_all()
        node.deselect()
        node.destroy()
        self.graph_nodes.remove(node)
        self.on_any_node_modified()

    def clear_nodes(self):
        for node in self.graph_nodes:
            node.disconnect_all()
            node.deselect()
            node.destroy()
        self.graph_nodes.clear()
        self.on_any_node_modified()
        gc.collect()

    def remove_highlight(self):
        for node in self.graph_nodes:
            node:GraphDraggableNode
            node.set_properties(outline="#000000")

    def highlight_node(self,node:GraphDraggableNode):
        self.remove_highlight()
        node.set_properties(outline="#FF0000")

    def serialize(self):
        data = [node.serialize() for node in self.graph_nodes]
        for i,node_data in enumerate(data):
            gnode = self.graph_nodes[i]
            output_links = gnode.get_output_links()
            node_data["outputs"] = {}
            for k in output_links.keys():
                node_data["outputs"][k] = []
                for output_node, tgt_port in output_links[k]:
                    index = self.graph_nodes.index(output_node)
                    node_data["outputs"][k].append([index, tgt_port])

        return data

    def deserialize(self,data):
        self.clear_nodes()
        self.graph_nodes = [GraphDraggableNode.deserialize(d,self) for d in data]
        for i in range(len(self.graph_nodes)):
            outlinks = data[i]["outputs"]
            for out_port in outlinks.keys():
                for [index, in_port] in outlinks[out_port]:
                    self.graph_nodes[i].get_output_port(out_port).link_to(self.graph_nodes[index].get_input_port(in_port))


    def ensure_cache(self):
        if self._node_cache is None:
            nodes = self.gather_nodes()
            top = dict()
            for n in nodes:
                print(n)
            node_pool = [node for node in nodes if node.IS_FINAL]
            print("FINALS", node_pool)
            while node_pool:
                node = node_pool.pop(0)
                i = nodes.index(node)
                # if i in top.keys():
                #     raise NodeExecutionError("Cyclic dependecy detected",node.graph_node)
                top[i] = []
                for k in node.inputs.keys():
                    link = node.inputs[k]
                    if link is not None:
                        tgt,port = link
                        if tgt not in top[i]:
                            j = nodes.index(tgt)
                            top[i].append(j)
                            if j not in top.keys():
                                node_pool.append(tgt)

            # for i,node in enumerate(nodes):
            #     top[i] = []
            #     for k in node.inputs.keys():
            #         link = node.inputs[k]
            #         if link is not None:
            #             tgt,port = link
            #             if tgt not in top[i]:
            #                 top[i].append(nodes.index(tgt))
            print(top)
            sorted_top = list(toposort.toposort_flatten(top))
            print(sorted_top)
            print("recompiled nodes")
            self._node_cache = [nodes[i] for i in sorted_top]


    def calculate(self, globs=None):
        if globs is None:
            globs = dict()
        self.ensure_cache()
        env = dict()
        for node in self._node_cache:
            node.apply_on_env(env,globs)
        #print("Nodes gathered")
