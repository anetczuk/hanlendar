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
import datetime
from typing import Any
import abc
from dateutil.relativedelta import relativedelta

from hanlendar import persist
from hanlendar.domainmodel.item import generate_uid, Item, CommonData, DateDateTime, ensure_date_time
from hanlendar.domainmodel.recurrent import Recurrent, find_multiplication_after
from hanlendar.domainmodel.reminder import Reminder, Notification
from hanlendar.domainmodel.taskoccurrence import DateTimeRange, TaskOccurrence, DateRange


_LOGGER = logging.getLogger(__name__)


class Task(Item):
    """Task is entity that lasts over time."""

    @abc.abstractmethod
    def _getCreateDateTime(self) -> datetime.datetime:
        message = "You need to define this method in derived class!"
        raise NotImplementedError(message)

    @property
    def createDateTime(self) -> datetime.datetime:
        return self._getCreateDateTime()

    @abc.abstractmethod
    def _getLastModifiedDateTime(self) -> datetime.datetime:
        message = "You need to define this method in derived class!"
        raise NotImplementedError(message)

    @property
    def lastModifiedDateTime(self) -> datetime.datetime:
        return self._getLastModifiedDateTime()

    @abc.abstractmethod
    def _getStartDateTime(self) -> DateDateTime:
        message = "You need to define this method in derived class!"
        raise NotImplementedError(message)

    @abc.abstractmethod
    def _setStartDateTime(self, _value: DateDateTime):
        message = "You need to define this method in derived class!"
        raise NotImplementedError(message)

    @property
    def startDDT(self) -> DateDateTime:
        return self._getStartDateTime()

    @property
    def startDate(self) -> datetime.date:
        value = self._getStartDateTime()
        if isinstance(value, datetime.datetime):
            return value.date()
        return value

    @property
    def startDateTime(self) -> datetime.datetime:
        value = self._getStartDateTime()
        return ensure_date_time(value)

    @abc.abstractmethod
    def _getDueDateTime(self) -> DateDateTime:
        message = "You need to define this method in derived class!"
        raise NotImplementedError(message)

    @abc.abstractmethod
    def _setDueDateTime(self, _value: DateDateTime):
        message = "You need to define this method in derived class!"
        raise NotImplementedError(message)

    @property
    def dueDDT(self) -> DateDateTime:
        return self._getDueDateTime()

    @property
    def dueDate(self) -> datetime.date:
        value = self._getDueDateTime()
        if isinstance(value, datetime.datetime):
            return value.date()
        return value

    @property
    def dueDateTime(self) -> datetime.datetime:
        value = self._getDueDateTime()
        return ensure_date_time(value)

    @property
    def endDDT(self) -> DateDateTime:
        return self.dueDate

    @property
    def endDate(self) -> datetime.date:
        return self.dueDate

    @property
    def endDateTime(self) -> datetime.datetime:
        return self.dueDateTime

    def setOccurrence(self, start: DateDateTime, due: DateDateTime):
        self._setStartDateTime(start)
        self._setDueDateTime(due)

    def setOccurrenceDue(self, due: DateDateTime):
        self._setStartDateTime(None)
        self._setDueDateTime(due)

    def setDefaultDateTime(self, start: datetime.datetime):
        due = start + datetime.timedelta(hours=1)
        self.setOccurrence(start, due)

    def setDefaultDate(self, startDate: datetime.date):
        start = datetime.datetime.combine(startDate, datetime.time(10, 0, 0))
        self.setDefaultDateTime(start)

    def setDeadline(self):
        self._setStartDateTime(None)

    def setDeadlineDateTime(self, due: DateDateTime):
        self.setOccurrenceDue(due)

    def isAllDay(self) -> bool:
        if self.startDateTime is None:
            return False
        if self.endDateTime is None:
            return False
        if isinstance(self.startDateTime, datetime.datetime):
            start_time = self.startDateTime.time()
            if start_time.hour != 0 or start_time.minute != 0 or start_time.second != 0:
                return False
        if isinstance(self.endDateTime, datetime.datetime):
            end_time = self.endDateTime.time()
            return not (end_time.hour != 0 or end_time.minute != 0 or end_time.second != 0)
        return True

    def getReferenceDateTime(self) -> DateDateTime:
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
    def getTaskOccurrenceForDate(self, entryDate: datetime.date) -> TaskOccurrence:
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

        multiplicator = find_multiplication_after(dateRange.end, entryDate, recurrentDateOffset)
        if multiplicator < 1:
            return None
        dateRange += recurrentDateOffset * multiplicator
        if entryDate in dateRange:
            datetime_range = self.getOccurrenceDateTimeRange(multiplicator)
            return TaskOccurrence(self, datetime_range=datetime_range)

        return None

    ## ========================================================================

    ## return smallest date from: occurrenceStart, occurrenceDue and reminder date
    def getFirstDateTime(self) -> datetime.datetime:
        if self.dueDateTime is None:
            return None
        minDate = self.dueDateTime
        if self.startDateTime is not None and self.startDateTime < minDate:
            minDate = self.startDateTime
        remindDate = self.getReminderFirstDate()
        if remindDate is not None and remindDate < minDate:
            minDate = remindDate
        return minDate

        # datetime.datetime(value.year, value.month, value.day)

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

    def getReminderFirstDate(self) -> datetime.datetime:
        if self.dueDateTime is None:
            return None
        reminderList = self._getReminderList()
        if reminderList is None:
            return None
        retOffset = self.getReminderGreatest()
        if retOffset is None:
            return None
        return self.dueDateTime - retOffset

    def getReminderGreatest(self) -> datetime.timedelta:
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
        currTime = datetime.datetime.today()
        ret: list[Notification] = []
        if self.dueDateTime > currTime:
            notif = Notification()
            notif.setNotifyTime(self.dueDateTime)
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
        if isinstance(nextDueDate, datetime.datetime):
            nextDate = nextDueDate.date()
        else:
            nextDate = nextDueDate
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


class LocalTask(Task, persist.Versionable):
    """Task is entity that lasts over time."""

    ##  1: _recurrentStartDate and _recurrentDueDate replaced with _recurrentOffset
    ##  2: add base class Item
    ##  3: rename: 'title' to '_title', 'description' to '_description', 'priority' to '_priority'
    ##  4: rename: 'reminderList' to '_reminderList'
    ##  5: rescaled 'priority'
    ##  6: added 'UID'
    ##  7: added '_completedList'
    ##  8: remove '_recurrentOffset' and use '_startDate' and '_dueDate'
    ##  9: added '_createDate'
    ## 10: added '_location', '_url', '_sequence', '_lastModifiedDate', '_unknown_props'
    ## 11: added '_status', '_class'
    ## 12: use '_common_data'
    ## 13: move '_reminderList' to CommonData
    _class_version = 13

    def __init__(self, title: str = ""):
        super().__init__()

        self._parent = None
        self.subitems: list = None

        self._common_data: CommonData = CommonData()
        self._common_data.title = title

        ## current task due time (updated every time recurrent task is completed)
        self._dueDate: DateDateTime = None
        ## include completed 'self._startDate' and 'self._dueDate' (even for non recurrent tasks)
        self._completedList: list[DateTimeRange] = []

    # ruff: noqa: PLR0912
    def _convertstate_(self, state_dict, state_version):  # pylint: disable=R0915,R0912
        _LOGGER.info("converting object from version %s to %s", state_version, self._class_version)

        if state_version is None:
            state_version = -1

        state_version = max(state_version, 0)

        if state_version == 0:
            ## replace _recurrentStartDate and _recurrentDueDate with _recurrentOffset
            recurrence = state_dict["_recurrence"]
            if recurrence is not None:
                dueDate = state_dict["_dueDate"].date()
                targetDueDate = state_dict["_recurrentDueDate"].date()
                recurrentOffset = recurrence.findRecurrentOffset(dueDate, targetDueDate)
                state_dict["_recurrentOffset"] = recurrentOffset
            else:
                ## set default value
                state_dict["_recurrentOffset"] = 0
            state_version += 1

        if state_version == 1:
            ## add field
            state_dict["subitems"] = None
            state_version += 1

        if state_version == 2:
            ## rename fields
            state_dict["_title"] = state_dict.pop("title", "")
            state_dict["_description"] = state_dict.pop("description", "")
            state_dict["_priority"] = state_dict.pop("priority", 10)
            state_version += 1

        if state_version == 3:
            ## rename fields
            state_dict["_reminderList"] = state_dict.pop("reminderList", None)
            state_version += 1

        if state_version == 4:
            ## rescale priority
            priority = state_dict.pop("_priority", 10)
            state_dict["_priority"] = int(priority / 2.0)
            state_version += 1

        if state_version == 5:
            state_dict["_UID"] = generate_uid()
            state_version += 1

        if state_version == 6:
            completed_list = []
            completed = state_dict["_completed"]
            recurrence = state_dict["_recurrence"]
            if recurrence is None:
                if completed == 100:
                    ## already completed - add start, due date
                    dt_range = DateTimeRange(state_dict["_startDate"], state_dict["_dueDate"])
                    completed_list.append(dt_range)
            else:
                start_date = state_dict["_startDate"]
                due_date = state_dict["_dueDate"]
                recurrence_offset = state_dict["_recurrentOffset"]
                completed_list = fill_completed_list(start_date, due_date, recurrence_offset, recurrence)
                if completed_list is None:
                    state_dict["_fix_completedList_"] = (start_date, due_date, recurrence_offset)
                    completed_list = []
            state_dict["_completedList"] = completed_list
            state_version += 1

        if state_version == 7:
            recurrence = state_dict["_recurrence"]
            if recurrence is not None:
                start_date = state_dict["_startDate"]
                due_date = state_dict["_dueDate"]
                recurrence_offset = state_dict["_recurrentOffset"]
                next_start_date, next_due_date = update_start_due_date(
                    start_date,
                    due_date,
                    recurrence_offset,
                    recurrence,
                )
                if next_due_date is not None:
                    state_dict["_startDate"] = next_start_date
                    state_dict["_dueDate"] = next_due_date
                else:
                    state_dict["_fix_recurrentOffset_"] = (start_date, due_date, recurrence_offset)
            del state_dict["_recurrentOffset"]
            state_version += 1

        if state_version == 8:
            create_date = state_dict["_startDate"]
            if create_date is None:
                create_date = state_dict["_dueDate"]
            state_dict["_createDate"] = create_date
            state_version += 1

        if state_version == 9:
            state_dict["_location"] = ""
            state_dict["_url"] = ""
            state_dict["_sequence"] = 0
            state_dict["_lastModifiedDate"] = state_dict["_createDate"]
            state_dict["_unknown_props"] = None
            state_version += 1

        if state_version == 10:
            state_dict["_class"] = ""
            state_dict["_status"] = ""
            state_version += 1

        if state_version == 11:
            fields_mapping = {
                "UID": "_UID",
                "title": "_title",
                "location": "_location",
                "url": "_url",
                "description": "_description",
                "component_class": "_class",
                "status": "_status",
                "sequence": "_sequence",
                "completed": "_completed",
                "priority": "_priority",
                "createDate": "_createDate",
                "lastModifiedDate": "_lastModifiedDate",
                "startDate": "_startDate",
                "recurrence": "_recurrence",
                "unknown_props": "_unknown_props",
            }
            common_data: CommonData = CommonData()
            for key, value in fields_mapping.items():
                common_data.__dict__[key] = state_dict[value]
                del state_dict[value]
            state_dict["_common_data"] = common_data
            state_version += 1

        if state_version == 12:
            common_data = state_dict["_common_data"]
            common_data.reminderList = state_dict["_reminderList"]
            state_version += 1

        return state_dict

    def __eq__(self, other):
        if not isinstance(other, LocalTask):
            return NotImplemented
        return self._key() == other._key()
        ## it triggers infinite recursion
        # return self.__dict__ == other.__dict__

    def _key(self):
        ## no parent, no subitems
        return (self._common_data, self._dueDate, None if not self._completedList else tuple(self._completedList))

    def __hash__(self):
        return hash(self._key())

    def __str__(self):
        return f"[common:{self._common_data} due:{self._dueDate} completed:{self._completedList}]"

    ## overrided
    def getParent(self):
        return self._parent

    ## overrided
    def setParent(self, parentItem=None):
        self._parent = parentItem

    ## return mutable reference
    ## overrided
    def getSubitems(self):
        return self.subitems

    ## overrided
    def setSubitems(self, newList):
        self.subitems = newList

    ## overriden
    def addSubTask(self):
        return self.addSubItem(LocalTask())

    ## ========================================================================

    ## overriden
    def _get_common_data(self) -> CommonData:
        return self._common_data

    ## overriden
    def _getUnknownProps(self) -> dict[Any, Any]:
        return self._common_data.unknown_props

    ## overriden
    def _getUID(self):
        return self._common_data.UID

    ## overriden
    def _setUID(self, value):
        self._common_data.UID = value

    ## overriden
    def _getTitle(self) -> str:
        return self._common_data.title

    ## overriden
    def _setTitle(self, value: str):
        self._common_data.title = value

    ## overriden
    def _getLocation(self) -> str:
        return self._common_data.location

    ## overriden
    def _setLocation(self, value: str):
        self._common_data.location = value

    ## overriden
    def _getURL(self) -> str:
        return self._common_data.url

    ## overriden
    def _setURL(self, value: str):
        self._common_data.url = value

    ## overriden
    def _getDescription(self) -> str:
        return self._common_data.description

    ## overriden
    def _setDescription(self, value: str):
        self._common_data.description = value

    ## overriden
    def _getStatus(self) -> str:
        return self._common_data.status

    ## overriden
    def _setStatus(self, value: str):
        self._common_data.status = value

    ## overriden
    def _getClass(self) -> str:
        return self._common_data.component_class

    ## overriden
    def _setClass(self, value: str):
        self._common_data.component_class = value

    ## overriden
    def _getSequence(self) -> int:
        return self._common_data.sequence

    ## overriden
    def _setSequence(self, value: int):
        self._common_data.sequence = value

    ## overrided
    def _getCompleted(self):
        return self._common_data.completed

    ## overrided
    def _setCompleted(self, value=100):
        if value < 0:
            value = 0
        elif value > 100:
            value = 100
        if value >= 100:
            if len(self._completedList) == 0:
                dt_range = DateTimeRange(self.startDateTime, self.dueDateTime)
                self._completedList.append(dt_range)
            else:
                dt_range = DateTimeRange(self.startDateTime, self.dueDateTime)
                self._completedList.append(dt_range)
        if value >= 100 and self._progressRecurrence() is True:
            # completed -- next occurrence
            self._common_data.completed = 0
        else:
            self._common_data.completed = value

    ## overrided
    def _getPriority(self):
        return self._common_data.priority

    ## overrided
    def _setPriority(self, value):
        self._common_data.priority = value

    ## ========================================================================

    ## overriden
    def _getCreateDateTime(self) -> datetime.datetime:
        return self._common_data.createDate

    ## overriden
    def _getLastModifiedDateTime(self) -> datetime.datetime:
        return self._common_data.lastModifiedDate

    ## overriden
    def _getStartDateTime(self) -> DateDateTime:
        return self._common_data.startDate

    ## overriden
    def _setStartDateTime(self, value: DateDateTime):
        self._common_data.startDate = value

    ## overriden
    def _getDueDateTime(self) -> DateDateTime:
        return self._dueDate

    ## overriden
    def _setDueDateTime(self, value: DateDateTime):
        self._dueDate = value

    ## overriden
    def _getCompletedList(self) -> list[DateTimeRange]:
        if self._completedList is None:
            return []
        return self._completedList

    ## ========================================================================

    ## overriden
    def _getReminderList(self):
        return self._common_data.reminderList

    ## overriden
    def _setReminderList(self, values):
        self._common_data.reminderList = values

    ## =====================================================================

    ## overriden
    def _getRecurrence(self) -> Recurrent:
        return self._common_data.recurrence

    ## overriden
    def _setRecurrence(self, value: Recurrent):
        self._common_data.recurrence = value


## ========================================================================


def fill_completed_list(start_date, due_date, recurrence_offset, recurrence):
    completed_list = []
    if recurrence_offset > 0:
        ## already completed - add start, due date
        dt_range = DateTimeRange(start_date, due_date)
        completed_list.append(dt_range)
    for offset in range(1, recurrence_offset):
        completed_start = recurrence.nextDateTime(start_date, offset)
        completed_due = recurrence.nextDateTime(due_date, offset)
        if completed_due is not None:
            dt_range = DateTimeRange(completed_start, completed_due)
            completed_list.append(dt_range)
        else:
            return None
    return completed_list


def update_start_due_date(start_date, due_date, recurrence_offset, recurrence):
    next_start_date = recurrence.nextDateTime(start_date, recurrence_offset)
    next_due_date = recurrence.nextDateTime(due_date, recurrence_offset)
    return (next_start_date, next_due_date)
