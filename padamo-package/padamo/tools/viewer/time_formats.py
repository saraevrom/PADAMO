import datetime
import numpy as np
from .animation_job import DATETIME_FORMAT

class TimeFormat(object):
    @staticmethod
    def format_time(frame, unixtime):
        raise NotImplementedError

    @staticmethod
    def time_xs(time_view, start,end):
        raise NotImplementedError


class FrameFormat(TimeFormat):
    @staticmethod
    def format_time(frame, unixtime):
        return f"Frame #{frame}"

    @staticmethod
    def time_xs(time_view, start,end):
        return np.arange(start,end)


class UnixTimeFormat(TimeFormat):
    @staticmethod
    def format_time(frame, unixtime):
        return f"{unixtime:.3f}"

    @staticmethod
    def time_xs(time_view, start,end):
        return time_view.request_data(slice(start,end))

class UTCTimeFormat(TimeFormat):
    @staticmethod
    def format_time(frame, unixtime):
        dt = datetime.datetime.utcfromtimestamp(float(unixtime))
        return dt.strftime(DATETIME_FORMAT)

    @staticmethod
    def time_xs(time_view, start,end):
        unixtime = time_view.request_data(slice(start,end))
        times = np.array([datetime.datetime.utcfromtimestamp(float(x)) for x in unixtime])
        return times
