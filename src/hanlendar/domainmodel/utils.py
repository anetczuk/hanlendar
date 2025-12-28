# MIT License
#
# Copyright (c) 2020 Arkadiusz Netczuk <dev.arnet@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

import logging
import uuid
import datetime


_LOGGER = logging.getLogger(__name__)


DateDateTime = datetime.date | datetime.datetime


def ensure_date_time(value: DateDateTime) -> datetime.datetime:
    if value is None:
        return value
    if isinstance(value, datetime.datetime):
        return value
    if isinstance(value, datetime.date):
        new_dt = datetime.datetime(value.year, value.month, value.day)
        return new_dt.astimezone()  ## convert to local timezone
    _LOGGER.warning("unknown type: %s %s", value, type(value))
    return None


def generate_uid() -> str:
    return str(uuid.uuid4())
    # return str(uuid.uuid4()) + "@hanlendar"


def hashable_object(obj):
    if isinstance(obj, (set, list, tuple)):
        items_list = [hashable_object(item) for item in obj]
        return tuple(items_list)
    if isinstance(obj, dict):
        items_list = [(hashable_object(key), hashable_object(item)) for key, item in obj.items()]
        return hashable_object(items_list)
    return obj


def is_offset_naive(dt: datetime.datetime) -> bool:
    return dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None


def compare_datetime_today(date_time: datetime.datetime) -> bool:
    currTime: datetime.datetime = None
    if is_offset_naive(date_time):
        currTime = datetime.datetime.today()
    else:
        currTime = datetime.datetime.now(datetime.timezone.utc)
    return date_time > currTime
