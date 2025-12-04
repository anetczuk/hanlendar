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

from hanlendar import persist

from hanlendar.domainmodel.item import Item, generate_uid, CommonData, DateDateTime, ensure_date_time
from hanlendar.domainmodel.recurrent import Recurrent


_LOGGER = logging.getLogger(__name__)


class LocalToDo(Item, persist.Versionable):
    """ToDo is entity without placement in time."""

    ##  0: add subtodos
    ##  1: add base class Item
    ##  2: rename: 'title' to '_title', 'description' to '_description', 'priority' to '_priority'
    ##  3: rescaled 'priority'
    ##  4: added 'UID'
    ##  5: added '_createDate'
    ##  6: added '_location', '_url', '_sequence', '_lastModifiedDate
    ##  7: added '_unknown_props'
    ##  8: added '_status', '_class'
    ##  9: use '_common_data'
    ## 10: added '_dueDate', '_completedDate'
    _class_version = 10

    def __init__(self, title: str = ""):
        super().__init__()

        self._parent = None
        self.subitems: list = None

        self._common_data: CommonData = CommonData()
        self._common_data.title = title

        self._dueDate: DateDateTime = None
        self._completedDate: DateDateTime = None

    def _convertstate_(self, state_dict, state_version):
        _LOGGER.info("converting object from version %s to %s", state_version, self._class_version)

        if state_version is None:
            state_version = -1

        ## set of conditions converting state_dict to recent version
        if state_version < 0:
            ## initialize subtodos field
            state_dict["subtodos"] = None
            state_version = 0

        if state_version == 0:
            ## base class extracted, "subtodos" renamed to "subitems"
            state_dict["subitems"] = state_dict["subtodos"]
            state_dict.pop("subtodos", None)
            state_version += 1

        if state_version == 1:
            ## rename fields
            state_dict["_title"] = state_dict.pop("title", "")
            state_dict["_description"] = state_dict.pop("description", "")
            state_dict["_priority"] = state_dict.pop("priority", 10)
            state_version += 1

        if state_version == 2:
            ## rescale priority
            priority = state_dict.pop("_priority", 10)
            state_dict["_priority"] = int(priority / 2.0)
            state_version += 1

        if state_version == 3:
            state_dict["_UID"] = generate_uid()
            state_version += 1

        if state_version == 4:
            state_dict["_createDate"] = datetime.datetime.now(datetime.timezone.utc)
            state_version += 1

        if state_version == 5:
            state_dict["_location"] = ""
            state_dict["_url"] = ""
            state_dict["_sequence"] = 0
            state_version += 1

        if state_version == 6:
            state_dict["_unknown_props"] = None
            state_version += 1

        if state_version == 7:
            state_dict["_class"] = ""
            state_dict["_status"] = ""
            state_version += 1

        if state_version == 8:
            if "_lastModifiedDate" not in state_dict:
                state_dict["_lastModifiedDate"] = state_dict["_createDate"]
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
                "unknown_props": "_unknown_props",
            }
            common_data: CommonData = CommonData()
            for key, value in fields_mapping.items():
                common_data.__dict__[key] = state_dict[value]
                del state_dict[value]
            state_dict["_common_data"] = common_data
            state_version += 1

        return state_dict

    def __eq__(self, other):
        if not isinstance(other, LocalToDo):
            return NotImplemented
        return self.__dict__ == other.__dict__

    def _key(self):
        ## no parent, no subitems
        return (self._common_data, self._dueDate, self._completedDate)

    def __hash__(self):
        return hash(self._key())

    def __str__(self):
        subLen = 0
        subitems = self.getSubitems()
        if subitems is not None:
            subLen = len(subitems)
        return f"[t:{self.title} d:{self.description} c:{self._common_data.completed} p:{self.priority} subs:{subLen}]"

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

    def addSubtodo(self, todo=None, index=-1):
        if todo is None:
            todo = LocalToDo()
        return self.addSubItem(todo, index)

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
        if self._common_data.completed == value:
            return
        self._common_data.completed = value
        if value >= 100:
            utc_dt = datetime.datetime.now(datetime.timezone.utc)
            self._completedDate = utc_dt.astimezone()
        else:
            self._completedDate = None

    ## overrided
    def _getPriority(self):
        return self._common_data.priority

    ## overrided
    def _setPriority(self, value):
        self._common_data.priority = value

    ## ========================================================================

    @property
    def createDateTime(self) -> datetime.datetime:
        return self._common_data.createDate

    @property
    def lastModifiedDateTime(self) -> datetime.datetime:
        return self._common_data.lastModifiedDate

    @property
    def startDDT(self) -> DateDateTime:
        return self._common_data.startDate

    @property
    def startDate(self) -> datetime.date:
        value = self._common_data.startDate
        if isinstance(value, datetime.datetime):
            return value.date()
        return value

    @property
    def startDateTime(self) -> datetime.datetime:
        value = self._common_data.startDate
        return ensure_date_time(value)

    def setStartDateTime(self, value: DateDateTime):
        self._common_data.startDate = value

    @property
    def dueDDT(self) -> DateDateTime:
        return self._dueDate

    @property
    def dueDate(self) -> datetime.date:
        value = self._dueDate
        if isinstance(value, datetime.datetime):
            return value.date()
        return value

    @property
    def dueDateTime(self) -> datetime.datetime:
        value = self._dueDate
        return ensure_date_time(value)

    def setDueDateTime(self, value: DateDateTime):
        self._dueDate = value

    @property
    def completedDDT(self) -> DateDateTime:
        return self._completedDate

    @property
    def completedDate(self) -> datetime.date:
        value = self._completedDate
        if isinstance(value, datetime.datetime):
            return value.date()
        return value

    @property
    def completedDateTime(self) -> datetime.datetime:
        value = self._completedDate
        return ensure_date_time(value)

    def setCompletedDateTime(self, value: DateDateTime):
        self._completedDate = value
        if value is not None:
            self._common_data.completed = 100
        else:
            self._common_data.completed = 0

    ## ========================================================================

    def getAppliedRecurrence(self) -> Recurrent:
        recurrence = self._common_data.recurrence
        if recurrence is None:
            return None
        if recurrence.isAsParent() is False:
            return recurrence
        parent = self.getParent()
        if parent is None:
            return None
        return parent.getAppliedRecurrence()

    def getReferenceDateTime(self) -> DateDateTime:
        if self.startDateTime is not None:
            return self.startDateTime
        ## deadline case
        return self.dueDateTime

    def printNextRecurrence(self) -> str:
        recurr = self.getAppliedRecurrence()
        if recurr is None:
            return "None"
        refDate = self.getReferenceDateTime()
        nextRepeat = recurr.nextDateTime(refDate)
        if nextRepeat is None:
            return "None"
        if isinstance(nextRepeat, datetime.datetime):
            return nextRepeat.strftime("%Y-%m-%d %H:%M")
        return nextRepeat.strftime("%Y-%m-%d")
