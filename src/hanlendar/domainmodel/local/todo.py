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

from hanlendar import persist

from hanlendar.domainmodel.item import Item, generate_uid


_LOGGER = logging.getLogger(__name__)


class LocalToDo( Item, persist.Versionable ):
    """ToDo is entity without placement in time."""

    ## 0: add subtodos
    ## 1: add base class Item
    ## 2: rename: 'title' to '_title', 'description' to '_description', 'priority' to '_priority'
    ## 3: rescaled 'priority'
    ## 4: added 'UID'
    _class_version = 4

    def __init__(self, title="" ):
        super(LocalToDo, self).__init__()
        self._UID                           = generate_uid()
        self._title                         = title
        self._description                   = ""
        self._completed                     = 0        ## in range [0..100]
        self._priority                      = 5        ## lower number, greater priority

        self._parent                        = None
        self.subitems: list                 = None

    def _convertstate_(self, dict_, dictVersion_ ):
        _LOGGER.info( "converting object from version %s to %s", dictVersion_, self._class_version )

        if dictVersion_ is None:
            dictVersion_ = -1

        ## set of conditions converting dict_ to recent version
        if dictVersion_ < 0:
            ## initialize subtodos field
            dict_["subtodos"] = None
            dictVersion_ = 0

        if dictVersion_ == 0:
            ## base class extracted, "subtodos" renamed to "subitems"
            dict_["subitems"] = dict_["subtodos"]
            dict_.pop('subtodos', None)
            dictVersion_ = 1

        if dictVersion_ == 1:
            ## rename fields
            dict_["_title"]       = dict_.pop( "title", "" )
            dict_["_description"] = dict_.pop( "description", "" )
            dict_["_priority"]    = dict_.pop( "priority", 10 )
            dictVersion_ = 2

        if dictVersion_ == 2:
            ## rescale priority
            priority = dict_.pop( "_priority", 10 )
            dict_["_priority"] = int( priority / 2.0 )
            dictVersion_ = 3

        if dictVersion_ == 3:
            dict_["_UID"] = generate_uid()
            dictVersion_ = 4

        # pylint: disable=W0201
        self.__dict__ = dict_

    def __str__(self):
        subLen = 0
        subitems = self.getSubitems()
        if subitems is not None:
            subLen = len(subitems)
        return "[t:%s d:%s c:%s p:%s subs: %s]" % (
            self.title, self.description,
            self._completed, self.priority, subLen )

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
    def _getUID(self):
        return self._UID

    ## overriden
    def _setUID(self, value):
        self._UID = value

    ## ========================================================================

    ## overriden
    def _getTitle(self):
        return self._title

    ## overriden
    def _setTitle(self, value):
        self._title = value

    ## ========================================================================

    ## overriden
    def _getDescription(self):
        return self._description

    ## overriden
    def _setDescription(self, value):
        self._description = value

    ## ========================================================================

    ## overrided
    def _getCompleted(self):
        return self._completed

    ## overrided
    def _setCompleted(self, value=100):
        self._completed = value

    ## ========================================================================

    ## overrided
    def _getPriority(self):
        return self._priority

    ## overrided
    def _setPriority(self, value):
        self._priority = value

    ## ========================================================================

    def addSubtodo(self, todo=None, index=-1):
        if todo is None:
            todo = LocalToDo()
        return self.addSubItem(todo, index)
