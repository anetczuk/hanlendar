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

from typing import List
from datetime import date, time, datetime, timedelta
from dateutil.relativedelta import relativedelta

from hanlendar.domainmodel.item import Item
from hanlendar.domainmodel.reminder import Reminder, Notification
from hanlendar.domainmodel import recurrent
from hanlendar.domainmodel.recurrent import Recurrent


_LOGGER = logging.getLogger(__name__)


class DateRange():

    def __init__(self, start=None, end=None ):
        self.start: date = start
        self.end:   date = end

    ## [] (array) operator
    def __getitem__(self, arg):
        if arg == 0:
            return self.start
        if arg == 1:
            return self.end
        raise IndexError( "bad index: 0 or 1 allowed" )

    ## + (plus) operator
    def __add__(self, dateOffset):
        start = self.start
        if start is not None:
            start += dateOffset
        end = self.end
        if end is not None:
            end += dateOffset
        return DateRange( start, end )

    ## in keyword
    def __contains__(self, entryDate: date):
        if self.start is not None and entryDate < self.start:
            return False
        if entryDate > self.end:
            return False
        return True

    def isNormalized(self):
        if self.start is None:
            return False
        if self.end is None:
            return False
        return True

    def normalize(self):
        if self.start is None:
            self.start = self.end

    def isInMonth( self, monthDate: date ):
        currDate = self.start
        if currDate is None:
            currDate = self.end
        if currDate.year == monthDate.year and currDate.month == monthDate.month:
            return True
        return False

    def __str__(self):
        return "[s:%s e:%s]" % ( self.start, self.end )


## ========================================================================


class DateTimeRange():

    def __init__(self, start=None, end=None ):
        self.start: datetime = start
        self.end:   datetime = end

    ## [] (array) operator
    def __getitem__(self, arg):
        if arg == 0:
            return self.start
        if arg == 1:
            return self.end
        raise IndexError( "bad index: 0 or 1 allowed" )

    ## + (plus) operator
    def __add__(self, dateOffset):
        start = self.start
        if start is not None:
            start += dateOffset
        end = self.end
        if end is not None:
            end += dateOffset
        return DateTimeRange( start, end )

    ## in keyword
    def __contains__(self, entryDate: datetime):
        if self.start is not None and entryDate < self.start:
            return False
        if self.end is not None and entryDate > self.end:
            return False
        return True

    def dateRange(self) -> DateRange:
        start = None
        if self.start is not None:
            start = self.start.date()
        end = None
        if self.end is not None:
            end = self.end.date()
        return DateRange( start, end )

    def isNormalized(self):
        if self.start is None:
            return False
        if self.end is None:
            return False
        return True

    def normalize(self):
        if self.start is None:
            self.start = self.end

    def isInMonth( self, monthDate: datetime ):
        currDate = self.start
        if currDate is None:
            currDate = self.end
        if currDate is None:
            return False
        if currDate.year == monthDate.year and currDate.month == monthDate.month:
            return True
        return False

    def isInPastMonths( self, monthDate: datetime ):
        currDate = self.start
        if currDate is None:
            currDate = self.end
        if currDate is None:
            return False
        if currDate.year < monthDate.year:
            return True
        if currDate.year == monthDate.year and currDate.month < monthDate.month:
            return True
        return False

    def __str__(self):
        return "[s:%s e:%s]" % ( self.start, self.end )


## ========================================================================


class TaskOccurrence:
    """Occurrences of task.

    Regular task has only one occurrence.
    Recurrent tasks has many occurrences.
    """

    def __init__(self, task, offset=0):
        if task is None:
            raise TypeError
        self.task                      = task
        self.offset                    = offset         ## recurrence offset
        self._dateRange: DateTimeRange = None           ## cache

    def isValid(self):
        if self.dateRange is None:
            return False
        return True

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
        subOccurrences = self.task.subOccurences()
        retDate = self.start
        for currItem in subOccurrences:
            if currItem.start is None:
                continue
            if retDate is None:
                retDate = currItem.start
            else:
                retDate = min( currItem.start, retDate )
        return retDate

    @property
    def due(self):
        return self.dateRange.end

    @property
    def dueCurrent(self):
        subOccurrences = self.task.subOccurences()
        retDate = self.due
        for currItem in subOccurrences:
            if currItem.due is None:
                continue
            if retDate is None:
                retDate = currItem.due
            else:
                retDate = min( currItem.due, retDate )
        return retDate

    def isCompleted(self):
        if self.offset < self.task.recurrentOffset:
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
        if notifTime > currTime:
            return False
        return True

    @property
    def dateRange(self):
        if hasattr(self, '_dateRange') and self._dateRange is not None:
            return self._dateRange

        dateRange: DateTimeRange = self.task.getDateTimeRange()
        if dateRange is None:
            self._dateRange = DateTimeRange()
            return self._dateRange
        if self.offset != 0:
            recurrenceOffset = self.task.getAppliedRecurrence().getDateOffset()
            dateRange += recurrenceOffset * self.offset
        self._dateRange = dateRange
        return self._dateRange

    def getFirstDateTime(self):
        return self.task.getFirstDateTime()

    def isInMonth( self, monthDate: date ):
        return self.dateRange.isInMonth( monthDate )

    def isInPastMonths( self, monthDate: date ):
        return self.dateRange.isInPastMonths( monthDate )

    def calculateTimeSpan(self, entryDate: date):
        startDate = self.task.occurrenceStart
        endDate   = self.task.occurrenceDue
        ret = calc_time_span( entryDate, startDate, endDate )
        if ret is not None:
            return ret

        recurrence = self.task.getAppliedRecurrence()
        if recurrence is None:
            return [0, 1]
        recurrentOffset: relativedelta = recurrence.getDateOffset()
        if recurrentOffset is None:
            return [0, 1]

        multiplicator = recurrent.find_multiplication_after( endDate.date(), entryDate, recurrentOffset )
        if multiplicator < 0:
            return [0, 1]
        endDate += recurrentOffset * multiplicator
        if startDate is not None:
            startDate += recurrentOffset * multiplicator
        ret = calc_time_span( entryDate, startDate, endDate )
        if ret is not None:
            return ret
        return [0, 1]

    def __str__(self):
        return "[t:%s %s off:%s range:%s]" % ( self.task.title, self.task.occurrenceDue, self.offset, self.dateRange )

    @staticmethod
    def sortByDates( entry ):
        return ( entry.dateRange[1], entry.dateRange[0] )


## ========================================================================
## ========================================================================


class Task( Item ):
    """Task is entity that lasts over time."""

    def __init__(self):
        super(Task, self).__init__()

    @abc.abstractmethod
    def _getStartDateTime(self):
        raise NotImplementedError('You need to define this method in derived class!')

    @abc.abstractmethod
    def _setStartDateTime(self, value):
        raise NotImplementedError('You need to define this method in derived class!')

    @property
    def startDateTime(self):
        return self._getStartDateTime()

    @startDateTime.setter
    def startDateTime(self, value):
        value = ensure_date_time( value )
        self._setStartDateTime( value )
        self._setRecurrentOffset( 0 )

    ## ========================================================================

    @abc.abstractmethod
    def _getDueDateTime(self):
        raise NotImplementedError('You need to define this method in derived class!')

    @abc.abstractmethod
    def _setDueDateTime(self, value):
        raise NotImplementedError('You need to define this method in derived class!')

    @property
    def dueDateTime(self):
        return self._getDueDateTime()
 
    @dueDateTime.setter
    def dueDateTime(self, value):
        value = ensure_date_time( value )
        self._setDueDateTime( value )
        self._setRecurrentOffset( 0 )

    ## ========================================================================

    @property
    def occurrenceStart(self):
        startDate = self._getStartDateTime()
        recurrenceDate = self._getRecurrenceDate( startDate )
        if recurrenceDate is not None:
            return recurrenceDate
        return startDate
 
    @occurrenceStart.setter
    def occurrenceStart(self, value):
        relativeDate = self._getRecurrenceRelative()
        if relativeDate is None:
            self._setStartDateTime( value )
            return
        diff = value - relativeDate
        self._setStartDateTime( diff )

    ## ========================================================================

    @property
    def occurrenceDue(self):
        dueDate = self._getDueDateTime()
        recurrenceDate = self._getRecurrenceDate( dueDate )
        if recurrenceDate is not None:
            return recurrenceDate
        return dueDate
 
    @occurrenceDue.setter
    def occurrenceDue(self, value):
        relativeDate = self._getRecurrenceRelative()
        if relativeDate is None:
            self._dueDate = value
            self._setDueDateTime( value )
            return
        diff = value - relativeDate
        self._setDueDateTime( diff )

    ## ========================================================================
    
    @abc.abstractmethod
    def _getRecurrence(self):
        raise NotImplementedError('You need to define this method in derived class!')

    @abc.abstractmethod
    def _setRecurrence(self, value):
        raise NotImplementedError('You need to define this method in derived class!')
    
    @property
    def recurrence(self) -> Recurrent:
        return self._getRecurrence()
 
    @recurrence.setter
    def recurrence(self, value):
        recurrence = self._getRecurrence()
        if recurrence is None and value is not None:
            self._setRecurrentOffset( 0 )
        self._setRecurrence( value )
 
    def getAppliedRecurrence(self) -> Recurrent:
        if self._recurrence is None:
            return None
        if self._recurrence.isAsParent() is False:
            return self._recurrence
        parent = self.getParent()
        if parent is None:
            return None
        return parent.getAppliedRecurrence()

    ## ========================================================================

    @abc.abstractmethod
    def _getRecurrentOffset(self):
        raise NotImplementedError('You need to define this method in derived class!')

    @abc.abstractmethod
    def _setRecurrentOffset(self, value):
        raise NotImplementedError('You need to define this method in derived class!')

    @property
    def recurrentOffset(self):
        return self._getRecurrentOffset()

    @recurrentOffset.setter
    def recurrentOffset(self, value):
        self._setRecurrentOffset( value )

    ## ========================================================================

    def currentOccurrence(self) -> TaskOccurrence:
        recOffset = self._getRecurrentOffset()
        return TaskOccurrence( self, recOffset )

    def subOccurences(self) -> List[TaskOccurrence]:
        subitems = self.getSubitems()
        if subitems is None:
            return list()
        ret = list()
        for currItem in subitems:
            currOccurrence = currItem.currentOccurrence()
            ret.append( currOccurrence )
        return ret
 
    def getTaskOccurrenceForDate(self, entryDate: date) -> TaskOccurrence:
        dateTimeRange: DateTimeRange = self.getDateTimeRange()
        dateRange = dateTimeRange.dateRange()
        dateRange.normalize()
        if dateRange.isNormalized() is False:
            return None
        if entryDate in dateRange:
            return TaskOccurrence( self )

        recurr = self.getAppliedRecurrence()
        if recurr is None:
            return None

        if recurr.endDate is not None and recurr.endDate < entryDate:
            return None
        recurrentOffset: relativedelta = recurr.getDateOffset()
        if recurrentOffset is None:
            return None

        multiplicator = recurrent.find_multiplication_after( dateRange.end, entryDate, recurrentOffset )
        if multiplicator < 1:
            return None
        dateRange += recurrentOffset * multiplicator
        if entryDate in dateRange:
            return TaskOccurrence( self, multiplicator )
        return None
 
    ## ========================================================================
 
    def getReferenceDateTime(self) -> datetime:
        if self.occurrenceStart is not None:
            return self.occurrenceStart
        ## deadline case
        return self.occurrenceDue
 
    def getFirstDateTime(self) -> datetime:
        if self.occurrenceDue is None:
            return None
        minDate = self.occurrenceDue
        if self.occurrenceStart is not None and self.occurrenceStart < minDate:
            minDate = self.occurrenceStart
        remindDate = self.getReminderFirstDate()
        if remindDate is not None and remindDate < minDate:
            minDate = remindDate
        return minDate
 
    def getDateTimeRange(self) -> DateTimeRange:
        startDate = self._getStartDateTime()
        endDate   = self._getDueDateTime()
        return DateTimeRange(startDate, endDate)
 
    def setDefaultDateTime(self, start: datetime ):
        self.startDateTime = start
        self.dueDateTime = self.startDateTime + timedelta( hours=1 )
 
    def setDefaultDate(self, startDate: date):
        start = datetime.combine( startDate, time(10, 0, 0) )
        self.setDefaultDateTime( start )
 
    def setDeadline(self):
        self.startDateTime = None
 
    def setDeadlineDateTime(self, due: datetime ):
        self.startDateTime = None
        self.dueDateTime = due
        
    ## ========================================================================

    @abc.abstractmethod
    def _getReminderList(self):
        raise NotImplementedError('You need to define this method in derived class!')

    @abc.abstractmethod
    def _setReminderList(self, value):
        raise NotImplementedError('You need to define this method in derived class!')

    @property
    def reminderList(self):
        return self._getReminderList()

    @reminderList.setter
    def reminderList(self, value):
        self._setReminderList( value )

    def addReminder( self, reminder=None ):
        reminderList = self._getReminderList()
        if reminderList is None:
            reminderList = list()
            self._setReminderList( reminderList )
        if reminder is None:
            reminder = Reminder()
        reminderList.append( reminder )
        return reminder
 
    def addReminderDays( self, days=1 ):
        reminder = Reminder()
        reminder.setDays( days )
        self.addReminder( reminder )
 
    def getReminderFirstDate(self) -> datetime:
        if self.occurrenceDue is None:
            return None
        reminderList = self._getReminderList()
        if reminderList is None:
            return None
        retOffset = self.getReminderGreatest()
        if retOffset is None:
            return None
        return self.occurrenceDue - retOffset
 
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
            if currOffset > retOffset:
                retOffset = currOffset
        return retOffset
    
    ## ========================================================================
 
    def getNotifications(self) -> List[Notification]:
        if self.occurrenceDue is None:
            return list()
        currTime = datetime.today()
        ret: List[Notification] = list()
        if self.occurrenceDue > currTime:
            notif = Notification()
            notif.notifyTime = self.occurrenceDue
            notif.task = self
            notif.message = "task '%s' reached deadline" % self.title
            ret.append( notif )
 
        reminderList = self._getReminderList()
        if reminderList is None:
            return ret
 
        for reminder in reminderList:
            notifTime = self.occurrenceDue - reminder.getOffset()
            if notifTime > currTime:
                notif = Notification()
                notif.notifyTime = notifTime
                notif.task = self
                notif.message = "task '%s': %s" % (self.title, reminder.printPretty())
                ret.append( notif )
 
        ret.sort( key=Notification.sortByTime )
        return ret

    @abc.abstractmethod
    def addSubTask(self):
        raise NotImplementedError('You need to define this method in derived class!')
 
    def printNextRecurrence(self) -> str:
        recurr = self.getAppliedRecurrence()
        if recurr is None:
            return "None"
        refDate = self.getReferenceDateTime()
        nextRepeat = recurr.nextDateTime( refDate )
        if nextRepeat is None:
            return "None"
        dateText = nextRepeat.strftime( "%Y-%m-%d %H:%M" )
        return dateText
 
#     def __str__(self):
#         reminderList = self._getReminderList()
#         return "[t:%s d:%s c:%s p:%s sd:%s dd:%s rem:%s rec:%s ro:%s]" % (
#             self.title, self.description, self._completed, self.priority,
#             self.occurrenceStart, self.occurrenceDue,
#             reminderList, self._recurrence,
#             self._recurrentOffset )
 
    def _progressRecurrence(self) -> bool:
        recurr = self.getAppliedRecurrence()
        if recurr is None:
            return False
        nextDueDate = self._getRecurrenceDate( self.dueDateTime, 1 )
        nextDate = nextDueDate.date()
        if recurr.isEnd( nextDate ):
            return False
        recOffset = self._getRecurrentOffset()
        recOffset += 1
        self._setRecurrentOffset( recOffset )
        return True
 
    def _getRecurrenceDate(self, aDate: datetime, offset: int = 0) -> datetime:
        if aDate is None:
            return None
        relativeDate = self._getRecurrenceRelative( offset )
        if relativeDate is None:
            return None
        recurrentDate = aDate + relativeDate
        return recurrentDate
 
    def _getRecurrenceRelative(self, offset: int = 0) -> relativedelta:
        recurr = self.getAppliedRecurrence()
        if recurr is None:
            return None
        recOffset = self._getRecurrentOffset()
        return recurr.getDateOffset() * (recOffset + offset)

    @staticmethod
    def sortByDates( task ):
        return ( task.occurrenceDue, task.occurrenceStart )


## ========================================================================
## ========================================================================


def calc_time_span(entryDate: date, start: datetime, end: datetime):
    startFactor = 0.0
    if start is not None:
        startDate = start.date()
        if entryDate < startDate:
            return None
        elif entryDate == startDate:
            midnight = datetime.combine( entryDate, datetime.min.time() )
            startDiff = start - midnight
            daySecs = timedelta( days=1 ).total_seconds()
            startFactor = startDiff.total_seconds() / timedelta( days=1 ).total_seconds()
    dueFactor = 1.0
    if end is not None:
        endDate = end.date()
        if entryDate > endDate:
            return None
        elif entryDate == endDate:
            midnight = datetime.combine( entryDate, datetime.min.time() )
            startDiff = end - midnight
            daySecs = timedelta( days=1 ).total_seconds()
            dueFactor = startDiff.total_seconds() / daySecs
    ret = [startFactor, dueFactor]
    return ret


def ensure_date_time( value ):
    if value is None:
        return value
    if isinstance( value, datetime):
        return value
    if isinstance( value, date):
        value = datetime.combine( value, datetime.min.time() )
    _LOGGER.warning( "unknown type: %s %s", value, type(value) )
    return None
