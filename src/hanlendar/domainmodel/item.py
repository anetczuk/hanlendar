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


_LOGGER = logging.getLogger(__name__)


class Item():
    """Base class for Task and ToDo."""

    def __init__(self, title=""):
        self.title                          = title
        self.description                    = ""
        self._completed                     = 0        ## in range [0..100]
        self.priority                       = 10       ## lower number, greater priority
        self.subitems: list                 = None

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
        if not self.subitems:
            return True
        for sub in self.subitems:
            if sub.isCompleted() is False:
                return False
        return True

    def getAllSubItems(self):
        """Return all sub items from tree."""
        if self.subitems is None:
            return list()
        return Item.getAllSubItemsFromList( self.subitems )

    def findParent(self, child):
        if self.subitems is None:
            return None
        for item in self.subitems:
            if item == child:
                return self
            ret = item.findParent( child )
            if ret is not None:
                return ret
        return None

    def getChildCoords(self, item):
        return Item.getItemCoords( self.subitems, item )

    def getChildFromCoords(self, coords):
        return Item.getItemFromCoords( self.subitems, coords )

    def detachChildByCoords(self, coords):
        return Item.detachItemByCoords( self.subitems, coords )

    def addSubItem(self, item, index=-1):
        if self.subitems is None:
            self.subitems = list()
        if index < 0:
            self.subitems.append( item )
        else:
            self.subitems.insert( index, item )
        return item

    def removeSubItem(self, item):
        if self.subitems is None:
            return None
        return Item.removeSubItemFromList( self.subitems, item )

    def replaceSubItem( self, oldItem, newItem ):
        if self.subitems is None:
            return False
        return Item.replaceSubItemInList( self.subitems, oldItem, newItem )

#     def __str__(self):
#         return "[t:%s d:%s c:%s p:%s]" % ( self.title, self.description, self._completed, self.priority )

    @staticmethod
    def getAllSubItemsFromList( itemList ):
        """Return all sub items from tree."""
        if itemList is None:
            return list()
        retList = list()
        for item in itemList:
            retList.append( item )
            retList += item.getAllSubItems()
        return retList

    @staticmethod
    def removeSubItemFromList( itemList, item ):
        if itemList is None:
            return None
        for i, _ in enumerate(itemList):
            currItem = itemList[i]
            if currItem == item:
                return itemList.pop( i )
            removed = currItem.removeSubItem( item )
            if removed is not None:
                return removed
        return None

    @staticmethod
    def replaceSubItemInList( itemList, oldItem, newItem ):
        if itemList is None:
            return None
        for i, _ in enumerate(itemList):
            currItem = itemList[i]
            if currItem == oldItem:
                itemList[i] = newItem
                return True
            if currItem.replaceSubItem( oldItem, newItem ) is True:
                return True
        return False

    @staticmethod
    def getItemCoords( itemsList, item ):
        if itemsList is None:
            return None
        if not itemsList:
            return None
        lSize = len(itemsList)
        for i in range( lSize ):
            currItem = itemsList[i]
            if currItem == item:
                return [i]
            ret = currItem.getChildCoords( item )
            if ret is not None:
                return [i] + ret
        return None

    @staticmethod
    def getItemFromCoords( itemsList, coords ):
        if itemsList is None:
            return None
        if not itemsList:
            return None
        if coords is None:
            return None
        if not coords:
            return None
        itemCoords = list( coords )
        elemIndex = itemCoords.pop(0)
        if elemIndex >= len(itemsList):
            return None
        item = itemsList[ elemIndex ]
        if not itemCoords:
            return item
        return item.getChildFromCoords( itemCoords )

    @staticmethod
    def detachItemByCoords( itemsList, coords ):
        if itemsList is None:
            return None
        if not itemsList:
            return None
        if coords is None:
            return None
        if not coords:
            return None
        itemCoords = list( coords )
        elemIndex = itemCoords.pop(0)
        if elemIndex >= len(itemsList):
            return None
        item = itemsList[ elemIndex ]
        if not itemCoords:
            itemsList.pop( elemIndex )
            return item
        return item.detachChildByCoords( itemCoords )

    @staticmethod
    def sortByPriority( item ):
        return item.priority
