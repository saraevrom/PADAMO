from datetime import datetime
from padamo.ui_elements.datetime_parser import parse_datetimes_dt
import json

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


def make_stamp(dt:datetime):
    sec_string = dt.strftime(DATETIME_FORMAT)
    ms = dt.microsecond//1000
    return sec_string + f":{ms}"


def parse_bookmark(ts):
    start, end = ts.split(";")
    now = datetime.now()  # Reference point
    start_time = parse_datetimes_dt(start, now)
    end_time = parse_datetimes_dt(end, start_time)
    return start_time,end_time

class Bookmark(object):
    def __init__(self, starttime:datetime, endtime:datetime, description=""):
        self.starttime = starttime
        self.endtime = endtime
        self.description = description

    def sort_key(self):
        return self.starttime.timestamp()

    def title(self):
        return make_stamp(self.starttime)

    def make_timestamp(self):
        start = make_stamp(self.starttime)
        end = make_stamp(self.endtime)
        return f"{start};{end}"

    @staticmethod
    def from_timestamp(ts:str):
        start_time, end_time = parse_bookmark(ts)
        if start_time is None or end_time is None:
            return None
        return Bookmark(start_time,end_time)

    def serialize(self):
        return {
            "time":self.make_timestamp(),
            "description":self.description
        }

    @staticmethod
    def deserialize(data):
        stamp = data["time"]
        obj = Bookmark.from_timestamp(stamp)
        obj.description = data["description"]
        return obj

    def serialize_string(self):
        time = self.make_timestamp()
        if len(time)<47:
            time += " "*(47-len(time))
        desc = self.description
        return time+desc

    @staticmethod
    def deserialize_string(s):
        time = s[:47]
        desc = s[47:]
        start, end = parse_bookmark(time)
        return Bookmark(start, end, desc)
