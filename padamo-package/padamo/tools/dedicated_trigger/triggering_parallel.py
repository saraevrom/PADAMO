import multiprocessing.connection
import pickle
import gc
from multiprocessing import Process
from multiprocessing import Pipe

import numpy as np

from .storage import  Interval
from multiprocessing.connection import Connection
import numba as nb
from numba.typed.typedlist import List
from time import sleep

from padamo.tools.remote_explorer.login_form import PersistentConnection


@nb.njit()
def find_intervals(x):
    res_pos = List()
    res_neg = List()
    state = False
    rising_edge = 0
    falling_edge = 0
    for i in range(len(x)):
        v = x[i]
        if v and not state:
            rising_edge = i
            if rising_edge>falling_edge:
                res_neg.append((falling_edge,rising_edge))
            state = True
        if not v and state:
            falling_edge = i
            state = False
            if rising_edge < falling_edge:
                res_pos.append((rising_edge,falling_edge))
    if state:
        res_pos.append((rising_edge, len(x)))
    else:
        res_neg.append((falling_edge, len(x)))

    return res_pos, res_neg

class ParallelTrigger(Process):
    def __init__(self, signal_serialized:str, interval:Interval, batch_size:int, child_pipe:Connection):
        super().__init__()
        self.signal = pickle.loads(signal_serialized)
        self.interval = interval
        self.batch_size = batch_size
        self.pipe = child_pipe

    def run(self):
        PersistentConnection.reset()
        start = self.interval.start
        end = self.interval.end
        batch_size = self.batch_size
        current_index = start
        while current_index<end:
            cur_size = min(batch_size,end-current_index)
            self.pipe.send((current_index-start,))
            gc.collect()
            processed_data = self.signal.trigger.request_data(slice(current_index, current_index+cur_size))
            processed_data = np.logical_or.reduce(processed_data,axis=tuple(range(1,len(processed_data.shape))))
            #print(processed_data)
            intervals_pos, intervals_neg = find_intervals(processed_data)
            for istart,iend in intervals_pos:
                print("Found",istart+current_index, iend+current_index)
                self.pipe.send((istart+current_index, iend+current_index,True))

            for istart,iend in intervals_neg:
                print("Nothing is in", istart+current_index, iend+current_index)
                self.pipe.send((istart+current_index, iend+current_index,False))

            current_index += cur_size
        #sleep(1)
        self.pipe.send("END")
        while not self.pipe.poll():
            pass

class ParallelTriggerHandle(object):
    def __init__(self,signal_serialized, start_interval,batch_size):
        parent,child = Pipe()
        self.conn = parent
        self._stopped = False
        self.process = ParallelTrigger(signal_serialized, start_interval,batch_size, child)

    def start(self):
        self.process.start()

    def stop(self):
        if self._stopped:
            return
        self.conn.send("STOP")
        sleep(0.1)
        self._stopped = True
        if self.process.is_alive():
            self.process.terminate()
            self.process.join()

    def is_stopped(self):
        return self._stopped

    def poll_status(self):
        if not self.process.is_alive():
            return None
        if self.conn.poll():
            subint = self.conn.recv()
            if subint=="END":
                self.conn.send("STOP")
                return None
            return subint
        else:
            return None

    def poll_stati(self):
        res = []
        data = self.poll_status()
        while data is not None:
            res.append(data)
            data = self.poll_status()
        return res

    def is_alive(self):
        return self.process.is_alive()
