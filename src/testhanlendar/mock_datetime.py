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


##
## Following code is based on:
##    https://blog.xelnor.net/python-mocking-datetime/
##


import datetime
import unittest.mock as mock


real_date_class     = datetime.date
real_datetime_class = datetime.datetime


def mock_date_meta(target):
    class DateSubclassMeta(type):
        @classmethod
        def __instancecheck__(mcs, obj):
            return isinstance(obj, real_date_class)

    class BaseMockedDate(real_date_class):
        @classmethod
        def now(cls, tz=None):
            return target.replace(tzinfo=tz)

        @classmethod
        def today(cls):
            return target

        @classmethod
        def utcnow(cls):
            return target

    # Python2 & Python3 compatible metaclass
    MockedDate = DateSubclassMeta('date', (BaseMockedDate,), {})
    return MockedDate


def get_mock_date(value, module=datetime):
    MockedDate = mock_date_meta(value)
    ## moduke/object, attribute, new value
    ## more info: https://docs.python.org/3/library/unittest.mock.html#patch-object
    return mock.patch.object( module, 'date', MockedDate )


def mock_date(value, module=datetime):
    MockedDate = mock_date_meta(value)
    ## moduke/object, attribute, new value
    ## more info: https://docs.python.org/3/library/unittest.mock.html#patch-object
    obj = mock.patch.object( module, 'date', MockedDate )
    obj.start()
    return obj


def mock_datetime_meta(value):
    class DatetimeSubclassMeta(type):
        @classmethod
        def __instancecheck__(mcs, obj):
            return isinstance(obj, real_datetime_class)

    class BaseMockedDatetime(real_datetime_class):
        @classmethod
        def now(cls, tz=None):
            return value.replace(tzinfo=tz)

        @classmethod
        def today(cls):
            return value

        @classmethod
        def utcnow(cls):
            return value

    # Python2 & Python3 compatible metaclass
    MockedDatetime = DatetimeSubclassMeta('datetime', (BaseMockedDatetime,), {})
    return MockedDatetime


def get_mock_datetime( value, module=datetime ):
    MockedDatetime = mock_datetime_meta(value)
    ## moduke/object, attribute, new value
    ## more info: https://docs.python.org/3/library/unittest.mock.html#patch-object
    return mock.patch.object(module, 'datetime', MockedDatetime)


def mock_datetime( value, module=datetime ):
    MockedDatetime = mock_datetime_meta(value)
    ## moduke/object, attribute, new value
    ## more info: https://docs.python.org/3/library/unittest.mock.html#patch-object
    obj = mock.patch.object(module, 'datetime', MockedDatetime)
    obj.start()
    return obj
