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
from typing import List

from PyQt5 import QtCore
from PyQt5.QtCore import Qt, QModelIndex

from hanlendar.domainmodel.item import Item


_LOGGER = logging.getLogger(__name__)


class CustomTreeModel( QtCore.QAbstractItemModel ):

    ## for invalid parent returns number of elements in root list
    def rowCount(self, parent: QModelIndex):
        parentItem = self.getItem( parent )
        children = self.getChildren( parentItem )
        if children is None:
            return 0
        return len( children )

    def columnCount(self, _):
        labels = self.headerLabels()
        return len(labels)

    def headerData(self, col, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            labels = self.headerLabels()
            return labels[col]
        return None

    ## for invalid parent return elements form root list
    def index(self, row, column, parent: QModelIndex):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()
        parentItem = self.getItem( parent )         ## None allowed
        children = self.getChildren( parentItem )
        if children is None:
            return QModelIndex()
        childItem = children[ row ]
        if childItem is None:
            return QModelIndex()
        return self.createIndex(row, column, childItem)

    def parent(self, index: QModelIndex):
        if not index.isValid():
            return QModelIndex()
        indexItem = self.getItem( index )
        if indexItem is None:
            return QModelIndex()
        parentItem = self.getParent( indexItem )
        if parentItem is None:
            return QModelIndex()
        grandParentItem = self.getParent( parentItem )
        children = self.getChildren( grandParentItem )
        try:
            parentRow = children.index( parentItem )
            return self.createIndex( parentRow, 0, parentItem )
        except ValueError:
            return QModelIndex()

    def flags(self, index: QModelIndex):
        if not index.isValid():
            return super().flags(index) | Qt.ItemIsDropEnabled
        return super().flags(index) | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled

    # pylint: disable=R0201
    def supportedDropActions(self):
        return Qt.MoveAction

    # pylint: disable=R0201
    def supportedDragActions(self):
        return Qt.MoveAction

    def canDropMimeData(self, data, action, row, column, parent):
        if row != -1:
            ## disable dropping between elements (it conflicts with sorting)
            return False
        return super().canDropMimeData(data, action, row, column, parent)

    def mimeTypes(self):
        return [ self.internalMoveMimeType() ]

    def mimeData(self, indexes):
        encodedData = QtCore.QByteArray()
        stream = QtCore.QDataStream(encodedData, QtCore.QIODevice.WriteOnly)
        for ind in indexes:
            if ind.column() != 0:
                continue
            item = ind.internalPointer()
            itemId = self.getItemId( item )
            # pylint: disable=W0106
            stream << QtCore.QVariant(itemId)
        mimeObject = QtCore.QMimeData()
        mimeObject.setData( self.internalMoveMimeType(), encodedData )
        return mimeObject

    def dropMimeData(self, data, action, row, _, parent):
        if action == Qt.IgnoreAction:
            return True
        if not data.hasFormat( self.internalMoveMimeType() ):
            return False

        if action != Qt.MoveAction:
            _LOGGER.warning("unhandled action: %s", action)
            return False

        self.beginResetModel()

        ## adding child to parent
        targetParent = parent.internalPointer()
        encodedData = data.data( self.internalMoveMimeType() )
        stream = QtCore.QDataStream(encodedData, QtCore.QIODevice.ReadOnly)
        while not stream.atEnd():
            value = QtCore.QVariant()
            # pylint: disable=W0104
            stream >> value
            itemCoords = value.value()
            self.moveItem( itemCoords, targetParent, row )

        self.endResetModel()
        return True

    # pylint: disable=R0201
    def getItem(self, itemIndex: QModelIndex):
        if itemIndex.isValid():
            return itemIndex.internalPointer()
        return None

    def getIndex(self, item, parentIndex: QModelIndex=None):
        if parentIndex is None:
            parentIndex = QModelIndex()
        if parentIndex.isValid():
            # dataTask = parentIndex.data( Qt.UserRole )
            dataTask = parentIndex.internalPointer()
            if dataTask == item:
                return parentIndex
        elems = self.rowCount( parentIndex )
        for i in range(elems):
            index = self.index( i, 0, parentIndex )
            subIndex = self.getIndex(item, index)
            if subIndex is not None:
                return subIndex
        return None

    ## ==================================================================

    @abc.abstractmethod
    def headerLabels(self) -> List[str]:
        raise NotImplementedError('You need to define this method in derived class!')

    @abc.abstractmethod
    def internalMoveMimeType(self) -> str:
        raise NotImplementedError('You need to define this method in derived class!')

    @abc.abstractmethod
    def getChildren(self, parent: object):
        raise NotImplementedError('You need to define this method in derived class!')

    @abc.abstractmethod
    def getParent(self, item: object):
        raise NotImplementedError('You need to define this method in derived class!')

    @abc.abstractmethod
    def getItemId(self, item: object):
        """Return object's identifier.

        It could be unique number or item's coordinates in objects tree.
        """
        raise NotImplementedError('You need to define this method in derived class!')

    @abc.abstractmethod
    def moveItem(self, itemId, targetItem: object, targetIndex):
        raise NotImplementedError('You need to define this method in derived class!')


## ====================================================================


class ItemTreeModel( CustomTreeModel ):

#     def moveItem(self, itemId, targetItem, targetIndex):
#         itemsList = self.getRootList()
#         sourceItem = Item.detachItemByCoords( itemsList, itemId )
#         if targetItem is not None:
#             targetItem.addSubItem( sourceItem, targetIndex )
#         elif targetIndex < 0:
#             itemsList.append( sourceItem )
#         else:
#             itemsList.insert( targetIndex, sourceItem )
#         ## triggers change event
#         self.setRootList( itemsList )

    def getChildren(self, parent):
        if parent is not None:
            return parent.getSubitems()
        return self.getRootList()

    def getParent(self, item):
        parent = item.getParent()
        return parent

    def getItemId(self, item: object):
        itemsList = self.getRootList()
        return Item.getItemCoords( itemsList, item )

    ## ================================================================

    @abc.abstractmethod
    def getRootList(self):
        raise NotImplementedError('You need to define this method in derived class!')

#     @abc.abstractmethod
#     def setRootList(self, newList):
#         raise NotImplementedError('You need to define this method in derived class!')
