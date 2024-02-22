import gc
import sys
import weakref

from .canvas_drawable import Line, Rectangle

def reflection_point(p1,p2, direction=1):
    xc = (p1[0]+p2[0])/2
    yc = (p1[1]+p2[1])/2
    r = 0.5*((p1[1]-p2[1])**2 + (p1[0]-p2[0])**2)**0.5
    return xc+r*direction, yc

def plot_line_5p(p1, p5):
    x0,y0 = p1
    x1,y1 = p5
    p3 = (x0+x1)/2, (y0+y1)/2
    p2 = reflection_point(p1,p3,1)
    p4 = reflection_point(p3,p5,-1)
    return p1,p2,p3,p4,p5

def plot_line_6p(p1,p6,box1,box2):

    y_box1 = box1[1]
    y_box2 = box2[1]

    x1,y1 = p1
    x6,y6 = p6

    # print(box1, box2)
    # print(y1,y6)

    x_max = x1+(y1-y_box1)+5
    x_min = x6-(y6-y_box2)-5
    y_main = (y1+y6)/2
    p2 = (x_max, y1)
    p3 = (x_max,y_main)
    p4 = (x_min, y_main)
    p5 = (x_min, y6)
    #print(p1,p2,p3,p4,p5,p6)
    return p1,p2,p3,p4,p5,p6

def get_weak(w):
    if w is None:
        return None
    return w()

class Polyline(Line):
    def __init__(self, canvas, start, end,fill="#000000"):
        super().__init__(canvas, *plot_line_5p(start, end), smooth=1, fill=fill)
        self._line_start = start
        self._line_end = end
        self.pivot1 = None
        self.pivot2 = None
        self._redraw_coords()

    def __repr__(self):
        return f"{self._line_start}->{self._line_end}"

    def set_objects(self,weak_obj1, weak_obj2):
        self.pivot1 = weak_obj1
        self.pivot2 = weak_obj2
        self._redraw_coords()

    def _redraw_coords(self):
        obj1 = get_weak(self.pivot1)
        obj2 = get_weak(self.pivot2)
        x1 = self._line_start[0]
        x2 = self._line_end[0]
        if (obj1 is None or obj2 is None or x2>x1) or not (obj1.is_alive() and obj2.is_alive()):
            points = plot_line_5p(self._line_start, self._line_end)
        else:
            bbox1 = obj1.bbox()
            bbox2 = obj2.bbox()
            points = plot_line_6p(self._line_start, self._line_end, bbox1, bbox2)
        p = sum(points, start=())
        self.coords(*p)

    def set_start(self, new_start):
        self._line_start = new_start
        self._redraw_coords()

    def set_end(self, new_end):
        self._line_end = new_end
        self._redraw_coords()

    def set_line(self, new_start, new_end):
        self._line_start = new_start
        self._line_end = new_end
        self._redraw_coords()


class PointerPolyline(Polyline):
    def __init__(self, master, startpos, invert, fill):
        super().__init__(master, startpos,startpos,fill=fill)
        self.invert = invert

    def on_canvas_hover(self, event):
        eventx = self.canvas.canvasx(event.x)
        eventy = self.canvas.canvasy(event.y)
        eps = 5
        if self.invert:
            startpoint = self._line_end
        else:
            startpoint = self._line_start
        l = ((eventx-startpoint[0])**2 + (eventy-startpoint[1])**2)**0.5
        if l!=0:
            x = eventx - (eventx-startpoint[0])*eps/l
            y = eventy - (eventy - startpoint[1]) * eps / l
        else:
            x = eventx
            y = eventy
        if self.invert:
            self.set_start((x,y))
        else:
            self.set_end((x,y))



class LinkedRectangle(Rectangle):
    last_linked = None
    hoverer = None
    inverted_linking = False

    def __init__(self, canvas, *args, **kwargs):
        super().__init__(canvas, *args, **kwargs)
        self.next_targets = []
        self.prev_target = None
        self.connect_lines = []
        self.modification_callback = None

    def on_modify(self):
        if self.modification_callback:
            self.modification_callback()

    def allow_output(self):
        return True

    def allow_input(self):
        return True

    def allow_connectivity(self,other):
        return True

    def link_to(self, next_target):
        if next_target is self:
            return
        if next_target.prev_target is not None:
            next_target.unlink_backward()
        if self.canvas is next_target.canvas:
            allowed = self.allow_output() and next_target.allow_input() and self.allow_connectivity(next_target)
            if allowed and next_target not in self.next_targets:
                self.next_targets.append(next_target)
                next_target.prev_target = self
                self.on_line_update()
                next_target.on_modify()
                self.on_modify()


    def unlink_forward(self, item=None):
        if item is None:
            for tgt in self.next_targets:
                tgt.prev_target = None
                tgt.on_modify()
            self.next_targets.clear()
        else:
            item.prev_target = None
            self.next_targets.remove(item)
        self.on_line_update()
        self.on_modify()

    def unlink_backward(self):
        if self.prev_target is not None:
            self.prev_target.unlink_forward(self)
            self.on_modify()

    def on_line_update(self):
        lines_length = len(self.connect_lines)
        tgt_length = len(self.next_targets)
        only_mut = min(tgt_length, lines_length)
        own_center = self.get_center()
        for i in range(only_mut):
            tgt = self.next_targets[i]
            self.connect_lines[i].set_line(own_center, tgt.get_center())
            self.connect_lines[i].set_objects(weakref.ref(self.root), weakref.ref(tgt.root))
        if lines_length < tgt_length:
            new_lines = tgt_length-lines_length
            for i in range(new_lines):
                tgt = self.next_targets[i+lines_length]
                newline = Polyline(self.canvas, own_center, tgt.get_center(), fill=self.get_property("fill"))
                newline.set_objects(weakref.ref(self.root), weakref.ref(tgt.root))
                newline.lower_below()
                self.connect_lines.append(newline)
        elif lines_length > tgt_length:
            for i in range(tgt_length, lines_length):
                self.connect_lines.pop(tgt_length)
            gc.collect()
            print("REMOVED",lines_length-tgt_length)

    def on_moved(self):
        if self.prev_target is not None:
            self.prev_target.on_line_update()
        self.on_line_update()

    def on_click(self, event):
        if LinkedRectangle.last_linked is None:
            start_color = self.get_property("fill")
            if self.allow_output():
                self._start_linkage(False,start_color)
            elif self.allow_input():
                self._start_linkage(True,start_color)
        elif LinkedRectangle.last_linked is self:
            self._break_linkage()
        else:
            if LinkedRectangle.inverted_linking:
                self.link_to(LinkedRectangle.last_linked)
            else:
                LinkedRectangle.last_linked.link_to(self)
            self._break_linkage()

    def _start_linkage(self, inverted, start_color):
        LinkedRectangle.last_linked = self
        LinkedRectangle.hoverer = PointerPolyline(self.canvas, self.get_center(), invert=inverted, fill=start_color)
        LinkedRectangle.inverted_linking = inverted

    def _break_linkage(self):
        if LinkedRectangle.last_linked is not None:
            LinkedRectangle.last_linked = None
            LinkedRectangle.hoverer = None
            gc.collect()

    def on_canvas_leave(self, event):
        if LinkedRectangle.last_linked is not None:
            LinkedRectangle.last_linked = None
            LinkedRectangle.hoverer = None

    def on_canvas_click(self, event):
        if LinkedRectangle.last_linked is not None:
            LinkedRectangle.last_linked = None
            LinkedRectangle.hoverer = None

    def on_rclick(self, event):
        self.unlink_all()
        self.on_modify()

    def unlink_all(self):
        self.unlink_backward()
        self.unlink_forward()


class TypedNode(LinkedRectangle):
    ADDITIONAL_ALLOW = []
    def __init__(self,canvas,node_type,is_output, *args, **kwargs):
        super().__init__(canvas,*args,**kwargs)
        self.is_output = is_output
        self.node_type = node_type

    def allow_output(self):
        return self.is_output

    def allow_input(self):
        return not self.is_output

    def allow_connectivity(self,other):
        if hasattr(other,"node_type"):
            if self.node_type == other.node_type:
                return True
            if (self.node_type, other.node_type) in self.ADDITIONAL_ALLOW:
                return True
        return False
