import tkinter as tk
import weakref

from .custom_canvas import SharedCanvas, ObjectRemovedError

# gc.set_debug(gc.DEBUG_STATS)

class Transform(object):
    def __init__(self):
        self.children = []
        self.parent = None


    def detach_children(self):
        for c in self.children:
            c.parent = None
        self.children.clear()

    @property
    def root(self):
        if self.parent is None:
            return self
        else:
            return self.parent.root

    def add_child(self, obj):
        if obj.parent is not None:
            obj.parent.children.remove(obj)
        self.children.append(obj)
        obj.parent = self

    def remove_child(self, obj):
        if obj in self.children:
            self.children.remove(obj)
            obj.parent = None

    def detach_child(self, obj):
        assert obj in self.children
        assert obj.parent is self
        self.children.remove(obj)
        obj.parent = None

    def _get_children_transforms(self):
        return [c.position for c in self.children]

    def _update_children(self,positions):
        for i,c in enumerate(self.children):
            c.position = positions[i]

    def get_position(self) -> (int, int):
        raise NotImplementedError

    def set_position(self,x,y):
        raise NotImplementedError

    @property
    def position(self):
        if self.parent is None:
            #print(self.get_position())
            return self.get_position()
        else:
            xs,ys = self.get_position()
            xp, yp = self.parent.get_position()
            return xs-xp, ys-yp

    def on_position_change(self):
        pass

    @position.setter
    def position(self, v_in):
        if self.parent is None:
            v = max(v_in[0],0), max(v_in[1], 0)
            x, y = v
        else:
            xr,yr = v_in
            xp, yp = self.parent.get_position()
            x = xp+xr
            y = yp+yr
        pos = self._get_children_transforms()
        self.set_position(x,y)
        self._update_children(pos)
        self.on_position_change()



class EmptyTransform(Transform):
    def __init__(self,x,y):
        super().__init__()
        self.x = x
        self.y = y

    def get_position(self) -> (int, int):
        return (self.x,self.y)

    def set_position(self,x,y):
        self.x = x
        self.y = y



ALLOWED_ATTRS = ["_exists", "__repr__", "__str__", "is_alive"]

class DrawnObject(Transform):
    '''
    Base object for manipulating tkinter.Canvas drawn shapes
    Invoke constructor first. Then set object ID
    '''
    def __init__(self, canvas:SharedCanvas, *args, **kwargs):
        super().__init__()
        self.canvas = canvas
        self.obj_id = None
        self._exists = True
        self.obj_id = self.draw_object(*args, **kwargs)
        # Direct tag binding via canvas.tag_bind leads to memory leak
        # So these events will be processed in custom canvas class through weakref
        self.canvas.add_weakref(weakref.ref(self))

    def is_alive(self):
        return self._exists

    def get_property(self, prop):
        return self.canvas.itemcget(self.obj_id, prop)

    def set_properties(self, **kwargs):
        self.canvas.itemconfigure(self.obj_id, **kwargs)

    @property
    def root(self):
        if self.parent is None:
            return self
        else:
            return self.parent.root

    def raise_above(self, other=None):
        if other is None:
            self.canvas.tag_raise(self.obj_id)
        else:
            self.canvas.tag_raise(self.obj_id, other.obj_id)

    def lower_below(self, other=None):
        if other is None:
            self.canvas.tag_lower(self.obj_id)
        else:
            self.canvas.tag_lower(self.obj_id, other.obj_id)

    def on_keypress(self, event):
        pass

    def on_canvas_click(self, event):
        pass

    def on_canvas_leave(self, event):
        pass

    def on_canvas_hover(self, event):
        pass

    def on_click(self, event):
        pass

    def on_dclick(self, event):
        pass

    def on_rclick(self, event):
        pass

    def on_lmb_release(self, event):
        pass

    def on_b1_motion(self, event):
        pass

    def draw_object(self, *args, **kwargs):
        raise NotImplementedError

    def __getattribute__(self,attr):
        if attr in ALLOWED_ATTRS:
            return super().__getattribute__(attr)
        exists = super().__getattribute__("_exists")
        if exists:
            return super().__getattribute__(attr)
        else:
            raise ObjectRemovedError()

    def _remove(self):
        try:
            self.canvas.delete(self.obj_id)
            self.canvas.after(10,self.canvas.cleanup)
        except tk.TclError as e:
            if "invalid command name" in str(e).lower():
                pass
            else:
                raise e

    def remove(self):
        if self._exists:
            self.detach_children()
            self._remove()
            self._exists = False

    def destroy(self):
        '''
        More brutal version of remove function.
        Make sure that children don't have links
        :return:
        '''
        if self._exists:
            for c in self.children:
                c.destroy()
            self.children.clear()
            self._remove()
            self._exists = False

    def __del__(self):
        if self._exists:
            print("DEL", self)
            self.remove()
        else:
            print("DEL <removed object>")

    def on_moved(self):
        pass

    def coords(self, *args):
        return self.canvas.coords(self.obj_id, *args)

    def bbox(self, *args):
        return self.canvas.bbox(self.obj_id, *args)

    def on_position_change(self):
        self.on_moved()
        self.canvas.update_size()


class Rectangle(DrawnObject):
    '''
    Rectangle for tkinter.Canvas
    Wrapper for tk.Canvas.create_rectangle
    '''

    def draw_object(self, *args, **kwargs):
        return self.canvas.create_rectangle(*args, **kwargs)

    def get_position(self) -> (int, int):
        x0,y0,x1,y1 = self.coords()[:4]
        return int(x0),int(y0)

    def set_position(self,x,y):
        x0,y0,x1,y1 = self.coords()[:4]
        x1 = x1-x0+x
        y1 = y1-y0+y
        self.coords(x,y,x1,y1)


    def get_center(self) -> (int,int):
        x0, y0, x1, y1 = self.coords()[:4]
        xc = (x0+x1)/2
        yc = (y0+y1)/2
        return int(xc), int(yc)

    @property
    def width(self):
        x0,y0,x1,y1 = self.coords()[:4]
        return x1-x0

    @width.setter
    def width(self,w):
        x0, y0, x1, y1 = self.coords()[:4]
        self.coords(x0, y0, x0+w, y1)

    @property
    def height(self):
        x0, y0, x1, y1 = self.coords()[:4]
        return y1-y0

    @height.setter
    def height(self, h):
        x0, y0, x1, y1 = self.coords()[:4]
        self.coords(x0, y0, x1, y0+h)


class Line(DrawnObject):
    '''
    Rectangle for tkinter.Canvas
    Wrapper for tk.Canvas.create_line
    '''

    def draw_object(self, *args, **kwargs):
        return self.canvas.create_line(*args, **kwargs)


class Text(DrawnObject):

    def draw_object(self, *args, **kwargs):
        return self.canvas.create_text(*args, **kwargs)

    def get_position(self) -> (int, int):
        x,y = self.coords()[:2]
        return int(x), int(y)

    def set_position(self,x,y):
        self.coords(x,y)
