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

from PyQt5 import QtCore
from PyQt5.QtCore import Qt, QModelIndex


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
        parentRow = children.index( parentItem )
        return self.createIndex( parentRow, 0, parentItem )

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
            coords = self.getItemCoords( item )
            # pylint: disable=W0106
            stream << QtCore.QVariant(coords)
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

    @abc.abstractmethod
    def headerLabels(self):
        raise NotImplementedError('You need to define this method in derived class!')

    @abc.abstractmethod
    def internalMoveMimeType(self):
        raise NotImplementedError('You need to define this method in derived class!')

    ## ==================================================================

    @abc.abstractmethod
    def getItem(self, item: QModelIndex):
        raise NotImplementedError('You need to define this method in derived class!')

    @abc.abstractmethod
    def getChildren(self, parent: object):
        raise NotImplementedError('You need to define this method in derived class!')

    @abc.abstractmethod
    def getParent(self, item: object):
        raise NotImplementedError('You need to define this method in derived class!')

    @abc.abstractmethod
    def getItemCoords(self, item: object):
        raise NotImplementedError('You need to define this method in derived class!')

    @abc.abstractmethod
    def moveItem(self, itemCoords, targetItem: object, targetIndex):
        raise NotImplementedError('You need to define this method in derived class!')
