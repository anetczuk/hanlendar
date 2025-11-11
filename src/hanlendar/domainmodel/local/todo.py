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

from hanlendar.domainmodel.item import Item, generate_uid


_LOGGER = logging.getLogger(__name__)


class LocalToDo(Item, persist.Versionable):
    """ToDo is entity without placement in time."""

    ## 0: add subtodos
    ## 1: add base class Item
    ## 2: rename: 'title' to '_title', 'description' to '_description', 'priority' to '_priority'
    ## 3: rescaled 'priority'
    ## 4: added 'UID'
    ## 5: added '_createDate'
    ## 6: added '_location', '_url', '_sequence', '_lastModifiedDate
    ## 7: added '_unknown_props'
    _class_version = 7

    def __init__(self, title=""):
        super().__init__()

        self._parent = None
        self.subitems: list = None

        self._UID: str = generate_uid()

        self._title: str = title
        self._location: str = ""
        self._url: str = ""
        self._description: str = ""

        self._sequence = 0
        self._completed = 0  ## in range [0..100]

        ## Evolution priority meanings:
        ##  missing: Undefined
        ##  3: High
        ##  5: Normal
        ##  7: Low
        self._priority: int = 5  ## lower number, greater priority

        self._createDate: datetime.datetime = datetime.datetime.now(datetime.timezone.utc)
        self._lastModifiedDate: datetime.datetime = datetime.datetime.now(datetime.timezone.utc)

        ## unknown icalendar properties
        self._unknown_props: dict[Any, Any] = None

    def _convertstate_(self, dict_, dict_version_):
        _LOGGER.info("converting object from version %s to %s", dict_version_, self._class_version)

        if dict_version_ is None:
            dict_version_ = -1

        ## set of conditions converting dict_ to recent version
        if dict_version_ < 0:
            ## initialize subtodos field
            dict_["subtodos"] = None
            dict_version_ = 0

        if dict_version_ == 0:
            ## base class extracted, "subtodos" renamed to "subitems"
            dict_["subitems"] = dict_["subtodos"]
            dict_.pop("subtodos", None)
            dict_version_ += 1

        if dict_version_ == 1:
            ## rename fields
            dict_["_title"] = dict_.pop("title", "")
            dict_["_description"] = dict_.pop("description", "")
            dict_["_priority"] = dict_.pop("priority", 10)
            dict_version_ += 1

        if dict_version_ == 2:
            ## rescale priority
            priority = dict_.pop("_priority", 10)
            dict_["_priority"] = int(priority / 2.0)
            dict_version_ += 1

        if dict_version_ == 3:
            dict_["_UID"] = generate_uid()
            dict_version_ += 1

        if dict_version_ == 4:
            dict_["_createDate"] = datetime.datetime.now(datetime.timezone.utc)
            dict_version_ += 1

        if dict_version_ == 5:
            dict_["_location"] = ""
            dict_["_url"] = ""
            dict_["_sequence"] = 0
            dict_version_ += 1

        if dict_version_ == 6:
            dict_["_unknown_props"] = None
            dict_version_ += 1

        # pylint: disable=W0201
        self.__dict__ = dict_

    def __str__(self):
        subLen = 0
        subitems = self.getSubitems()
        if subitems is not None:
            subLen = len(subitems)
        return f"[t:{self.title} d:{self.description} c:{self._completed} p:{self.priority} subs:{subLen}]"

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
    def _getUID(self):
        return self._UID

    ## overriden
    def _setUID(self, value):
        self._UID = value

    ## overriden
    def _getTitle(self) -> str:
        return self._title

    ## overriden
    def _setTitle(self, value: str):
        self._title = value

    ## overriden
    def _getLocation(self) -> str:
        return self._location

    ## overriden
    def _setLocation(self, value: str):
        self._location = value

    ## overriden
    def _getURL(self) -> str:
        return self._url

    ## overriden
    def _setURL(self, value: str):
        self._url = value

    ## overriden
    def _getDescription(self) -> str:
        return self._description

    ## overriden
    def _setDescription(self, value: str):
        self._description = value

    ## overriden
    def _getSequence(self) -> int:
        return self._sequence

    ## overriden
    def _setSequence(self, value: int):
        self._sequence = value

    ## overrided
    def _getCompleted(self):
        return self._completed

    ## overrided
    def _setCompleted(self, value=100):
        self._completed = value

    ## overrided
    def _getPriority(self):
        return self._priority

    ## overrided
    def _setPriority(self, value):
        self._priority = value

    ## ========================================================================

    @property
    def createDateTime(self) -> datetime.datetime:
        return self._createDate

    @property
    def lastModifiedDateTime(self) -> datetime.datetime:
        return self._lastModifiedDate
