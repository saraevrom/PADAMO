import typing

slicing = typing.Union[slice,int]
slice_t = typing.Union[typing.Tuple[slicing,...],slice,int]

def normalize_slice(init_size,s:slice):
    start = s.start
    stop = s.stop
    step = s.step
    if step is None:
        step = 1
    if start is None:
        start = 0
    if stop is None:
        stop = init_size
    if step == 0:
        raise ValueError("slice step cannot be zero")
    if step < 0:
        raise IndexError("Lazy operations are not supporting reverse step (yet)")
        step = -step
        start, stop = stop, start
    if start < 0:
        start = init_size + start
    if stop < 0:
        stop = init_size + stop

    stop = min(stop, init_size)
    start = max(start, 0)
    return start,stop,step


def determine_slice_size(init_size:int, s:slice):
    start,stop,step = normalize_slice(init_size,s)

    if start>=stop:
        return 0

    new_size = (stop-start-1)//step+1
    return new_size


def transform_single_axis(length, s:slicing, axis_num=0):
    if isinstance(s,int):
        if s>=length or s<0:
            raise IndexError(f"index {s} is out of bounds for axis {axis_num} with size {length}")
        return None
    elif isinstance(s,slice):
        return determine_slice_size(length,s)
    else:
        raise IndexError("only integers or slices (`:`) are valid indices for lazy operations")


def shape_transform(shape: tuple, s: slice_t):
    if isinstance(s, tuple):
        if len(s) > len(shape):
            raise IndexError(f"too many indices for array: array is {len(shape)}-dimensional, but {len(s)} were indexed")
        new_shapes = [transform_single_axis(shape[i],s[i],i) for i in range(len(s))]
        new_shapes = [item for item in new_shapes if item is not None]
        return tuple(new_shapes)
    else:
        tr = transform_single_axis(shape[0], s)
        if tr is None:
            return shape[1:]
        else:
            return (tr,)+shape[1:]


def combine_slice_int(l:int,a:slice, b:int):
    start, end,step = normalize_slice(l, a)
    if b>=0:
        new_index = start+step*b
        if new_index >= end:
            raise IndexError(f"Index {b} is out of range")
    else:
        l_ = determine_slice_size(l,a)
        if l_==0:
            raise IndexError("Cannot index empty array")
        last_included_index = start+(l_-1)*step
        new_index = last_included_index+(b+1)*step
        if new_index<start:
            raise IndexError(f"Index {b} is out of range")
    return new_index

def combine_two_slices(l:int, a:slice, b:slice):
    start1, end1, step1 = normalize_slice(l, a)
    imm_len = determine_slice_size(l,a)
    start2, end2, step2 = normalize_slice(imm_len,b)

    result_step = step1*step2
    result_start = start1+start2 * step1
    result_end = start1+step1*end2
    result_end = min(result_end, end1)
    return slice(result_start, result_end, result_step)


def combine_two_tuple_slices(src_shape:tuple,a:typing.Tuple[slicing], b:typing.Tuple[slicing]):
    res_slice = []
    i = 0
    j = 0
    while j<len(b):
        if i<len(a):
            a_slice = a[i]
        else:
            a_slice = slice(None,None,None)
        b_slice = b[j]
        if isinstance(a_slice, int):
            res_slice.append(a[i])
            i += 1
        elif isinstance(b_slice, int):
            res_slice.append(combine_slice_int(src_shape[i],a_slice,b_slice))
            i += 1
            j += 1
        else:
            res_slice.append(combine_two_slices(src_shape[i],a_slice,b_slice))
            i += 1
            j += 1

    if i<len(a):
        #print(src_shape,a,b,"=>",tuple(res_slice)+a[i:])
        return tuple(res_slice)+a[i:]
    #print(src_shape,a,b,"=>",tuple(res_slice))
    return tuple(res_slice)


def combine_slices(src_shape,a:slice_t,b:slice_t):
    if isinstance(a, int) and isinstance(b, int):
        return a+b
    else:
        if not isinstance(a,tuple):
            a = (a,)
        if not isinstance(b, tuple):
            b = (b,)
        return combine_two_tuple_slices(src_shape,a,b)
