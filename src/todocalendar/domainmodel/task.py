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

from datetime import date, time, datetime, timedelta


class Task():
    """Task is entity that lasts over time."""

    def __init__(self):
        self.title               = ""
        self.description         = ""
        self.completed           = 0        ## in range [0..100]
        self.priority            = 10       ## lower number, greater priority
        self.startDate: datetime = None
        self.dueDate: datetime   = None
        self.reminder            = None
        self.recurrence          = None

    def setDefaultDateTime(self, start: datetime ):
        self.startDate = start
        self.dueDate = self.startDate + timedelta( hours=1 )

    def setDefaultDate(self, startDate: date):
        start = datetime.combine( startDate, time(10, 0, 0) )
        self.setDefaultDateTime( start )

    def setCompleted(self):
        self.completed = 100

    def __str__(self):
        return "[t:%s d:%s c:%s p:%s sd:%s dd:%s rem:%s rec:%s]" % ( self.title, self.description, self.completed, self.priority,
                                                                     self.startDate, self.dueDate,
                                                                     self.reminder, self.recurrence )

