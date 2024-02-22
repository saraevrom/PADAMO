import re
from datetime import datetime, timezone
import time


class Modifier(object):
    def __init__(self, key, delta_mul):
        self.key = key
        self.delta_mul = delta_mul

    def __call__(self, groups, editing):
        delta = int(groups[0])*self.delta_mul
        editing[self.key] += delta


# Y - year, M - month, D - day
# h - hour, m - minute, s - second, ms - millisecond
DATETIME_REGEXES = [
    (r"\s+", None),
    (r"(\d+)-(\d+)-(\d+)", "Y M D"),
    (r"(\d+):(\d+):(\d+):(\d+)", "h m s ms"),
    (r"(\d+):(\d+):(\d)+\.(\d+)", "h m s ms"),
    (r"(\d+):(\d+):(\d+)", "h m s"),
    (r"(\d+):(\d+)", "h m"),
    # sugar: When someone fails to understand ISO 8601
    (r"(\d+)\.(\d+)\.(\d+)", "D M Y"),
    (r"dmy\s*(\d+)/(\d+)/(\d+)","D M Y"),
    # manual entry
    (r"Y\s*=\s*(\d+)", "Y"),
    (r"M\s*=\s*(\d+)", "M"),
    (r"D\s*=\s*(\d+)", "D"),
    (r"h\s*=\s*(\d+)", "h"),
    (r"ms\s*=\s*(\d+)", "ms"),
    (r"m\s*=\s*(\d+)", "m"),
    (r"s\s*=\s*(\d+)", "s"),
    #Relative
    (r"Y\s*\+\s*(\d+)", Modifier("Y",1)),
    (r"M\s*\+\s*(\d+)", Modifier("M",1)),
    (r"D\s*\+\s*(\d+)", Modifier("D",1)),
    (r"h\s*\+\s*(\d+)", Modifier("h",1)),
    (r"ms\s*\+\s*(\d+)", Modifier("ms",1)),
    (r"m\s*\+\s*(\d+)", Modifier("m",1)),
    (r"s\s*\+\s*(\d+)", Modifier("s",1)),

    (r"Y\s*-\s*(\d+)", Modifier("Y", -1)),
    (r"M\s*-\s*(\d+)", Modifier("M", -1)),
    (r"D\s*-\s*(\d+)", Modifier("D", -1)),
    (r"h\s*-\s*(\d+)", Modifier("h", -1)),
    (r"ms\s*-\s*(\d+)", Modifier("ms", -1)),
    (r"m\s*-\s*(\d+)", Modifier("m", -1)),
    (r"s\s*-\s*(\d+)", Modifier("s", -1)),
]

for i in range(len(DATETIME_REGEXES)):
    src, mask = DATETIME_REGEXES[i]
    if hasattr(mask,"split"):
        mask = mask.split()
    DATETIME_REGEXES[i] = (re.compile(src), mask)



def match_string(s, start, editing_dict):
    for regex, mask in DATETIME_REGEXES:
        mat = regex.match(s, pos=start)
        if mat:
            if mask is None:
                pass
            elif isinstance(mask,list):
                groups = mat.groups()
                assert len(groups) == len(mask)
                for i in range(len(groups)):
                    editing_dict[mask[i]] = int(groups[i])
                #return {mask[i]: int(groups[i]) for i in range(len(groups))}, mat.end()
            else:
                groups = mat.groups()
                mask(groups,editing_dict)
            return mat.end()
    return None, None

def datetime_to_unixtime(dt):
    return (dt - datetime(1970, 1, 1)).total_seconds()


def parse_datetimes_dt(datetime_string, current_dt: datetime):
    start = 0
    data = {
        "Y":current_dt.year, "M":current_dt.month, "D":current_dt.day,
        "h":current_dt.hour, "m":current_dt.minute, "s":current_dt.second, "ms":current_dt.microsecond//1000
    }
    while start < len(datetime_string):
        end = match_string(datetime_string, start,data)
        if end is None:
            return current_dt
        start = end
        # if parsed is not None:
        #     data.update(parsed)
    try:
        print(data)
        dt = datetime(year=data["Y"], month=data["M"], day=data["D"],
                      hour=data["h"], minute=data["m"],second=data["s"], microsecond=data["ms"]*1000)
        return dt
    except ValueError:
        return current_dt


def parse_datetimes(datetime_string, current_dt: datetime):
    return datetime_to_unixtime(parse_datetimes_dt(datetime_string, current_dt))
