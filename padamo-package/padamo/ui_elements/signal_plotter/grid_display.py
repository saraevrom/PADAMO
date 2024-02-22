import numpy as np
import numba as nb
from ..plotter import Plotter
from ..configurable_gridview import ConfigurableGridView


def squarify(xmin,xmax,ymin,ymax):
    com_x = (xmin+xmax)/2
    com_y = (ymin+ymax)/2
    span = max(abs(com_x-xmin), abs(com_x-xmax),abs(com_y-ymin), abs(com_y-ymax))
    return com_x-span, com_x+span, com_y-span, com_y+span

# def x0_from_pmt(alive_matrix):
#     low = HALF_GAP_SIZE
#     high = -HALF_GAP_SIZE
#     fullsize=False
#     if alive_matrix[:8,:].any():
#         low = -SPAN
#     if alive_matrix[8:,:].any():
#         high = SPAN
#         fullsize = low<0
#     if high<low:
#         fullsize = True
#         low = -SPAN
#         high = SPAN
#     return low, high, fullsize
#
#
# def y0_from_pmt(alive_matrix):
#     low = HALF_GAP_SIZE
#     high = -HALF_GAP_SIZE
#     fullsize=False
#     if alive_matrix[:, :8].any():
#         low = -SPAN
#     if alive_matrix[:, 8:].any():
#         fullsize = low<0
#         high = SPAN
#     if high < low:
#         fullsize = True
#         low = -SPAN
#         high = SPAN
#     return low, high, fullsize

@nb.njit()
def hsv_to_rgb(h,s,v):
    '''
    0<=h<=360
    0<=s<=1
    0<=v<=1
    '''
    h = h % 360
    c = v*s
    x = c*(1-abs((h/60)%2-1))
    m = v-c
    if h<60:
        _r = c
        _g = x
        _b = 0
    elif h<120:
        _r = x
        _g = c
        _b = 0
    elif h<180:
        _r = 0
        _g = c
        _b = x
    elif h<240:
        _r = 0
        _g = x
        _b = c
    elif h<300:
        _r = x
        _g = 0
        _b = c
    else:
        _r = c
        _g = 0
        _b = x
    return _r+m, _g+m, _b+m


def h_color(i, hue_shift=0.0,s_shift = 0.0, v_shift = 0.0):
    h = (i)/8*360+hue_shift
    s = 1-s_shift
    v = 1-v_shift
    return hsv_to_rgb(h,s,v)



def floormod(x,y):
    pivot = int(np.floor(x/y))*y
    return x-pivot

def get_color(i,j):
    if i%2==0:
        j1 = j
    else:
        j1 = j + 1
    shift_id = floormod(floormod(i-j1*4,16),16)
    gray_shift = 0.0
    if j%2==0 and (i-j//2)%2==0:
        gray_shift = 1.0
    return h_color(shift_id,j/16*180,
                   v_shift=gray_shift*0.5,
                   s_shift=gray_shift*0.3)

RECT = [0.01, 0.75, 0.2, 0.2]
def get_position(fig, axes):
    x, y, w, h = RECT
    inax_position = axes.transAxes.transform(RECT[0:2])
    transFigure = fig.transFigure.inverted()
    infig_position = transFigure.transform(inax_position)
    x = infig_position[0]
    y = infig_position[1]
    return x,y,w,h

def add_subplot_axes(fig,ax,axisbg='w'):
    x,y,w,h = get_position(fig, ax)
    # width *= rect[2]
    # height *= rect[3]  # <= Typo was here
    #subax = fig.add_axes([x,y,width,height],facecolor=facecolor)  # matplotlib 2.0+
    subax = fig.add_axes([x,y,w,h])
    return subax

class AltLegendView(ConfigurableGridView):
    def __init__(self, parent:Plotter, conf):
        parent_axes = parent.axes
        parent_figure = parent.figure
        rect = [0.01, 0.8, 0.15, 0.15]
        self.parent_axes = parent_axes
        self.parent_figure = parent_figure
        self.subaxes = add_subplot_axes(parent_figure,parent_axes,rect)
        super().__init__(self.subaxes, "white")
        self.configure_detector(conf)
        self.subaxes.get_xaxis().set_visible(False)
        self.subaxes.get_yaxis().set_visible(False)

    def update_view(self):
        x,y,w,h = get_position(self.parent_figure, self.parent_axes)

        self.subaxes.set_position([x,y,w,h])

    def set_alive(self, alive_matrix, adapt=True):
        width, height = self.full_shape
        for i in range(width):
            for j in range(height):
                if alive_matrix[i, j]:
                    self.set_pixel_color(j, i, get_color(i, j))
                else:
                    self.set_pixel_color(j, i, "white")

        if adapt:
            xmin, xmax = self.get_visible_range(alive_matrix, 0)
            ymin, ymax = self.get_visible_range(alive_matrix, 1)
        else:
            xmin, xmax = self.get_full_range(0)
            ymin, ymax = self.get_full_range(1)

        xmin,xmax,ymin,ymax = squarify(xmin,xmax,ymin,ymax)

        self.subaxes.set_xlim(xmin, xmax)
        self.subaxes.set_ylim(ymin, ymax)
        self.subaxes.set_aspect("equal")