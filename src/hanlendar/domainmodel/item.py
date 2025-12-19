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
import uuid
from typing import Any
import datetime
from hanlendar.domainmodel.recurrent import Recurrent
from hanlendar.domainmodel.reminder import Reminder
from hanlendar import persist


_LOGGER = logging.getLogger(__name__)


DateDateTime = datetime.date | datetime.datetime


def ensure_date_time(value: DateDateTime) -> datetime.datetime:
    if value is None:
        return value
    if isinstance(value, datetime.datetime):
        return value
    if isinstance(value, datetime.date):
        return datetime.datetime(value.year, value.month, value.day)
    _LOGGER.warning("unknown type: %s %s", value, type(value))
    return None


def generate_uid() -> str:
    return str(uuid.uuid4())
    # return str(uuid.uuid4()) + "@hanlendar"


## ============================================================


class CommonData(persist.Versionable):
    """Container for common data for Task and ToDo."""

    ##  1: added '_reminderList'
    ##  2: added 'calendar_id'
    _class_version = 2

    def __init__(self):
        self.UID: str = generate_uid()

        ## None value means local "default" calendar
        self.calendar_id: str = None
        self.title: str = ""
        self.location: str = ""
        self.url: str = ""
        self.description: str = ""
        self.component_class: str = ""  ## PUBLIC, PRIVATE, CONFIDENTIAL

        ## item Task - TENTATIVE, CONFIRMED, CANCELLED
        ## item ToDo - NEEDS-ACTION, COMPLETED, IN-PROCESS, CANCELLED
        self.status: str = ""

        self.sequence: int = 0
        self.completed: int = 0  ## completion percentage, in range [0..100]

        ## Evolution priority meanings:
        ##  missing: Undefined
        ##  3: High
        ##  5: Normal
        ##  7: Low
        self.priority: int = 5  ## lower number, greater priority

        self.createDate: datetime.datetime = datetime.datetime.now(datetime.timezone.utc)
        self.lastModifiedDate: datetime.datetime = datetime.datetime.now(datetime.timezone.utc)

        ## current task start time (updated every time recurrent task is completed)
        self.startDate: DateDateTime = None

        self.recurrence: Recurrent = None

        self.reminderList: list[Reminder] = None

        ## unknown icalendar properties
        self.unknown_props: dict[str, Any] = None

    # ruff: noqa: PLR0912
    def _convertstate_(self, state_dict, state_version):  # pylint: disable=R0915
        _LOGGER.info("converting object from version %s to %s", state_version, self._class_version)

        if state_version is None:
            state_version = -1

        state_version = max(state_version, 0)

        if state_version == 0:
            state_dict["reminderList"] = None
            state_version += 1

        if state_version == 1:
            state_dict["calendar_id"] = None
            state_version += 1

        return state_dict

    def __eq__(self, other):
        if not isinstance(other, CommonData):
            return NotImplemented
        return self.__dict__ == other.__dict__

    def _key(self):
        return (
            self.UID,
            self.title,
            self.location,
            self.url,
            self.description,
            self.component_class,
            self.status,
            self.sequence,
            self.completed,
            self.priority,
            self.createDate,
            self.lastModifiedDate,
            self.startDate,
            self.recurrence,
            None if not self.reminderList else tuple(self.reminderList),
            self.unknown_props,
        )

    def __hash__(self):
        return hash(self._key())

    def __str__(self):
        return (
            f"[uid:{self.UID} t:{self.title} l:{self.location} u:{self.url} d:{self.description}"
            f" c:{self.component_class} s:{self.status} s:{self.sequence} c:{self.completed} p:{self.priority}"
            f" cd:{self.createDate} lm:{self.lastModifiedDate} sd:{self.startDate}"
            f" rec:{self.recurrence} rem:{self.reminderList} up:{self.unknown_props}]"
        )

    def addReminder(self, reminder=None):
        if self.reminderList is None:
            self.reminderList = []
        if reminder is None:
            reminder = Reminder()
        self.reminderList.append(reminder)
        return reminder


## ============================================================


class Item:
    """Base class for Task and ToDo."""

    @abc.abstractmethod
    def getParent(self):
        message = "You need to define this method in derived class!"
        raise NotImplementedError(message)

    @abc.abstractmethod
    def setParent(self, _parentItem=None):
        message = "You need to define this method in derived class!"
        raise NotImplementedError(message)

    ## return mutable reference
    @abc.abstractmethod
    def getSubitems(self):
        message = "You need to define this method in derived class!"
        raise NotImplementedError(message)

    @abc.abstractmethod
    def setSubitems(self, _newList):
        message = "You need to define this method in derived class!"
        raise NotImplementedError(message)

    ## ========================================================================

    @abc.abstractmethod
    def _get_common_data(self) -> CommonData:
        message = "You need to define this method in derived class!"
        raise NotImplementedError(message)

    @property
    def commonData(self) -> CommonData:
        return self._get_common_data()

    @abc.abstractmethod
    def _getUnknownProps(self) -> dict[Any, Any]:
        message = "You need to define this method in derived class!"
        raise NotImplementedError(message)

    @property
    def unknownProps(self) -> dict[Any, Any]:
        return self._getUnknownProps()

    @abc.abstractmethod
    def _getUID(self):
        message = "You need to define this method in derived class!"
        raise NotImplementedError(message)

    @abc.abstractmethod
    def _setUID(self, _value):
        message = "You need to define this method in derived class!"
        raise NotImplementedError(message)

    def getUID(self):
        return self._getUID()

    def setUID(self, value):
        self._setUID(value)

    @property
    def UID(self):
        return self.getUID()

    @UID.setter
    def UID(self, value):
        self.setUID(value)

    ## ========================================================================

    @abc.abstractmethod
    def _getTitle(self) -> str:
        message = "You need to define this method in derived class!"
        raise NotImplementedError(message)

    @abc.abstractmethod
    def _setTitle(self, _value: str):
        message = "You need to define this method in derived class!"
        raise NotImplementedError(message)

    def getTitle(self) -> str:
        return self._getTitle()

    def setTitle(self, value: str):
        self._setTitle(value)

    @property
    def title(self) -> str:
        return self.getTitle()

    @title.setter
    def title(self, value: str):
        self.setTitle(value)

    @property
    def summary(self) -> str:
        return self.getTitle()

    @summary.setter
    def summary(self, value: str):
        self.setTitle(value)

    ## ========================================================================

    @abc.abstractmethod
    def _getLocation(self) -> str:
        message = "You need to define this method in derived class!"
        raise NotImplementedError(message)

    @abc.abstractmethod
    def _setLocation(self, _value: str):
        message = "You need to define this method in derived class!"
        raise NotImplementedError(message)

    def getLocation(self) -> str:
        return self._getLocation()

    def setLocation(self, value: str):
        self._setLocation(value)

    @property
    def location(self) -> str:
        return self.getLocation()

    @location.setter
    def location(self, value: str):
        self.setLocation(value)

    ## ========================================================================

    @abc.abstractmethod
    def _getURL(self) -> str:
        message = "You need to define this method in derived class!"
        raise NotImplementedError(message)

    @abc.abstractmethod
    def _setURL(self, _value: str):
        message = "You need to define this method in derived class!"
        raise NotImplementedError(message)

    def getURL(self) -> str:
        return self._getURL()

    def setURL(self, value: str):
        self._setURL(value)

    @property
    def url(self) -> str:
        return self.getURL()

    @url.setter
    def url(self, value: str):
        self.setURL(value)

    ## ========================================================================

    @abc.abstractmethod
    def _getDescription(self) -> str:
        message = "You need to define this method in derived class!"
        raise NotImplementedError(message)

    @abc.abstractmethod
    def _setDescription(self, _value: str):
        message = "You need to define this method in derived class!"
        raise NotImplementedError(message)

    def getDescription(self) -> str:
        return self._getDescription()

    def setDescription(self, value: str):
        self._setDescription(value)

    @property
    def description(self) -> str:
        return self.getDescription()

    @description.setter
    def description(self, value: str):
        self.setDescription(value)

    ## ========================================================================

    @abc.abstractmethod
    def _getStatus(self) -> str:
        message = "You need to define this method in derived class!"
        raise NotImplementedError(message)

    @abc.abstractmethod
    def _setStatus(self, _value: str):
        message = "You need to define this method in derived class!"
        raise NotImplementedError(message)

    def getStatus(self) -> str:
        return self._getStatus()

    def setStatus(self, value: str):
        self._setStatus(value)

    @property
    def status(self) -> str:
        return self.getStatus()

    @status.setter
    def status(self, value: str):
        self.setStatus(value)

    ## ========================================================================

    @abc.abstractmethod
    def _getClass(self) -> str:
        message = "You need to define this method in derived class!"
        raise NotImplementedError(message)

    @abc.abstractmethod
    def _setClass(self, _value: str):
        message = "You need to define this method in derived class!"
        raise NotImplementedError(message)

    def getClass(self) -> str:
        return self._getClass()

    def setClass(self, value: str):
        self._setClass(value)

    @property
    def class_prop(self) -> str:
        return self.getClass()

    @class_prop.setter
    def class_prop(self, value: str):
        self.setClass(value)

    ## ========================================================================

    @abc.abstractmethod
    def _getSequence(self) -> int:
        message = "You need to define this method in derived class!"
        raise NotImplementedError(message)

    @abc.abstractmethod
    def _setSequence(self, _value: int):
        message = "You need to define this method in derived class!"
        raise NotImplementedError(message)

    def getSequence(self) -> int:
        return self._getSequence()

    def setSequence(self, value: int):
        self._setSequence(value)

    @property
    def sequence(self) -> int:
        return self.getSequence()

    @sequence.setter
    def sequence(self, value: int):
        self.setSequence(value)

    ## ========================================================================

    @abc.abstractmethod
    def _getCompleted(self):
        message = "You need to define this method in derived class!"
        raise NotImplementedError(message)

    @abc.abstractmethod
    def _setCompleted(self, _value=100):
        message = "You need to define this method in derived class!"
        raise NotImplementedError(message)

    def getCompleted(self):
        return self._getCompleted()

    def setCompleted(self, value=100):
        if value < 0:
            value = 0
        elif value > 100:
            value = 100
        self._setCompleted(value)

    @property
    def completed(self):
        return self.getCompleted()

    @completed.setter
    def completed(self, value):
        self.setCompleted(value)

    def isCompleted(self):
        if self.completed < 100:
            return False
        subitems = self.getSubitems()
        if not subitems:
            return True
        return all(sub.isCompleted() is not False for sub in subitems)

    ## ========================================================================

    @abc.abstractmethod
    def _getPriority(self):
        message = "You need to define this method in derived class!"
        raise NotImplementedError(message)

    @abc.abstractmethod
    def _setPriority(self, _value):
        message = "You need to define this method in derived class!"
        raise NotImplementedError(message)

    def getPriority(self):
        return self._getPriority()

    def setPriority(self, value):
        value = min(value, 9)
        self._setPriority(value)

    @property
    def priority(self):
        return self.getPriority()

    @priority.setter
    def priority(self, value):
        self.setPriority(value)

    ## ========================================================================
    ## ========================================================================

    def getRootItem(self):
        currItem = self
        visitedItems = set()
        while True:
            if currItem in visitedItems:
                _LOGGER.warning("cycle detected -- unable to find root item")
                return None
            visitedItems.add(currItem)
            currParent = currItem.getParent()
            if currParent is None:
                return currItem
            currItem = currParent

    def getAllSubItems(self):
        """Return all sub items from tree."""
        subitems = self.getSubitems()
        if subitems is None:
            return []
        return Item.getAllSubItemsFromList(subitems)

    def getChildCoords(self, item):
        subitems = self.getSubitems()
        return Item.getItemCoords(subitems, item)

    def getChildFromCoords(self, coords):
        subitems = self.getSubitems()
        return Item.getItemFromCoords(subitems, coords)

    def detachChildByCoords(self, coords):
        subitems = self.getSubitems()
        return Item.detachItemByCoords(subitems, coords)

    def addSubItem(self, item: "Item", index=-1):
        subitems = self.getSubitems()
        if subitems is None:
            subitems = []
            self.setSubitems(subitems)
        if index < 0:
            subitems.append(item)
            item.setParent(self)
        else:
            subitems.insert(index, item)
            item.setParent(self)
        return item

    def removeSubItem(self, item):
        subitems = self.getSubitems()
        if subitems is None:
            return None
        return Item.removeSubItemFromList(subitems, item)

    def replaceSubItem(self, oldItem, newItem):
        subitems = self.getSubitems()
        if subitems is None:
            return False
        return Item.replaceSubItemInList(subitems, oldItem, newItem)

    #     def __str__(self):
    #         return "[t:%s d:%s c:%s p:%s]" % ( self.title, self.description, self._completed, self.priority )

    ## ==============================================================

    @staticmethod
    def getAllSubItemsFromList(itemList):
        """Return all sub items from tree."""
        if itemList is None:
            return []
        retList = []
        for item in itemList:
            retList.append(item)
            retList += item.getAllSubItems()
        return retList

    @staticmethod
    def removeSubItemFromList(itemList, item):
        if itemList is None:
            return None
        items_num = len(itemList)
        for index in range(items_num):
            currItem = itemList[index]
            if currItem is item:
                popped = itemList.pop(index)
                popped.setParent(None)
                return popped
            removed = currItem.removeSubItem(item)
            if removed is not None:
                return removed
        return None

    @staticmethod
    def replaceSubItemInList(itemList, oldItem, newItem):
        if itemList is None:
            return None
        items_num = len(itemList)
        for index in range(items_num):
            currItem = itemList[index]
            if currItem is oldItem:
                newItem.setParent(oldItem.getParent())
                itemList[index] = newItem
                return True
            if currItem.replaceSubItem(oldItem, newItem) is True:
                return True
        return False

    @staticmethod
    def getItemCoords(itemsList, item):
        if itemsList is None:
            return None
        if not itemsList:
            return None
        lSize = len(itemsList)
        for i in range(lSize):
            currItem = itemsList[i]
            if currItem is item:
                return [i]
            ret = currItem.getChildCoords(item)
            if ret is not None:
                return [i, *ret]
        return None

    @staticmethod
    def getItemFromCoords(itemsList, coords):
        if itemsList is None:
            return None
        if not itemsList:
            return None
        if coords is None:
            return None
        if not coords:
            return None
        itemCoords = list(coords)
        elemIndex = itemCoords.pop(0)
        if elemIndex >= len(itemsList):
            return None
        item = itemsList[elemIndex]
        if not itemCoords:
            return item
        return item.getChildFromCoords(itemCoords)

    @staticmethod
    def detachItemByCoords(itemsList, coords):
        if itemsList is None:
            return None
        if not itemsList:
            return None
        if coords is None:
            return None
        if not coords:
            return None
        itemCoords = list(coords)
        elemIndex = itemCoords.pop(0)
        if elemIndex >= len(itemsList):
            return None
        item = itemsList[elemIndex]
        if not itemCoords:
            itemsList.pop(elemIndex)
            return item
        return item.detachChildByCoords(itemCoords)

    @staticmethod
    def sortByPriority(item):
        return item.priority
