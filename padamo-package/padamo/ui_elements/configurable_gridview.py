import copy
import tkinter as tk
from typing import Optional

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np
from serde import Model, fields
from .plotter import Plotter
from .searching import comparing_binsearch
import numba as nb

def pdm_start(i, size):
    return i//size*size

@nb.njit()
def firstlast(bools):
    start = 0
    end = bools.shape[0]-1
    while start<bools.shape[0] and not bools[start]:
        start += 1
    if start == bools.shape[0]:
        return 0, end

    while end >= 0 and not bools[end]:
        end -= 1

    return start,end


class CellLayer(Model):
    layer_name: fields.Str()
    gap: fields.Tuple(fields.Float(), fields.Float())
    shape: fields.Tuple(fields.Int(), fields.Int())
    mask: fields.List(fields.Tuple(fields.Int(), fields.Int()))


class DeviceParameters(Model):
    name: fields.Str()
    flipped_x: fields.Bool()
    flipped_y: fields.Bool()

    pixel_size: fields.Tuple(fields.Float(), fields.Float())
    pixels_shape: fields.Tuple(fields.Int(), fields.Int())

    supercells: fields.List(fields.Nested(CellLayer))

    @property
    def inversion(self):
        return self.flipped_x, self.flipped_y

    @property
    def full_shape(self):
        x, y = self.pixels_shape
        for supercell in self.supercells:
            x1, y1 = supercell.shape
            x *= x1
            y *= y1
        return x, y

    def is_compatible(self,shape):
        return self.full_shape==shape

    def check_compatibility(self,shape):
        if not self.is_compatible(shape):
            raise GridError(f"Shape {shape} is not compatible with {self.name} detector")

class GridError(Exception):
    pass


def repeat_positions(src_arr, number, gap):
    offset = src_arr[-1] + gap
    offsetted = np.arange(number) * offset
    res = np.add.outer(offsetted, src_arr).flatten()
    #print(src_arr,offset, offsetted,"->",res)
    return res


class ConfigurableGridView(object):
    def __init__(self, axes, initcolor="blue"):
        self._conf_grid_axes = axes
        axes.set_box_aspect(1)

        self._configuration: Optional[DeviceParameters] = None
        self.patches = []
        self._initcolor = initcolor
        self._additional_patches = []
        self._lower = None
        self._centers = None

    @property
    def full_shape(self):
        self._check_init()
        return self._configuration.full_shape

    def calculate_centered_coords(self, dim):
        centers = repeat_positions(np.array([0]),
                                   self._configuration.pixels_shape[dim],
                                   self._configuration.pixel_size[dim]
                                   )
        #print("MAPMT", centers)
        for supercell in self._configuration.supercells:
            centers = repeat_positions(centers, supercell.shape[dim], supercell.gap[dim]+self._configuration.pixel_size[dim])

        com = centers.mean()
        res = centers - com
        if self._configuration.inversion[dim]:
            res = -res
        #print("RES",res)
        return res

    def configure_detector(self, configuration: DeviceParameters):
        self._configuration = configuration
        self._centers = (self.calculate_centered_coords(0), self.calculate_centered_coords(1))
        self._lower = (self._centers[0]-self._configuration.pixel_size[0]/2,
                       self._centers[1]-self._configuration.pixel_size[1]/2)

        for row in self.patches:
            for p in row:
                p.remove()
        self.patches.clear()
        for p in self._additional_patches:
            p.remove()
        self._additional_patches.clear()

        for y in self._lower[1]:
            row = []
            for x in self._lower[0]:
                rect = Rectangle((x, y), self._configuration.pixel_size[0],
                                 self._configuration.pixel_size[1], color=self._initcolor
                                 )
                self._conf_grid_axes.add_patch(rect)
                row.append(rect)
            self.patches.append(row)

        # To make correct z offset for edges
        for y in self._lower[1]:
            for x in self._lower[0]:
                rect = Rectangle((x, y), self._configuration.pixel_size[0], self._configuration.pixel_size[1], fill=None,
                                 linewidth=1,
                                 edgecolor='black')
                self._conf_grid_axes.add_patch(rect)
                self._additional_patches.append(rect)

        min_x = self._lower[0][0]
        max_x = self._lower[0][-1]+self._configuration.pixel_size[0]
        min_y = self._lower[1][0]
        max_y = self._lower[1][-1]+self._configuration.pixel_size[1]

        max_c = max(abs(min_x),abs(min_y),abs(max_x), abs(max_y))
        self._conf_grid_axes.set_xlim(-max_c, max_c)
        self._conf_grid_axes.set_ylim(-max_c, max_c)
        self._conf_grid_axes.set_box_aspect(1)

    def find_index_from_coord(self, dim, x):
        self._check_init()
        min_x = self._lower[dim][0]
        max_x = self._lower[dim][-1] + self._configuration.pixel_size[dim]
        # if x<=min_x or x>=max_x:
        #     return -1
        index = comparing_binsearch(self._centers[dim], x)
        x0 = self._centers[dim][index]
        if abs(x-x0)*2 < self._configuration.pixel_size[dim]:
            return index

        if index>0:
            x0 = self._centers[dim][index-1]
            if abs(x - x0)*2 < self._configuration.pixel_size[dim]:
                return index-1
        if index< len(self._centers[dim])-1:
            x0 = self._centers[dim][index +1]
            if abs(x - x0)*2 < self._configuration.pixel_size[dim]:
                return index+1
        return -1

    def set_colors(self, color_mat):
        self._check_compatibility(color_mat.shape)
        w, h = self.full_shape
        for j in range(w):
            for i in range(h):
                self.set_pixel_color(j, i, color_mat[i, j])

    def _check_init(self):
        if not self.patches:
            raise GridError("Grid is not set up")

    def set_pixel_color(self, j, i, color):
        self._check_init()
        self.patches[j][i].set_color(color)

    def is_compatible(self, shape):
        if self._configuration is None:
            return False
        return self._configuration.is_compatible(shape)

    def _check_compatibility(self, shape):
        if self._configuration is None:
            raise GridError(f"Detector is not set up")
        self._configuration.check_compatibility(shape)

    def get_configuration(self):
        if self._configuration is None:
            return None
        return copy.deepcopy(self._configuration)

    def get_visible_range(self, visibility_matrix,dim):
        collapsed = np.logical_or.reduce(visibility_matrix, axis=1-dim)
        first_, last_ = firstlast(collapsed)
        pdm_size = self._configuration.pixels_shape[dim]
        first = pdm_start(first_,pdm_size)
        last = pdm_start(last_,pdm_size)+pdm_size-1

        half_pix = self._configuration.pixel_size[dim]/2
        return self._centers[dim][first]-half_pix, self._centers[dim][last]+half_pix

    def get_full_range(self,dim):
        half_pix = self._configuration.pixel_size[dim] / 2
        return self._centers[dim][0] - half_pix, self._centers[dim][-1] + half_pix
