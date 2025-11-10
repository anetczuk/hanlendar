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

from hanlendar import persist
from hanlendar.domainmodel.task import Task, DateTimeRange
from hanlendar.domainmodel.item import generate_uid
from hanlendar.domainmodel.recurrent import Recurrent
from hanlendar.domainmodel.reminder import Reminder


_LOGGER = logging.getLogger(__name__)


class LocalTask(Task, persist.Versionable):
    """Task is entity that lasts over time."""

    ## 1: _recurrentStartDate and _recurrentDueDate replaced with _recurrentOffset
    ## 2: add base class Item
    ## 3: rename: 'title' to '_title', 'description' to '_description', 'priority' to '_priority'
    ## 4: rename: 'reminderList' to '_reminderList'
    ## 5: rescaled 'priority'
    ## 6: added 'UID'
    ## 7: added '_completedList'
    ## 8: remove '_recurrentOffset' and use '_startDate' and '_dueDate'
    ## 9: added '_createDate'
    _class_version = 9

    def __init__(self, title=""):
        super().__init__()
        self._UID = generate_uid()
        self._title = title
        self._description = ""
        self._completed = 0  ## task completion percentage, in range [0..100]
        self._priority = 5  ## lower number, greater priority

        self._parent = None
        self.subitems: list = None

        self._createDate: datetime.datetime = datetime.datetime.now(datetime.timezone.utc)
        ## current task start time (updated every time recurrent task is completed)
        self._startDate: datetime.datetime = None
        ## current task due time (updated every time recurrent task is completed)
        self._dueDate: datetime.datetime = None
        ## include completed 'self._startDate' and 'self._dueDate' (even for non recurrent tasks)
        self._completedList: list[DateTimeRange] = []

        self._reminderList: list[Reminder] = None
        self._recurrence: Recurrent = None

    # ruff: noqa: PLR0912
    def _convertstate_(self, dict_, dict_version_):
        _LOGGER.info("converting object from version %s to %s", dict_version_, self._class_version)

        if dict_version_ is None:
            dict_version_ = -1

        dict_version_ = max(dict_version_, 0)

        if dict_version_ == 0:
            ## replace _recurrentStartDate and _recurrentDueDate with _recurrentOffset
            recurrence = dict_["_recurrence"]
            if recurrence is not None:
                dueDate = dict_["_dueDate"].date()
                targetDueDate = dict_["_recurrentDueDate"].date()
                recurrentOffset = recurrence.findRecurrentOffset(dueDate, targetDueDate)
                dict_["_recurrentOffset"] = recurrentOffset
            else:
                ## set default value
                dict_["_recurrentOffset"] = 0
            dict_version_ = 1

        if dict_version_ == 1:
            ## add field
            dict_["subitems"] = None
            dict_version_ = 2

        if dict_version_ == 2:
            ## rename fields
            dict_["_title"] = dict_.pop("title", "")
            dict_["_description"] = dict_.pop("description", "")
            dict_["_priority"] = dict_.pop("priority", 10)
            dict_version_ = 3

        if dict_version_ == 3:
            ## rename fields
            dict_["_reminderList"] = dict_.pop("reminderList", None)
            dict_version_ = 4

        if dict_version_ == 4:
            ## rescale priority
            priority = dict_.pop("_priority", 10)
            dict_["_priority"] = int(priority / 2.0)
            dict_version_ = 5

        if dict_version_ == 5:
            dict_["_UID"] = generate_uid()
            dict_version_ = 6

        if dict_version_ == 6:
            completed_list = []
            completed = dict_["_completed"]
            recurrence = dict_["_recurrence"]
            if recurrence is None:
                if completed == 100:
                    ## already completed - add start, due date
                    dt_range = DateTimeRange(dict_["_startDate"], dict_["_dueDate"])
                    completed_list.append(dt_range)
            else:
                start_date = dict_["_startDate"]
                due_date = dict_["_dueDate"]
                recurrence_offset = dict_["_recurrentOffset"]
                completed_list = fill_completed_list(start_date, due_date, recurrence_offset, recurrence)
                if completed_list is None:
                    dict_["_fix_completedList_"] = (start_date, due_date, recurrence_offset)
                    completed_list = []
            dict_["_completedList"] = completed_list
            dict_version_ = 7

        if dict_version_ == 7:
            recurrence = dict_["_recurrence"]
            if recurrence is not None:
                start_date = dict_["_startDate"]
                due_date = dict_["_dueDate"]
                recurrence_offset = dict_["_recurrentOffset"]
                next_start_date, next_due_date = update_start_due_date(
                    start_date,
                    due_date,
                    recurrence_offset,
                    recurrence,
                )
                if next_due_date is not None:
                    dict_["_startDate"] = next_start_date
                    dict_["_dueDate"] = next_due_date
                else:
                    dict_["_fix_recurrentOffset_"] = (start_date, due_date, recurrence_offset)
            del dict_["_recurrentOffset"]
            dict_version_ = 8

        if dict_version_ == 8:
            create_date = dict_["_startDate"]
            if create_date is None:
                create_date = dict_["_dueDate"]
            dict_["_createDate"] = create_date
            dict_version_ = 9

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
    def getSubitems(self):
        return self.subitems

    ## overrided
    def setSubitems(self, newList):
        self.subitems = newList

    ## ========================================================================

    ## overriden
    def _getUID(self):
        return self._UID

    ## overriden
    def _setUID(self, value):
        self._UID = value

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
        if value == 100:
            if len(self._completedList) == 0:
                dt_range = DateTimeRange(self.startDateTime, self.dueDateTime)
                self._completedList.append(dt_range)
            else:
                dt_range = DateTimeRange(self.startDateTime, self.dueDateTime)
                self._completedList.append(dt_range)
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

    ## overriden
    def _getCreateDateTime(self) -> datetime.datetime:
        return self._createDate

    ## overriden
    def _getStartDateTime(self) -> datetime.datetime:
        return self._startDate

    ## overriden
    def _setStartDateTime(self, value: datetime.datetime):
        self._startDate = value

    ## overriden
    def _getDueDateTime(self) -> datetime.datetime:
        return self._dueDate

    ## overriden
    def _setDueDateTime(self, value: datetime.datetime):
        self._dueDate = value

    ## overriden
    def _getCompletedList(self) -> list[DateTimeRange]:
        if self._completedList is None:
            return []
        return self._completedList

    ## ========================================================================

    ## overriden
    def _getReminderList(self):
        return self._reminderList

    ## overriden
    def _setReminderList(self, values):
        self._reminderList = values

    ## =====================================================================

    ## overriden
    def _getRecurrence(self) -> Recurrent:
        return self._recurrence

    ## overriden
    def _setRecurrence(self, value: Recurrent):
        self._recurrence = value

    ## ========================================================================

    ## overriden
    def addSubTask(self):
        return self.addSubItem(LocalTask())

    def __str__(self):
        reminderList = self._getReminderList()
        return (
            f"[t:{self.title} d:{self.description} c:{self._completed} p:{self.priority}"
            f" sd:{self.startDateTime} dd:{self.dueDateTime} rem:{reminderList}"
            f" rec:{self._recurrence}]"
        )


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
