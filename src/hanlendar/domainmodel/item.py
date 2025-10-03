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


_LOGGER = logging.getLogger(__name__)


def generate_uid():
    return str( uuid.uuid4() ) + "@hanlendar"


class Item():
    """Base class for Task and ToDo."""

    @abc.abstractmethod
    def getParent(self):
        raise NotImplementedError('You need to define this method in derived class!')

    @abc.abstractmethod
    def setParent(self, parentItem=None):
        raise NotImplementedError('You need to define this method in derived class!')

    ## return mutable reference
    @abc.abstractmethod
    def getSubitems( self ):
        raise NotImplementedError('You need to define this method in derived class!')

    @abc.abstractmethod
    def setSubitems( self, newList ):
        raise NotImplementedError('You need to define this method in derived class!')

    ## ========================================================================

    @abc.abstractmethod
    def _getUID(self):
        raise NotImplementedError('You need to define this method in derived class!')

    @abc.abstractmethod
    def _setUID(self, value):
        raise NotImplementedError('You need to define this method in derived class!')

    def getUID(self):
        return self._getUID()

    def setUID(self, value):
        self._setUID( value )

    @property
    def UID(self):
        return self.getUID()

    @UID.setter
    def UID(self, value):
        self.setUID( value )

    ## ========================================================================

    @abc.abstractmethod
    def _getTitle(self):
        raise NotImplementedError('You need to define this method in derived class!')

    @abc.abstractmethod
    def _setTitle(self, value):
        raise NotImplementedError('You need to define this method in derived class!')

    def getTitle(self):
        return self._getTitle()

    def setTitle(self, value):
        self._setTitle( value )

    @property
    def title(self):
        return self.getTitle()

    @title.setter
    def title(self, value):
        self.setTitle( value )

    ## ========================================================================

    @abc.abstractmethod
    def _getDescription(self):
        raise NotImplementedError('You need to define this method in derived class!')

    @abc.abstractmethod
    def _setDescription(self, value):
        raise NotImplementedError('You need to define this method in derived class!')

    def getDescription(self):
        return self._getDescription()

    def setDescription(self, value):
        self._setDescription( value )

    @property
    def description(self):
        return self.getDescription()

    @description.setter
    def description(self, value):
        self.setDescription( value )

    ## ========================================================================

    @abc.abstractmethod
    def _getCompleted(self):
        raise NotImplementedError('You need to define this method in derived class!')

    @abc.abstractmethod
    def _setCompleted(self, value=100):
        raise NotImplementedError('You need to define this method in derived class!')

    def getCompleted(self):
        return self._getCompleted()

    def setCompleted(self, value=100):
        if value < 0:
            value = 0
        elif value > 100:
            value = 100
        self._setCompleted( value )

    @property
    def completed(self):
        return self.getCompleted()

    @completed.setter
    def completed(self, value):
        self.setCompleted( value )

    def isCompleted(self):
        if self.completed < 100:
            return False
        subitems = self.getSubitems()
        if not subitems:
            return True
        for sub in subitems:
            if sub.isCompleted() is False:
                return False
        return True

    ## ========================================================================

    @abc.abstractmethod
    def _getPriority(self):
        raise NotImplementedError('You need to define this method in derived class!')

    @abc.abstractmethod
    def _setPriority(self, value):
        raise NotImplementedError('You need to define this method in derived class!')

    def getPriority(self):
        return self._getPriority()

    def setPriority(self, value):
        if value > 9:
            value = 9
        self._setPriority( value )

    @property
    def priority(self):
        return self.getPriority()

    @priority.setter
    def priority(self, value):
        self.setPriority( value )

    ## ========================================================================
    ## ========================================================================

    def getRootItem(self):
        currItem = self
        visitedItems = set()
        while True:
            if currItem in visitedItems:
                _LOGGER.warning( "cycle detected -- unable to find root item" )
                return None
            visitedItems.add( currItem )
            currParent = currItem.getParent()
            if currParent is None:
                return currItem
            currItem = currParent

    def getAllSubItems(self):
        """Return all sub items from tree."""
        subitems = self.getSubitems()
        if subitems is None:
            return list()
        return Item.getAllSubItemsFromList( subitems )

    def getChildCoords(self, item):
        subitems = self.getSubitems()
        return Item.getItemCoords( subitems, item )

    def getChildFromCoords(self, coords):
        subitems = self.getSubitems()
        return Item.getItemFromCoords( subitems, coords )

    def detachChildByCoords(self, coords):
        subitems = self.getSubitems()
        return Item.detachItemByCoords( subitems, coords )

    def addSubItem(self, item: 'Item', index=-1):
        subitems = self.getSubitems()
        if subitems is None:
            subitems = list()
            self.setSubitems( subitems )
        if index < 0:
            subitems.append( item )
            item.setParent( self )
        else:
            subitems.insert( index, item )
            item.setParent( self )
        return item

    def removeSubItem(self, item):
        subitems = self.getSubitems()
        if subitems is None:
            return None
        return Item.removeSubItemFromList( subitems, item )

    def replaceSubItem( self, oldItem, newItem ):
        subitems = self.getSubitems()
        if subitems is None:
            return False
        return Item.replaceSubItemInList( subitems, oldItem, newItem )

#     def __str__(self):
#         return "[t:%s d:%s c:%s p:%s]" % ( self.title, self.description, self._completed, self.priority )

    ## ==============================================================

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
                popped = itemList.pop( i )
                popped.setParent( None )
                return popped
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
                newItem.setParent( oldItem.getParent() )
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
