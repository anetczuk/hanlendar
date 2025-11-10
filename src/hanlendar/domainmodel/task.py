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
import abc

from datetime import date, time, datetime, timedelta
from dateutil.relativedelta import relativedelta

from hanlendar.domainmodel.item import Item
from hanlendar.domainmodel.reminder import Reminder, Notification
from hanlendar.domainmodel import recurrent
from hanlendar.domainmodel.recurrent import Recurrent


_LOGGER = logging.getLogger(__name__)


class DateRange:

    def __init__(self, start=None, end=None):
        self.start: date = start
        self.end: date = end

    ## [] (array) operator
    def __getitem__(self, arg):
        if arg == 0:
            return self.start
        if arg == 1:
            return self.end
        message = "bad index: 0 or 1 allowed"
        raise IndexError(message)

    ## + (plus) operator
    def __add__(self, dateOffset):
        start = self.start
        if start is not None:
            start += dateOffset
        end = self.end
        if end is not None:
            end += dateOffset
        return DateRange(start, end)

    ## in keyword
    def __contains__(self, entryDate: date):
        if self.start is not None and entryDate < self.start:
            return False
        return not entryDate > self.end

    def isNormalized(self):
        if self.start is None:
            return False
        return self.end is not None

    def normalize(self):
        if self.start is None:
            self.start = self.end

    def isInMonth(self, monthDate: date):
        currDate = self.start
        if currDate is None:
            currDate = self.end
        return currDate.year == monthDate.year and currDate.month == monthDate.month

    def __str__(self):
        return f"[s:{self.start} e:{self.end}]"


## ========================================================================


class DateTimeRange:

    def __init__(self, start=None, end=None):
        self.start: datetime = start
        self.end: datetime = end

    ## [] (array) operator
    def __getitem__(self, arg):
        if arg == 0:
            return self.start
        if arg == 1:
            return self.end
        message = "bad index: 0 or 1 allowed"
        raise IndexError(message)

    ## + (plus) operator
    def __add__(self, dateOffset):
        start = self.start
        if start is not None:
            start += dateOffset
        end = self.end
        if end is not None:
            end += dateOffset
        return DateTimeRange(start, end)

    ## in keyword
    def __contains__(self, entryDate: datetime):
        if self.start is not None and entryDate < self.start:
            return False
        return not (self.end is not None and entryDate > self.end)

    def _key(self):
        return (self.start, self.end)

    def __hash__(self):
        return hash(self._key())

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return self._key() == other._key()

    def __str__(self):
        return f"[s:{self.start} e:{self.end}]"

    def __repr__(self):
        return f"[DTR {self.start} {self.end}]"

    def get_raw(self):
        return (self.start, self.end)

    def dateRange(self) -> DateRange:
        start = None
        if self.start is not None:
            start = self.start.date()
        end = None
        if self.end is not None:
            end = self.end.date()
        return DateRange(start, end)

    def isNormalized(self):
        if self.start is None:
            return False
        return self.end is not None

    def normalize(self):
        if self.start is None:
            self.start = self.end

    def isInMonth(self, monthDate: datetime):
        currDate = self.start
        if currDate is None:
            currDate = self.end
        if currDate is None:
            return False
        return currDate.year == monthDate.year and currDate.month == monthDate.month

    def isInPastMonths(self, monthDate: datetime):
        currDate = self.start
        if currDate is None:
            currDate = self.end
        if currDate is None:
            return False
        if currDate.year < monthDate.year:
            return True
        return currDate.year == monthDate.year and currDate.month < monthDate.month


## ========================================================================


class TaskOccurrence:
    """Occurrences of task.

    Regular task has only one occurrence.
    Recurrent tasks has many occurrences.
    """

    def __init__(self, task, datetime_range: DateTimeRange = None):
        if task is None:
            raise TypeError
        self.task = task
        if datetime_range is None:
            datetime_range = task.getDateTimeRange()
        self._dateRange = datetime_range

    def __str__(self):
        return f"[t:{self.task.title} {self.task.dueDateTime} range:{self.dateRange}]"

    def isValid(self):
        return self.dateRange is not None

    @property
    def title(self):
        return self.task.title

    @property
    def priority(self):
        return self.task.priority

    @property
    def completed(self):
        return self.task.completed

    @property
    def start(self):
        return self.dateRange.start

    @property
    def startCurrent(self):
        subOccurrences = self.task.subOccurrences()
        retDate = self.start
        for currItem in subOccurrences:
            if currItem.start is None:
                continue
            if retDate is None:
                retDate = currItem.start
            else:
                retDate = min(currItem.start, retDate)
        return retDate

    @property
    def due(self):
        return self.dateRange.end

    @property
    def dueCurrent(self):
        subOccurrences = self.task.subOccurrences()
        retDate = self.due
        for currItem in subOccurrences:
            if currItem.due is None:
                continue
            retDate = currItem.due if retDate is None else min(currItem.due, retDate)
        return retDate

    def isCompleted(self):
        if self.dateRange.end < self.task.dueDateTime:
            return True
        return self.task.isCompleted()

    def isTimedout(self):
        if self.dateRange.end is None:
            return False
        currTime = datetime.today()
        return currTime > self.dateRange.end

    def isReminded(self):
        if self.dateRange.end is None:
            return False
        retOffset = self.task.getReminderGreatest()
        if retOffset is None:
            return False
        currTime = datetime.today()
        notifTime = self.dateRange.end - retOffset
        return not notifTime > currTime

    @property
    def dateRange(self):
        if hasattr(self, "_dateRange") and self._dateRange is not None:
            return self._dateRange
        return None

    def getFirstDateTime(self):
        return self.task.getFirstDateTime()

    def isInMonth(self, monthDate: date):
        return self.dateRange.isInMonth(monthDate)

    def isInPastMonths(self, monthDate: date):
        return self.dateRange.isInPastMonths(monthDate)

    def calculateTimeSpan(self, entryDate: date):
        startDate = self.task.startDateTime
        endDate = self.task.dueDateTime
        ret = calc_time_span(entryDate, startDate, endDate)
        if ret is not None:
            return ret

        recurrence = self.task.getAppliedRecurrence()
        if recurrence is None:
            return [0, 1]
        recurrentDateOffset: relativedelta = recurrence.getDateOffset()
        if recurrentDateOffset is None:
            return [0, 1]

        multiplicator = recurrent.find_multiplication_after(endDate.date(), entryDate, recurrentDateOffset)
        if multiplicator < 0:
            return [0, 1]
        endDate += recurrentDateOffset * multiplicator
        if startDate is not None:
            startDate += recurrentDateOffset * multiplicator
        ret = calc_time_span(entryDate, startDate, endDate)
        if ret is not None:
            return ret
        return [0, 1]

    @staticmethod
    def sortByDates(entry):
        ## entry.dateRange[0] can be None
        if entry.dateRange[0] is None:
            return (entry.dateRange[1],)
        return (entry.dateRange[1], entry.dateRange[0])


## ========================================================================
## ========================================================================


class Task(Item):
    """Task is entity that lasts over time."""

    @abc.abstractmethod
    def _getCreateDateTime(self) -> datetime:
        message = "You need to define this method in derived class!"
        raise NotImplementedError(message)

    @abc.abstractmethod
    def _getStartDateTime(self) -> datetime:
        message = "You need to define this method in derived class!"
        raise NotImplementedError(message)

    @abc.abstractmethod
    def _setStartDateTime(self, _value: datetime):
        message = "You need to define this method in derived class!"
        raise NotImplementedError(message)

    @abc.abstractmethod
    def _getDueDateTime(self) -> datetime:
        message = "You need to define this method in derived class!"
        raise NotImplementedError(message)

    @abc.abstractmethod
    def _setDueDateTime(self, _value: datetime):
        message = "You need to define this method in derived class!"
        raise NotImplementedError(message)

    @property
    def createDateTime(self) -> datetime:
        return self._getCreateDateTime()

    @property
    def startDateTime(self) -> datetime:
        return self._getStartDateTime()

    @property
    def dueDateTime(self) -> datetime:
        return self._getDueDateTime()

    def setOccurrence(self, start: datetime, due: datetime):
        start = ensure_date_time(start)
        due = ensure_date_time(due)
        self._setStartDateTime(start)
        self._setDueDateTime(due)

    def setOccurrenceDue(self, due: datetime):
        self._setStartDateTime(None)
        due = ensure_date_time(due)
        self._setDueDateTime(due)

    def setDefaultDateTime(self, start: datetime):
        start = ensure_date_time(start)
        due = start + timedelta(hours=1)
        self.setOccurrence(start, due)

    def setDefaultDate(self, startDate: date):
        start = datetime.combine(startDate, time(10, 0, 0))
        self.setDefaultDateTime(start)

    def setDeadline(self):
        self._setStartDateTime(None)

    def setDeadlineDateTime(self, due: datetime):
        self.setOccurrenceDue(due)

    def getReferenceDateTime(self) -> datetime:
        if self.startDateTime is not None:
            return self.startDateTime
        ## deadline case
        return self.dueDateTime

    @abc.abstractmethod
    def _getCompletedList(self) -> list[DateTimeRange]:
        message = "You need to define this method in derived class!"
        raise NotImplementedError(message)

    @property
    def completedList(self) -> list[DateTimeRange]:
        return self._getCompletedList()

    ## ========================================================================

    @abc.abstractmethod
    def _getRecurrence(self):
        message = "You need to define this method in derived class!"
        raise NotImplementedError(message)

    @abc.abstractmethod
    def _setRecurrence(self, _value):
        message = "You need to define this method in derived class!"
        raise NotImplementedError(message)

    @property
    def recurrence(self) -> Recurrent:
        return self._getRecurrence()

    @recurrence.setter
    def recurrence(self, value: Recurrent):
        self._setRecurrence(value)

    def getAppliedRecurrence(self) -> Recurrent:
        recurrence = self._getRecurrence()
        if recurrence is None:
            return None
        if recurrence.isAsParent() is False:
            return recurrence
        parent = self.getParent()
        if parent is None:
            return None
        return parent.getAppliedRecurrence()

    ## ========================================================================

    def currentOccurrence(self) -> TaskOccurrence:
        dateRange = self.getDateTimeRange()
        return TaskOccurrence(self, datetime_range=dateRange)

    def subOccurrences(self) -> list[TaskOccurrence]:
        subitems = self.getSubitems()
        if subitems is None:
            return []
        ret = []
        for currItem in subitems:
            currOccurrence: TaskOccurrence = currItem.currentOccurrence()
            ret.append(currOccurrence)
        return ret

    ## return TaskOccurrence for given date
    ## returns None if no occurrence in given date
    def getTaskOccurrenceForDate(self, entryDate: date) -> TaskOccurrence:
        startDueRange: DateTimeRange = self.getDateTimeRange()
        dateRange: DateRange = startDueRange.dateRange()
        dateRange.normalize()
        if dateRange.isNormalized() is False:
            return None
        if entryDate in dateRange:
            return TaskOccurrence(self)

        recurr = self.getAppliedRecurrence()
        if recurr is None:
            return None

        if recurr.endDate is not None and recurr.endDate < entryDate:
            return None

        completedList = self.completedList
        for item in completedList:
            itemRange: DateRange = item.dateRange()
            itemRange.normalize()
            if itemRange.isNormalized() is False:
                return None
            if entryDate in itemRange:
                return TaskOccurrence(self, datetime_range=item)

        recurrentDateOffset: relativedelta = recurr.getDateOffset()
        if recurrentDateOffset is None:
            return None

        multiplicator = recurrent.find_multiplication_after(dateRange.end, entryDate, recurrentDateOffset)
        if multiplicator < 1:
            return None
        dateRange += recurrentDateOffset * multiplicator
        if entryDate in dateRange:
            datetime_range = self.getOccurrenceDateTimeRange(multiplicator)
            return TaskOccurrence(self, datetime_range=datetime_range)

        return None

    ## ========================================================================

    ## return smallest date from: occurrenceStart, occurrenceDue and reminder date
    def getFirstDateTime(self) -> datetime:
        if self.dueDateTime is None:
            return None
        minDate = self.dueDateTime
        if self.startDateTime is not None and self.startDateTime < minDate:
            minDate = self.startDateTime
        remindDate = self.getReminderFirstDate()
        if remindDate is not None and remindDate < minDate:
            minDate = remindDate
        return minDate

    def getDateTimeRange(self) -> DateTimeRange:
        startDate = self._getStartDateTime()
        endDate = self._getDueDateTime()
        return DateTimeRange(startDate, endDate)

    def getOccurrenceDateTimeRange(self, offset: int = 0) -> DateTimeRange:
        dateRange: DateTimeRange = self.getDateTimeRange()
        if dateRange is None:
            return DateTimeRange()
        if offset != 0:
            recurrence: Recurrent = self.getAppliedRecurrence()
            if recurrence is not None:
                recurrenceOffset = recurrence.getDateOffset()
                dateRange += recurrenceOffset * offset
        return dateRange

    ## ========================================================================

    @abc.abstractmethod
    def _getReminderList(self):
        message = "You need to define this method in derived class!"
        raise NotImplementedError(message)

    @abc.abstractmethod
    def _setReminderList(self, _values):
        message = "You need to define this method in derived class!"
        raise NotImplementedError(message)

    @property
    def reminderList(self):
        return self._getReminderList()

    @reminderList.setter
    def reminderList(self, values):
        self._setReminderList(values)

    def addReminder(self, reminder=None):
        reminderList = self._getReminderList()
        if reminderList is None:
            reminderList = []
            self._setReminderList(reminderList)
        if reminder is None:
            reminder = Reminder()
        reminderList.append(reminder)
        return reminder

    def addReminderDays(self, days=1):
        reminder = Reminder()
        reminder.setDays(days)
        self.addReminder(reminder)

    def getReminderFirstDate(self) -> datetime:
        if self.dueDateTime is None:
            return None
        reminderList = self._getReminderList()
        if reminderList is None:
            return None
        retOffset = self.getReminderGreatest()
        if retOffset is None:
            return None
        return self.dueDateTime - retOffset

    def getReminderGreatest(self) -> timedelta:
        reminderList = self._getReminderList()
        if reminderList is None:
            return None
        retOffset = None
        for reminder in reminderList:
            if retOffset is None:
                retOffset = reminder.getOffset()
                continue
            currOffset = reminder.getOffset()
            retOffset = max(retOffset, currOffset)
        return retOffset

    ## ========================================================================

    def getNotifications(self) -> list[Notification]:
        if self.dueDateTime is None:
            return []
        currTime = datetime.today()
        ret: list[Notification] = []
        if self.dueDateTime > currTime:
            notif = Notification()
            notif.notifyTime = self.dueDateTime
            notif.task = self
            notif.message = f"task '{self.title}' reached deadline"
            ret.append(notif)

        reminderList = self._getReminderList()
        if reminderList is None:
            return ret

        for reminder in reminderList:
            notifTime = self.dueDateTime - reminder.getOffset()
            if notifTime > currTime:
                notif = Notification()
                notif.notifyTime = notifTime
                notif.task = self
                notif.message = f"task '{self.title}': {reminder.printPretty()}"
                ret.append(notif)

        ret.sort(key=Notification.sortByTime)
        return ret

    @abc.abstractmethod
    def addSubTask(self):
        message = "You need to define this method in derived class!"
        raise NotImplementedError(message)

    def printNextRecurrence(self) -> str:
        recurr = self.getAppliedRecurrence()
        if recurr is None:
            return "None"
        refDate = self.getReferenceDateTime()
        nextRepeat = recurr.nextDateTime(refDate)
        if nextRepeat is None:
            return "None"
        return nextRepeat.strftime("%Y-%m-%d %H:%M")

    def _progressRecurrence(self) -> bool:
        recurr: Recurrent = self.getAppliedRecurrence()
        if recurr is None or recurr.isValid() is False:
            return False
        recurrent_date_offset = recurr.getDateOffset()
        nextDueDate = self.dueDateTime + recurrent_date_offset
        nextDate = nextDueDate.date()
        if recurr.isEnd(nextDate):
            return False
        nextStartDate = self.startDateTime
        if nextStartDate is not None:
            nextStartDate += recurrent_date_offset
        self.setOccurrence(nextStartDate, nextDueDate)
        return True

    @staticmethod
    def sortByDates(task):
        return (task.dueDateTime, task.startDateTime)


## ========================================================================
## ========================================================================


def calc_time_span(entryDate: date, start: datetime, end: datetime):
    startFactor = 0.0
    if start is not None:
        startDate = start.date()
        if entryDate < startDate:
            return None
        if entryDate == startDate:
            midnight = datetime.combine(entryDate, datetime.min.time())
            startDiff = start - midnight
            daySecs = timedelta(days=1).total_seconds()
            startFactor = startDiff.total_seconds() / timedelta(days=1).total_seconds()
    dueFactor = 1.0
    if end is not None:
        endDate = end.date()
        if entryDate > endDate:
            return None
        if entryDate == endDate:
            midnight = datetime.combine(entryDate, datetime.min.time())
            startDiff = end - midnight
            daySecs = timedelta(days=1).total_seconds()
            dueFactor = startDiff.total_seconds() / daySecs
    return [startFactor, dueFactor]


def ensure_date_time(value):
    if value is None:
        return value
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        value = datetime.combine(value, datetime.min.time())
    _LOGGER.warning("unknown type: %s %s", value, type(value))
    return None
