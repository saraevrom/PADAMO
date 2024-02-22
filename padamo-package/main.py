#!/usr/bin/env python3
import multiprocessing
from padamo import run


if __name__ == '__main__':
    # import matplotlib
    # print("MATPLOTLIB CACHE DIR", matplotlib.get_cachedir())
    multiprocessing.freeze_support()
    run()