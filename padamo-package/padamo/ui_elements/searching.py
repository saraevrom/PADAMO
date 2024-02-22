import numpy as np


def comparing_binsearch(array,target):
    '''
    Finds target in a sorted array.
    :param array: array for search.
    :param target: target element.
    :return: index of target in array.
    '''
    use_descend = array[0] > array[-1]
    start = 0
    end = len(array)
    middle = (start+end)//2
    while start!=middle:
        if target==array[middle]:
            return middle
        if (target < array[middle]) != use_descend:
            end = middle
            middle = (start+end)//2
        elif (target > array[middle]) != use_descend:
            start = middle
            middle = (start+end)//2
        else:
            raise RuntimeError(f"Unknown searching state reached {start},{middle},{end},{target}")

    return middle