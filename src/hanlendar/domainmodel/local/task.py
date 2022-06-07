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

from typing import List
from datetime import date, time, datetime, timedelta
from dateutil.relativedelta import relativedelta

from hanlendar import persist
from hanlendar.domainmodel import recurrent
from hanlendar.domainmodel.task import Task, ensure_date_time, TaskOccurrence,\
    DateTimeRange
from hanlendar.domainmodel.recurrent import Recurrent
from hanlendar.domainmodel.reminder import Reminder, Notification


_LOGGER = logging.getLogger(__name__)


class LocalTask( Task, persist.Versionable ):
    """Task is entity that lasts over time."""

    ## 1: _recurrentStartDate and _recurrentDueDate replaced with _recurrentOffset
    ## 2: add base class Item
    ## 3: rename: 'title' to '_title', 'description' to '_description', 'priority' to '_priority'
    _class_version = 3

    def __init__(self, title="" ):
        super(LocalTask, self).__init__()
        self._title                         = title
        self._description                   = ""
        self._completed                     = 0        ## in range [0..100]
        self._priority                      = 10       ## lower number, greater priority

        self._parent                        = None
        self.subitems: list                 = None
        self._startDate: datetime           = None
        self._dueDate: datetime             = None
        self.reminderList: List[Reminder]   = None
        self._recurrence: Recurrent         = None
        self._recurrentOffset               = 0

    def _convertstate_(self, dict_, dictVersion_ ):
        _LOGGER.info( "converting object from version %s to %s", dictVersion_, self._class_version )

        if dictVersion_ is None:
            dictVersion_ = -1

        if dictVersion_ < 0:
            ## do nothing
            dictVersion_ = 0

        if dictVersion_ == 0:
            ## replace _recurrentStartDate and _recurrentDueDate with _recurrentOffset
            recurrence = dict_["_recurrence"]
            if recurrence is not None:
                dueDate = dict_["_dueDate"].date()
                targetDueDate = dict_["_recurrentDueDate"].date()
                recurrentOffset = recurrence.findRecurrentOffset( dueDate, targetDueDate )
                dict_["_recurrentOffset"] = recurrentOffset
            else:
                ## set default value
                dict_["_recurrentOffset"] = 0
            dictVersion_ = 1

        if dictVersion_ == 1:
            ## add field
            dict_["subitems"] = None
            dictVersion_ = 2

        if dictVersion_ == 2:
            ## rename fields
            dict_["_title"]       = dict_.pop( "title", "" )
            dict_["_description"] = dict_.pop( "description", "" )
            dict_["_priority"]    = dict_.pop( "priority", 10 )
            dictVersion_ = 3

        # pylint: disable=W0201
        self.__dict__ = dict_

    ## overrided
    def getParent(self):
        return self._parent

    ## overrided
    def setParent(self, parentItem=None):
        self._parent = parentItem

    ## return mutable reference
    ## overrided
    def getSubitems( self ):
        return self.subitems

    ## overrided
    def setSubitems( self, newList ):
        self.subitems = newList
        
    ## ========================================================================
        
    ## overriden
    def _getTitle(self):
        return self._title

    ## overriden
    def _setTitle(self, value):
        self._title = value
        
    ## overriden
    def _getDescription(self):
        return self._description

    ## overriden
    def _setDescription(self, value):
        self._description = value

    ## overrided
    def _getCompleted(self):
        return self._completed

    ## overrided
    def _setCompleted(self, value=100):
        if value < 0:
            value = 0
        elif value > 100:
            value = 100
        if value == 100 and self._progressRecurrence() is True:
            # completed -- next occurrence
            self._completed = 0
        else:
            self._completed = value

    ## overrided
    def _getPriority(self):
        return self._priority

    ## overrided
    def _setPriority(self, value):
        self._priority = value
    
    ## ========================================================================

    @property
    def startDateTime(self):
        return self._startDate

    @startDateTime.setter
    def startDateTime(self, value):
        value = ensure_date_time( value )
        self._startDate = value
        self._recurrentOffset = 0

    @property
    def occurrenceStart(self):
        recurrenceDate = self._getRecurrenceDate( self._startDate )
        if recurrenceDate is not None:
            return recurrenceDate
        return self._startDate

    @occurrenceStart.setter
    def occurrenceStart(self, value):
        relativeDate = self._getRecurrenceRelative()
        if relativeDate is None:
            self._startDate = value
            return
        self._startDate = value - relativeDate

    @property
    def dueDateTime(self):
        return self._dueDate

    @dueDateTime.setter
    def dueDateTime(self, value):
        value = ensure_date_time( value )
        self._dueDate = value
        self._recurrentOffset = 0

    @property
    def occurrenceDue(self):
        recurrenceDate = self._getRecurrenceDate( self._dueDate )
        if recurrenceDate is not None:
            return recurrenceDate
        return self._dueDate

    @occurrenceDue.setter
    def occurrenceDue(self, value):
        relativeDate = self._getRecurrenceRelative()
        if relativeDate is None:
            self._dueDate = value
            return
        self._dueDate = value - relativeDate

    def currentOccurrence(self) -> TaskOccurrence:
        return TaskOccurrence( self, self._recurrentOffset )

    def subOccurences(self) -> List[TaskOccurrence]:
        subitems = self.getSubitems()
        if subitems is None:
            return list()
        ret = list()
        for currItem in subitems:
            currOccurrence = currItem.currentOccurrence()
            ret.append( currOccurrence )
        return ret

    ## =====================================================================

    @property
    def recurrence(self) -> Recurrent:
        return self._recurrence

    @recurrence.setter
    def recurrence(self, value):
        if self._recurrence is None and value is not None:
            self._recurrentOffset = 0
        self._recurrence = value

    def getAppliedRecurrence(self) -> Recurrent:
        if self._recurrence is None:
            return None
        if self._recurrence.isAsParent() is False:
            return self._recurrence
        parent = self.getParent()
        if parent is None:
            return None
        return parent.getAppliedRecurrence()

    @property
    def recurrentOffset(self):
        return self._recurrentOffset

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
        startDate = None
        endDate   = None
        if self._startDate is not None:
            startDate = self._startDate
        if self._dueDate is not None:
            endDate = self._dueDate
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

    def getTaskOccurrenceForDate(self, entryDate: date):
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

    def addReminder( self, reminder=None ):
        if self.reminderList is None:
            self.reminderList = list()
        if reminder is None:
            reminder = Reminder()
        self.reminderList.append( reminder )
        return reminder

    def addReminderDays( self, days=1 ):
        reminder = Reminder()
        reminder.setDays( days )
        self.addReminder( reminder )

    def getReminderFirstDate(self) -> datetime:
        if self.occurrenceDue is None:
            return None
        if self.reminderList is None:
            return None
        retOffset = self.getReminderGreatest()
        if retOffset is None:
            return None
        return self.occurrenceDue - retOffset

    def getReminderGreatest(self) -> timedelta:
        if self.reminderList is None:
            return None
        retOffset = None
        for reminder in self.reminderList:
            if retOffset is None:
                retOffset = reminder.getOffset()
                continue
            currOffset = reminder.getOffset()
            if currOffset > retOffset:
                retOffset = currOffset
        return retOffset

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

        if self.reminderList is None:
            return ret

        for reminder in self.reminderList:
            notifTime = self.occurrenceDue - reminder.getOffset()
            if notifTime > currTime:
                notif = Notification()
                notif.notifyTime = notifTime
                notif.task = self
                notif.message = "task '%s': %s" % (self.title, reminder.printPretty())
                ret.append( notif )

        ret.sort( key=Notification.sortByTime )
        return ret

    def addSubTask(self):
        return self.addSubItem( LocalTask() )

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

    def __str__(self):
        return "[t:%s d:%s c:%s p:%s sd:%s dd:%s rem:%s rec:%s ro:%s]" % (
            self.title, self.description, self._completed, self.priority,
            self.occurrenceStart, self.occurrenceDue,
            self.reminderList, self._recurrence,
            self._recurrentOffset )

    def _progressRecurrence(self) -> bool:
        recurr = self.getAppliedRecurrence()
        if recurr is None:
            return False
        nextDueDate = self._getRecurrenceDate( self._dueDate, 1 )
        nextDate = nextDueDate.date()
        if recurr.isEnd( nextDate ):
            return False
        self._recurrentOffset += 1
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
        return recurr.getDateOffset() * (self._recurrentOffset + offset)

    @staticmethod
    def sortByDates( task ):
        return ( task.occurrenceDue, task.occurrenceStart )

