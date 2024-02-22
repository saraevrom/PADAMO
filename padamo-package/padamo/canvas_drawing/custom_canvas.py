import tkinter as tk
import weakref


def add_to_collection(c, item):
    c.append(item)
    return len(c)-1

LMB_PRESSED = 256
RMB_PRESSED = 1024



class ObjectRemovedError(Exception):
    def __init__(self):
        super().__init__(f"Object was removed")

class SharedCanvas(tk.Canvas):
    key_listeners = []
    def __init__(self, master, *args,**kwargs):
        super().__init__(master, *args,**kwargs)
        self.weak_objects = []
        self.bind("<Motion>", self.on_hover)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Button-1>", self.on_click)
        self.bind("<Button-3>", self.on_rclick)
        self.bind('<Double-Button-1>', self.on_dclick)
        self.bind_all("<Key>", SharedCanvas.on_keypress_global)
        SharedCanvas.key_listeners.append(self)

    def destroy(self) -> None:
        SharedCanvas.key_listeners.remove(self)
        super().destroy()

    def update_size(self):
        region = self.bbox('all')
        region = 0,0,region[2],region[3]
        self.config(scrollregion=region)

    def _broadcast_event(self, attr_name, event):
        i = 0
        while i < len(self.weak_objects):
            obj = self.weak_objects[i]()
            if obj is None:
                self.weak_objects.pop(i)
            else:
                try:
                    getattr(obj, attr_name)(event)
                    i += 1
                except ObjectRemovedError:
                    self.weak_objects.pop(i)

    def _send_event_to_tag(self, attr_name, event, tgt_tag):
        i = 0
        while i < len(self.weak_objects):
            obj = self.weak_objects[i]()
            if obj is None:
                self.weak_objects.pop(i)
            else:
                if tgt_tag == obj.obj_id:
                    getattr(obj, attr_name)(event)
                    return
                i += 1

    def _send_event_to_tags(self, attr_name, event, tgt_tags):
        for t in tgt_tags:
            self._send_event_to_tag(attr_name, event, t)

    def cleanup(self):
        i = 0
        while i < len(self.weak_objects):
            obj = self.weak_objects[i]()
            if obj is None:
                self.weak_objects.pop(i)
            else:
                i += 1

    def add_weakref(self, r):
        self.weak_objects.append(r)
        return len(self.weak_objects)-1

    def del_weakref(self,i):
        if 0<=i<len(self.weak_objects):
            self.weak_objects.pop(i)

    def on_hover(self, event):
        # self._hover_handle = self.canvas.add_hover_listener(self.on_canvas_hover)
        found_tag = self.find_withtag("current")
        if found_tag:
            if event.state & LMB_PRESSED!=0:
                self._send_event_to_tags("on_b1_motion", event, found_tag)
        self._broadcast_event("on_canvas_hover", event)

    def on_leave(self, event):
        # self._leave_handle = self.canvas.add_leave_listener(self.on_canvas_leave)
        self._broadcast_event("on_canvas_leave", event)


    def on_click(self, event):
        self.focus_set()
        # self._click_handle = self.canvas.add_b1_listener(self.on_canvas_click)
        found_tag = self.find_withtag("current")
        if found_tag:
            self._send_event_to_tags("on_click", event, found_tag)
        else:
            self._broadcast_event("on_canvas_click", event)

    def on_dclick(self, event):
        found_tag = self.find_withtag("current")
        if found_tag:
            self._send_event_to_tags("on_dclick", event, found_tag)

    def on_rclick(self, event):
        found_tag = self.find_withtag("current")
        if found_tag:
            self._send_event_to_tags("on_rclick", event, found_tag)

    @staticmethod
    def on_keypress_global(event):
        for listener in SharedCanvas.key_listeners:
            listener.on_key_press(event)

    def on_key_press(self, event):
        self._broadcast_event("on_keypress", event)


class CanvasWrapper(tk.Frame):
    def __init__(self, master,*args,**kwargs):
        super().__init__(master)
        inner_frame = tk.Frame(self)
        self.canvas = SharedCanvas(inner_frame,*args,**kwargs)
        self.canvas.pack(side="left", fill="both", expand=True)
        side_scrollbar = tk.Scrollbar(self,orient="vertical")
        bottom_scrollbar = tk.Scrollbar(self, orient="horizontal")
        side_scrollbar.pack(side="right", fill="y")
        bottom_scrollbar.pack(side="bottom", fill="x")
        inner_frame.pack(side="left",fill="both", expand=True)
        bottom_scrollbar.config(command=self.canvas.xview)
        side_scrollbar.config(command=self.canvas.yview)
        self.canvas.config(xscrollcommand=bottom_scrollbar.set, yscrollcommand=side_scrollbar.set)
