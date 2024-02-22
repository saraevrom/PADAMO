import numpy as np
def set_vlines_position(lines, position):
    seg_old = lines.get_segments()
    ymin = seg_old[0][0, 1]
    ymax = seg_old[0][1, 1]

    seg_new = [np.array([[position, ymin],
                         [position, ymax]])]
    lines.set_segments(seg_new)


def set_vlines_position_ylims(lines, position, ymin, ymax):
    seg_old = lines.get_segments()

    seg_new = [np.array([[position, ymin],
                         [position, ymax]])]
    lines.set_segments(seg_new)