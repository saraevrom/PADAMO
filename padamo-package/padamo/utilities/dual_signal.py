from padamo.lazy_array_operations import LazyArrayOperation
from typing import Optional

class SignalShapeError(Exception):
    pass

class NoneGetter(object):
    def __getitem__(self, item):
        return None

class Signal(object):
    def __init__(self, space:LazyArrayOperation, time:LazyArrayOperation, trigger:Optional[LazyArrayOperation]=None):
        assert isinstance(space, LazyArrayOperation)
        assert isinstance(time, LazyArrayOperation)
        time_shape = time.shape()
        if len(time_shape)>1:
            if len(time_shape) == 2 and time_shape[1] == 1:
                print("MATLAB time detected", time_shape)
                time = time[:, 0]
            else:
                raise IndexError(f"Time dimensions are not compatible {time_shape}", self)
        del time_shape # Not needed anymore but can confuse afterwards

        spaceshape = space.shape()
        timeshape = time.shape()

        if not (spaceshape and timeshape):
            raise SignalShapeError("Cannot make signal out of empty arrays")
        if spaceshape[0] != timeshape[0]:
            raise SignalShapeError(f"Array length mismatch (space: {spaceshape[0]}, time: {timeshape[0]})")
        self.space = space
        self.time = time

        if trigger is not None:
            trigger_shape = trigger.shape()
            if not trigger_shape:
                raise SignalShapeError("Trigger array is empty")
            if trigger_shape[0] != time.shape()[0]:
                raise SignalShapeError(f"Array length mismatch (trigger: {trigger_shape[0]}, time: {timeshape[0]})")
        self.trigger = trigger

    def clone(self):
        return Signal(self.space, self.time, self.trigger)

    def get_trigger(self):
        if self.trigger is None:
            return NoneGetter()
        else:
            return self.trigger

    def _get_trigger_item(self,item):
        if self.trigger is None:
            return None
        else:
            return self.trigger[item]

    def request_trigger_data(self, item):
        if self.trigger is None:
            return None
        else:
            return self.trigger.request_data(item)

    def _concatenate_triggers(self,other):
        if self.trigger is None or other.trigger is None:
            return None
        else:
            return self.trigger.extend(other.trigger)

    def __getitem__(self, item):
        return Signal(self.space[item], self.time[item], self._get_trigger_item(item))

    # def request_data(self,item):
    #     return Signal(self.space.request_data(item), self.time.request_data(item), self._request_trigger_item(item))

    def length(self):
        return self.time.shape()[0]

    def extend(self,other):
        space_concat = self.space.extend(other.space)
        time_concat = self.time.extend(other.time)
        trigger = self._concatenate_triggers(other)
        return Signal(space_concat, time_concat, trigger)
