import numpy as np
from .finder import comparing_binsearch

class ConservativeStorage(object):
    def __init__(self):
        self.on_store = None
        self.on_take = None
        self.last_source = None
        self.last_index = None

    def get_available(self):
        raise NotImplementedError("Cannot determine what is here")

    def get_first_accessible(self):
        avail = self.get_available()
        if avail:
            return avail[0]
        return None

    def store(self, item):
        raise NotImplementedError("Cannot store obj here")

    def take(self, *args):
        raise NotImplementedError("Cannot take obj from here")

    def is_empty(self):
        raise NotImplementedError("Cannot determine if storage is empty")

    def take_external(self, *args):
        item = self.take(*args)
        if item is not None and self.on_take:
            self.on_take()
        return item

    def store_external(self, item, source=None):
        success = self.store(item)
        if success and self.on_store:
            self.on_store()
        self.last_source = source
        return success


    def try_move_to(self, target, *args, callback=True):
        item = self.take(*args)
        if item is not None:
            if target.store(item):
                target.last_source = self
                if callback:
                    if target.on_store:
                        target.on_store()
                    if self.on_take:
                        self.on_take()
                return True
            else:
                self.store(item)
                return False
        return False

    def try_retract(self,*args, callback=True):
        if self.last_source is not None:
            return self.try_move_to(self.last_source,*args, callback=callback)
        return False

    def serialize(self):
        raise NotImplementedError("Cannot serialize storage")

    @staticmethod
    def deserialize(obj):
        raise NotImplementedError("Cannot deserialize storage")

    def deserialize_inplace(self, obj):
        raise NotImplementedError("Cannot deserialize storage inplace")



class ArrayStorage(ConservativeStorage):
    def __init__(self):
        super().__init__()
        self.storage = []

    def store(self, item):
        self.storage.append(item)
        self.last_index = len(self.storage)-1
        return True

    def get_available(self):
        return self.storage


    def take(self, index):
        if 0 <= index < len(self.storage):
            self.last_index = None
            return self.storage.pop(index)
        else:
            return None

    def is_empty(self):
        return not self.storage

    def clear(self):
        self.storage.clear()

    def serialize(self):
        return [item.serialize() for item in self.storage]

    @staticmethod
    def deserialize(obj):
        stor = [Interval.deserialize(item) for item in obj]
        res = ArrayStorage()
        res.storage = stor
        return res
        
    def deserialize_inplace(self, obj):
        stor = [Interval.deserialize(item) for item in obj]
        self.storage = stor

class SingleStorage(ConservativeStorage):
    def __init__(self):
        super().__init__()
        self.item = None

    def store(self, item):
        if self.item is None:
            self.last_index = 0
            self.item = item
            return True
        else:
            return False

    def take(self):
        item = self.item
        self.item = None
        self.last_index = None
        return item

    def drop(self):
        self.item = None

    def has_item(self):
        return self.item is not None

    def is_empty(self):
        return self.item is None

    def serialize(self):
        if self.has_item():
            return self.item.serialize()
        else:
            return None

    @staticmethod
    def deserialize(obj):
        if obj is None:
            item = None
        else:
            item = obj.deserialize()
        res = SingleStorage()
        res.item = item
        return res

    def deserialize_inplace(self, obj):
        if obj is None:
            item = None
        else:
            item = Interval.deserialize(obj)
        self.item = item


class Interval(object):
    def __init__(self,start,end):
        assert start<end
        self.start = start
        self.end = end
        assert isinstance(start,int)
        assert isinstance(end,int)

    def length(self):
        return self.end - self.start

    def inside_of(self,outer):
        return outer.start <= self.start and self.end <= outer.end

    def intersects(self,other):
        return self.start<other.end and other.start<self.end

    def subdivide(self):
        middle = (self.start+self.end)//2
        if middle == self.start:
            return None
        return Interval(self.start, middle), Interval(middle, self.end)

    def __repr__(self):
        return f"[{self.start}, {self.end})"

    def __str__(self):
        return f"[{self.start}, {self.end}) ({self.length()})"

    def __lt__(self, other):
        return self.start<other.start

    def __gt__(self, other):
        return self.start>other.start

    def is_same_as(self, other):
        return self.start == other.start and self.end == other.end

    def serialize(self):
        return [self.start, self.end]

    @staticmethod
    def deserialize(item):
        start,end = item
        return Interval(start, end)

    def to_arange(self):
        return np.arange(self.start, self.end)

    def to_istorage(self):
        return IntervalStorage(self.start,self.end)

    def to_slice(self):
        return slice(self.start, self.end)


class IntervalStorage(ConservativeStorage):
    def __init__(self, start, end, empty=False):
        super().__init__()
        self.outer = Interval(start,end)
        self.taken_intervals = []
        if empty:
            self.taken_intervals.append(Interval(start,end))

    def is_empty(self):
        if self.taken_intervals:
            take1 = self.taken_intervals[0]
            return take1.is_same_as(self.outer)
        return False

    def has_interval(self,interval):
        return interval.inside_of(self.outer)

    def get_available_index_to_take(self, interval:Interval):
        if not self.has_interval(interval):
            return None
        if self.taken_intervals:
            closest_i = comparing_binsearch(self.taken_intervals, interval)
            if self.taken_intervals[closest_i].intersects(interval):
                return None
            if closest_i>0 and self.taken_intervals[closest_i-1].intersects(interval):
                return None
            if closest_i<len(self.taken_intervals)-1 and self.taken_intervals[closest_i+1].intersects(interval):
                return None
            closest = self.taken_intervals[closest_i]
            if closest<interval:
                return closest_i+1
            elif closest>interval:
                return closest_i
            else:
                raise RuntimeError(f"Somehow got equal non-intersecting intervals {closest} and {interval}")

        else:
            return 0

    def get_available_index_to_store(self, interval:Interval):
        if not self.has_interval(interval):
            return None
        if self.taken_intervals:
            assert isinstance(interval, Interval)
            closest_i = comparing_binsearch(self.taken_intervals, interval)
            source_i = None
            if interval.inside_of(self.taken_intervals[closest_i]):
                source_i = closest_i
            if source_i is None \
                    and closest_i>0 \
                    and interval.inside_of(self.taken_intervals[closest_i-1]):
                source_i = closest_i-1
            if source_i is None \
                    and closest_i < len(self.taken_intervals) - 1 \
                    and self.taken_intervals[closest_i + 1].intersects(interval):
                source_i = closest_i+1

            return source_i

        else:
            return None

    def simplify(self):
        i = 0
        while i<len(self.taken_intervals)-1:
            e1 = self.taken_intervals[i].end
            s1 = self.taken_intervals[i + 1].start
            if e1<s1:
                i+=1
            else:
                assert e1==s1
                nextint = self.taken_intervals.pop(i + 1)
                s = self.taken_intervals[i].start
                e = nextint.end
                self.taken_intervals[i] = Interval(s, e)

    def simplify_from(self,index):
        while index<len(self.taken_intervals)-1:
            e1 = self.taken_intervals[index].end
            s1 = self.taken_intervals[index+1].start
            if e1<s1:
                return
            else:
                assert e1==s1
                nextint = self.taken_intervals.pop(index+1)
                s = self.taken_intervals[index].start
                e = nextint.end
                self.taken_intervals[index] = Interval(s,e)

    def take(self, interval:Interval):
        index_to_take = self.get_available_index_to_take(interval)
        if index_to_take is None:
            return None
        else:
            self.taken_intervals.insert(index_to_take,interval)
            self.simplify_from(max(index_to_take-1,0))
            self.last_index = None
            return interval

    def store(self, item:Interval):
        index = self.get_available_index_to_store(item)
        if index is None:
            return False
        target_interval = self.taken_intervals.pop(index)
        e2 = target_interval.end
        s2 = item.end
        if e2>s2:
            self.taken_intervals.insert(index,Interval(s2,e2))
        s1 = target_interval.start
        e1 = item.start
        if s1<e1:
            self.taken_intervals.insert(index,Interval(s1, e1))
        self.last_index = index
        return True

    def get_available(self):
        last = self.outer.start
        r = []
        for item in self.taken_intervals:
            if last<item.start:
                r.append(Interval(last, item.start))
            last = item.end
        if last<self.outer.end:
            r.append(Interval(last,self.outer.end))
        return r

    def get_first_accessible(self):
        if self.taken_intervals:
            first_taken_interval = self.taken_intervals[0]
            if first_taken_interval.start > self.outer.start:
                return Interval(self.outer.start, first_taken_interval.start)
            elif len(self.taken_intervals)==1:
                if first_taken_interval.is_same_as(self.outer):
                    return None
                return Interval(first_taken_interval.end,self.outer.end)
            else:
                second_taken_interval = self.taken_intervals[1]
                return Interval(first_taken_interval.end, second_taken_interval.start)
        else:
            return self.outer

    def __repr__(self):
        return str(self)

    def __str__(self):
        free = self.get_available()
        rs = [str(item) for item in free]
        return f"U({', '.join(rs)})"

    def serialize(self):
        outer = self.outer.serialize()
        taken = [item.serialize() for item in self.taken_intervals]
        return {
            "outer":outer,
            "taken":taken
        }

    @staticmethod
    def deserialize(obj):
        outer = obj["outer"]
        result = IntervalStorage(outer[0],outer[1])
        taken = obj["taken"]
        result.taken_intervals = [Interval.deserialize(item) for item in taken]
        result.simplify()
        return result

    def deserialize_inplace(self, obj):
        outer = obj["outer"]
        taken = obj["taken"]
        self.outer = outer
        self.taken_intervals = [Interval.deserialize(item) for item in taken]
        self.simplify()