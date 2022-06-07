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

from hanlendar import persist
from hanlendar.domainmodel.task import Task


_LOGGER = logging.getLogger(__name__)


class LocalTask( Task, persist.Versionable ):
    """Task is entity that lasts over time."""

    ## 1: _recurrentStartDate and _recurrentDueDate replaced with _recurrentOffset
    ## 2: add base class Item
    ## 3: rename: 'title' to '_title', 'description' to '_description', 'priority' to '_priority'
    ## 4: rename: 'reminderList' to '_reminderList'
    _class_version = 4

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
        self._reminderList: List[Reminder]  = None
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

        if dictVersion_ == 3:
            ## rename fields
            dict_["_reminderList"] = dict_.pop( "reminderList", None )
            dictVersion_ = 4

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

    ## overriden
    def _getStartDateTime(self):
        return self._startDate

    ## overriden
    def _setStartDateTime(self, value):
        self._startDate = value

    ## overriden
    def _getDueDateTime(self):
        return self._dueDate

    ## overriden
    def _setDueDateTime(self, value):
        self._dueDate = value

    ## ========================================================================

    ## overriden
    def _getReminderList(self):
        return self._reminderList

    ## overriden
    def _setReminderList(self, value):
        self._reminderList = value

    ## =====================================================================

    ## overriden
    def _getRecurrence(self):
        return self._recurrence

    ## overriden
    def _setRecurrence(self, value):
        self._recurrence = value

    ## overriden
    def _getRecurrentOffset(self):
        return self._recurrentOffset

    ## overriden
    def _setRecurrentOffset(self, value):
        self._recurrentOffset = value

    ## ========================================================================

    ## overriden
    def addSubTask(self):
        return self.addSubItem( LocalTask() )

    def __str__(self):
        reminderList = self._getReminderList()
        return "[t:%s d:%s c:%s p:%s sd:%s dd:%s rem:%s rec:%s ro:%s]" % (
            self.title, self.description, self._completed, self.priority,
            self.occurrenceStart, self.occurrenceDue,
            reminderList, self._recurrence,
            self._recurrentOffset )

