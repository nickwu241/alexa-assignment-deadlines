from datetime import datetime
import pytz

PACIFIC_TIMEZONE = pytz.timezone('US/Pacific')

def fmt_pst(dt):
    if not dt:
        return dt
    return dt.astimezone(PACIFIC_TIMEZONE).strftime('%a, %b %d %I:%M %p')

def now_utc():
    return datetime.now(tz=pytz.utc)

def parse_canvas_date(date_str):
    if not date_str:
        return date_str
    return datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=pytz.utc)

def fmt_timedelta(td):
    days = td.days
    hours = td.seconds // 3600
    minutes = td.seconds % 3600 // 60

    if days <= 0 and hours <= 0:
        return __pluralize(minutes, 'minute')

    result = []
    if days > 0:
        result.append(__pluralize(days, 'day'))
    if hours:
        result.append(__pluralize(hours, 'hour'))
    return ' and '.join(result)

def __pluralize(count, word):
    return '{:d} {:s}'.format(count, word if count == 1 else word + 's')
