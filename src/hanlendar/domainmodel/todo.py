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


_LOGGER = logging.getLogger(__name__)


class ToDo( persist.Versionable ):
    """ToDo is entity without placement in time."""

    ## 0: add subtodos
    _class_version = 0

    def __init__(self, title=""):
        self.title                          = title
        self.description                    = ""
        self._completed                     = 0        ## in range [0..100]
        self.priority                       = 10       ## lower number, greater priority
        self.subtodos: list                 = None

    def _convertstate_(self, dict_, dictVersion_ ):
        _LOGGER.info( "converting object from version %s to %s", dictVersion_, self._class_version )

        if dictVersion_ is None:
            ## initialize subtodos field
            # pylint: disable=W0201
            self.__dict__ = dict_
            self.subtodos = None
            return

    @property
    def completed(self):
        return self._completed

    @completed.setter
    def completed(self, value):
        self.setCompleted( value )

    def setCompleted(self, value=100):
        if value < 0:
            value = 0
        elif value > 100:
            value = 100
        self._completed = value

    def isCompleted(self):
        if self._completed < 100:
            return False
        if not self.subtodos:
            return True
        for sub in self.subtodos:
            if sub.isCompleted() is False:
                return False
        return True

    def addSubtodo(self, subitem, index=-1):
        if self.subtodos is None:
            self.subtodos = list()
        if index < 0:
            self.subtodos.append( subitem )
        else:
            self.subtodos.insert( index, subitem )
        return subitem

    def findParent(self, child):
        if self.subtodos is None:
            return None
        for item in self.subtodos:
            if item == child:
                return self
            ret = item.findParent( child )
            if ret is not None:
                return ret
        return None

    def getChildCoords(self, todo):
        return ToDo.getToDoCoords( self.subtodos, todo )

    def getChildFromCoords(self, coords):
        return ToDo.getToDoFromCoords( self.subtodos, coords )

    def detachChildByoords(self, coords):
        return ToDo.detachToDoByCoords( self.subtodos, coords )

    def __str__(self):
        return "[t:%s d:%s c:%s p:%s]" % ( self.title, self.description, self._completed, self.priority )

    @staticmethod
    def getToDoCoords( todosList, todo ):
        if todosList is None:
            return None
        if not todosList:
            return None
        lSize = len(todosList)
        for i in range( lSize ):
            item = todosList[i]
            if item == todo:
                return [i]
            ret = item.getChildCoords( todo )
            if ret is not None:
                return [i] + ret
        return None

    @staticmethod
    def getToDoFromCoords( todosList, coords ):
        if todosList is None:
            return None
        if not todosList:
            return None
        if coords is None:
            return None
        if not coords:
            return None
        todoCoords = list( coords )
        elemIndex = todoCoords.pop(0)
        if elemIndex >= len(todosList):
            return None
        todo = todosList[ elemIndex ]
        if not todoCoords:
            return todo
        return todo.getChildFromCoords( todoCoords )

    @staticmethod
    def detachToDoByCoords( todosList, coords ):
        if todosList is None:
            return None
        if not todosList:
            return None
        if coords is None:
            return None
        if not coords:
            return None
        todoCoords = list( coords )
        elemIndex = todoCoords.pop(0)
        if elemIndex >= len(todosList):
            return None
        todo = todosList[ elemIndex ]
        if not todoCoords:
            todosList.pop( elemIndex )
            return todo
        return todo.getChildFromCoords( todoCoords )

    @staticmethod
    def sortByPriority( todo ):
        return todo.priority

    @staticmethod
    def sortTree( todoList, attrName: str, reverseOrder: bool ):
        if todoList is None:
            return
        todoList.sort( key=lambda x: getattr(x, attrName), reverse=reverseOrder )
        for todo in todoList:
            ToDo.sortTree( todo.subtodos, attrName, reverseOrder )
