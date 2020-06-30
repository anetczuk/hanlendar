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
from dateutil.relativedelta import relativedelta

from .reminder import Reminder, Notification

from typing import List
from todocalendar.domainmodel.recurrent import RepeatType


class Task():
    """Task is entity that lasts over time."""

    def __init__(self):
        self.title                          = ""
        self.description                    = ""
        self.completed                      = 0        ## in range [0..100]
        self.priority                       = 10       ## lower number, greater priority
        self.startDate: datetime            = None
        self.dueDate: datetime              = None
        self.reminderList: List[Reminder]   = None
        self.recurrence                     = None

    def getReferenceDate(self):
        if self.startDate is None:
            ## deadline case
            return self.dueDate
        return self.startDate

    def setDefaultDateTime(self, start: datetime ):
        self.startDate = start
        self.dueDate = self.startDate + timedelta( hours=1 )

    def setDefaultDate(self, startDate: date):
        start = datetime.combine( startDate, time(10, 0, 0) )
        self.setDefaultDateTime( start )

    def setDeadline(self):
        self.startDate = None

    def setDeadlineDateTime(self, due: datetime ):
        self.startDate = None
        self.dueDate = due

    def setDeadlineDate(self, dueDate: date):
        due = datetime.combine( dueDate, time(10, 0, 0) )
        self.setDeadlineDateTime( due )

    def isCompleted(self):
        return self.completed >= 100

    def setCompleted(self):
        self.completed = 100

    def getNotifications(self):
        if self.dueDate is None:
            return list()
        currTime = datetime.today()
        ret = list()
        if self.dueDate > currTime:
            notif = Notification()
            notif.notifyTime = self.dueDate
            notif.task = self
            notif.message = "task '%s' reached deadline" % self.title
            ret.append( notif )

        if self.reminderList is None:
            return ret

        for reminder in self.reminderList:
            notif = Notification()
            notif.notifyTime = self.dueDate - reminder.getOffset()
            notif.task = self
            notif.message = reminder.printPretty()
            ret.append( notif )

        ret.sort( key=Notification.sortByTime )
        return ret

    def isTimedout(self):
        currTime = datetime.today()
        return currTime > self.dueDate

    def printRecurrent(self) -> str:
        if self.recurrence is None:
            return "None"
        if self.recurrence.every < 1:
            return "None"
        if self.recurrence.mode is RepeatType.NEVER:
            return "None"
        refDate = self.getReferenceDate()
        if self.recurrence.mode is RepeatType.DAILY:
            nextRepeat = refDate + relativedelta( days=1 )
            dateText = nextRepeat.strftime( "%Y-%m-%d %H:%M" )
            return dateText
        if self.recurrence.mode is RepeatType.WEEKLY:
            nextRepeat = refDate + relativedelta( days=7 )
            dateText = nextRepeat.strftime( "%Y-%m-%d %H:%M" )
            return dateText
        if self.recurrence.mode is RepeatType.MONTHLY:
            nextRepeat = refDate + relativedelta( months=1 )
            dateText = nextRepeat.strftime( "%Y-%m-%d %H:%M" )
            return dateText
        if self.recurrence.mode is RepeatType.YEARLY:
#             nextRepeat = refDate.replace( year = refDate.year + 1 )
            nextRepeat = refDate + relativedelta( years=1 )
            dateText = nextRepeat.strftime( "%Y-%m-%d %H:%M" )
            return dateText
        return "Unknown"

    def __str__(self):
        return "[t:%s d:%s c:%s p:%s sd:%s dd:%s rem:%s rec:%s]" % ( self.title, self.description, self.completed, self.priority,
                                                                     self.startDate, self.dueDate,
                                                                     self.reminderList, self.recurrence )

