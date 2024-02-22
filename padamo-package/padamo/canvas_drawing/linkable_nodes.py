import gc

from .connections import TypedNode
from .draggable_rect import DraggableRectangle
from .port_types import PortType, PORT_WIDTH, PORT_HEIGHT
from .canvas_drawable import EmptyTransform, Text

class ConstantDefinition(object):
    def __init__(self,const_type,state,allow_external, externally_driven,associated_link, optional):
        self.const_type = const_type
        self.value = state
        self.allow_external = allow_external
        self.externally_driven = externally_driven
        self.associated_link = associated_link
        self.optional = optional

    def state(self):
        return [self.value, self.externally_driven]

    def set_state(self,state):
        self.value = state[0]
        self.externally_driven = state[1]

class ConnectivityPort(EmptyTransform):
    def __init__(self,x,y, canvas, port_type:PortType, label:str, is_output):
        super().__init__(x,y)
        self.canvas = canvas
        if is_output:
            self.port = port_type.build_node(canvas,is_output,x-PORT_WIDTH,y)
            text_x = x-PORT_WIDTH-5
            self.label = Text(canvas,text_x,y,text=label, anchor='ne')
        else:
            self.port = port_type.build_node(canvas,is_output,x,y)
            text_x = x+self.port.width+5
            self.label = Text(canvas,text_x,y,text=label, anchor='nw')
        self.add_child(self.port)
        self.add_child(self.label)
        self.name = label
        self._is_output = is_output
        self.port_type = port_type

    def set_modify_callback(self, callback):
        self.port.modification_callback = callback

    def bbox(self):
        x01,y01,x11,y11 = self.port.bbox()
        x02,y02,x12,y12 =self.label.bbox()
        x0 = min(x01,x02)
        y0 = min(y01,y02)
        x1 = max(x11,x12)
        y1 = max(y11,y12)
        return x0,y0,x1,y1

    def width(self):
        x0, y0, x1, y1 = self.bbox()
        return x1-x0

    def unlink_all(self):
        self.port.unlink_all()

    def destroy(self):
        self.port.destroy()
        self.label.destroy()

    def get_connected_inputs(self):
        res = []
        if self._is_output:
            for tgt in self.port.next_targets:
                port = tgt.parent
                node = tgt.root
                res.append((node, port.name))
        return res

    def get_connected_output(self):
        if self._is_output:
            return None
        src = self.port.prev_target
        if src is None:
            return None
        port = src.parent
        node = src.root
        return node, port.name

class DraggableNode(DraggableRectangle):
    def __init__(self,canvas, min_width, min_height,*args,**kwargs):
        '''

        :param canvas:
        :param args: args for rectangle
        :param kwargs: kwargs for rectangle
        '''
        super().__init__(canvas,0,0,min_width,min_height, *args,**kwargs)
        self.title = Text(canvas,3,0, anchor="nw")
        self.add_child(self.title)
        self._min_width = min_width
        self._min_height = min_height
        self.inputs = dict()
        self.outputs = dict()
        self.constants = dict()

    def set_title(self, v):
        self.title.set_properties(text=v)
        self._place_ports()

    def disconnect_all(self):
        for p in self.inputs.values():
            p.unlink_all()
        for p in self.outputs.values():
            p.unlink_all()

    def _place_inputs(self):
        y = 5+PORT_HEIGHT
        for k in self.inputs.keys():
            self.inputs[k].position = (0,y)
            y += PORT_HEIGHT+5

    def _place_outputs(self):
        x = self.width
        y = 5+PORT_HEIGHT
        for k in self.outputs.keys():
            self.outputs[k].position = (x, y)
            y += PORT_HEIGHT+5

    def _inputs_width(self):
        if self.inputs:
            return max([x.width() for x in self.inputs.values()])
        else:
            return 0

    def _outputs_width(self):
        if self.outputs:
            return max([x.width() for x in self.outputs.values()])
        else:
            return 0


    def _port_height(self):
        inp_h = 5+PORT_HEIGHT+(5+PORT_HEIGHT)*len(self.inputs)
        out_h = 5+PORT_HEIGHT+(5+PORT_HEIGHT)*len(self.outputs)
        return max(inp_h, out_h)


    def _place_ports(self):
        x1, y1, x2, y2 = self.title.bbox()
        titlewidth = abs(x2 - x1) + 6
        self.width = max(self._inputs_width() + self._min_width, titlewidth)
        self.height = self._port_height()
        self._place_inputs()
        self._place_outputs()

    def _get_workon(self, is_output):
        if is_output:
            return self.outputs
        else:
            return self.inputs

    def _add_io(self, type_, name, is_output):
        workon_dict = self._get_workon(is_output)

        if name not in workon_dict.keys():
            new_ = ConnectivityPort(0, 0, self.canvas, type_, name, is_output)
            new_.set_modify_callback(self.on_node_modified)
            self.add_child(new_)
            workon_dict[name] = new_
        self._place_ports()

    def _del_io(self, name, is_output):
        workon_dict = self._get_workon(is_output)
        if name in workon_dict:
            item = workon_dict[name]
            item.unlink_all()
            item.destroy()
            self.detach_child(item)
            del workon_dict[name]
            self._place_ports()
            gc.collect()

    def check_input(self,name,type_):
        return self.inputs[name].port_type is type_

    def check_output(self,name,type_):
        return self.outputs[name].port_type is type_

    def replace_input(self,name,type_):
        if self.check_input(name,type_):
            return
        self.remove_input(name)
        self.add_input(type_,name)

    def replace_output(self,name,type_):
        if self.check_output(name,type_):
            return
        self.remove_output(name)
        self.add_output(type_,name)

    def remove_input(self,name):
        self._del_io(name,False)

    def remove_output(self,name):
        self._del_io(name,True)

    def add_input(self, input_type, name):
        self._add_io(input_type,name, False)

    def add_output(self, output_type, name):
        self._add_io(output_type,name,True)

    def add_constant(self, const_type, name, default_value, allow_external, optional):
        if name not in self.constants.keys():
            from padamo.editing.editors import pick_editor
            associated_link = pick_editor(const_type).ASSOCIATED_LINK_TYPE
            self.constants[name] = ConstantDefinition(const_type, default_value, allow_external, externally_driven=0,
                                                      associated_link=associated_link, optional=optional)

    def set_constants(self,vs:dict):
        for name in vs.keys():
            state = vs[name]
            if not isinstance(state,list):
                state = [state,0]
            self.constants[name].set_state(state)
        self.on_constants_update()
        self.on_node_modified()

    def on_constants_update(self):
        pass

    def on_node_modified(self):
        pass

    def get_constants(self):
        return self.constants


    # def remove_input(self, key):
    #     if key in self.inputs.keys():
    #         self.detach_child(self.inputs[key])
    #         del self.inputs[key]
    #         gc.collect()
    #         self._place_ports()
    #
    # def remove_output(self, key):
    #     if key in self.outputs.keys():
    #         self.detach_child(self.outputs[key])
    #         del self.outputs[key]
    #         gc.collect()
    #         self._place_ports()

    def get_inputs(self):
        return list(self.inputs.keys())

    def get_outputs(self):
        return list(self.outputs.keys())

    def get_output_links(self):
        res = dict()
        for k in self.outputs.keys():
            output = self.outputs[k]
            output:ConnectivityPort
            res[k] = output.get_connected_inputs()
        return res

    def get_input_links(self):
        res = dict()
        for k in self.inputs.keys():
            inp = self.inputs[k]
            inp:ConnectivityPort
            res[k] = inp.get_connected_output()
        return res

    def get_output_port(self,p):
        return self.outputs[p].port

    def get_input_port(self,p):
        return self.inputs[p].port