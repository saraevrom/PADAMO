import numpy as np

# Implementation that works with intervals
def comparing_binsearch(array,target):
    '''
    Finds target in a sorted array.
    :param array: array for search.
    :param target: target element.
    :return: index of target in array.
    '''
    start = 0
    end = len(array)
    middle = (start+end)//2
    while start!=middle:
        if target<array[middle]:
            end = middle
            middle = (start+end)//2
        elif target>array[middle]:
            start = middle
            middle = (start+end)//2
        else:
            return middle

    return middle