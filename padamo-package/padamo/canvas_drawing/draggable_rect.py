import tkinter as tk
from .canvas_drawable import Rectangle
from .canvas_drawable import SharedCanvas


class DraggableRectangle(Rectangle):
    def __init__(self, canvas:SharedCanvas, *args,**kwargs):
        super().__init__(canvas, *args,**kwargs)
        self._start_x = None
        self._start_y = None
        self._start_pos = None

    def on_click(self, event):
        start_pos = self.position
        self._start_x = -event.x+start_pos[0]
        self._start_y = -event.y+start_pos[1]

    def on_b1_motion(self, event):
        if self._start_x is not None:
            new_x = event.x + self._start_x
            new_y = event.y + self._start_y
            self.position = new_x, new_y