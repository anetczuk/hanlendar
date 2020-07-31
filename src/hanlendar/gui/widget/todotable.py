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

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import Qt, pyqtSignal, QModelIndex
from PyQt5.QtWidgets import QAbstractItemView, QHeaderView
from PyQt5.QtWidgets import QMenu
from PyQt5.QtGui import QColor, QBrush

from hanlendar.gui.customtreemodel import ItemTreeModel
from hanlendar.gui.widget.tasktable import get_completed_color

from hanlendar.domainmodel.todo import ToDo


_LOGGER = logging.getLogger(__name__)


class ToDoTreeModel( ItemTreeModel ):

    attrList = [ "title", "priority", "completed" ]

    def __init__(self, parent, *args):
        super().__init__(parent, *args)
        self.dataObject = None

    def setDataObject(self, dataObject):
        self.beginResetModel()
        self.dataObject = dataObject
        self.endResetModel()

    def data(self, index: QModelIndex, role):
        if role == QtCore.Qt.SizeHintRole:
            return QtCore.QSize(10, 30)

        item: ToDo = self.getItem( index )
        if item is None:
            return None

        if role == Qt.TextAlignmentRole:
            attrIndex = index.column()
            if attrIndex > 0:
                return Qt.AlignHCenter | Qt.AlignVCenter

        if role == Qt.ForegroundRole:
            return get_todo_fgcolor( item )

        if role == QtCore.Qt.DisplayRole:
            attrIndex = index.column()
            attrName = self._getAttrName(attrIndex)
            if attrName is None:
                return None
            return getattr( item, attrName )

        return None

    def headerLabels(self):
        return [ "Summary", "Priority", "Complete" ]

    def internalMoveMimeType(self):
        return "TodosTreeNode"

    ## overrided
    def moveItem(self, itemId, targetItem, targetIndex):
        if self.dataObject is None:
            return
        self.dataObject.moveToDo( itemId, targetItem, targetIndex )

    def getRootList(self):
        if self.dataObject is None:
            return None
        manager = self.dataObject.getManager()
        return manager.getToDos()

    def setRootList(self, newList):
        if self.dataObject is None:
            return
        self.dataObject.setTodosList( newList )

    def _getAttrName(self, attrIndex):
        if attrIndex < 0:
            return None
        if attrIndex >= len(self.attrList):
            return None
        return self.attrList[attrIndex]


## ===========================================================


class ToDoSortFilterProxyModel( QtCore.QSortFilterProxyModel ):

    def __init__(self, parentObject=None):
        super().__init__(parentObject)
        self._showCompleted = False

    def showCompleted(self, show=True):
        self._showCompleted = show
        self.invalidateFilter()

    def filterAcceptsRow(self, sourceRow, sourceParent: QModelIndex):
        if self._showCompleted is True:
            return True
        dataIndex = self.sourceModel().index( sourceRow, 2, sourceParent )
        item: ToDo = dataIndex.internalPointer()
        return item.isCompleted() is False

    def lessThan(self, left: QModelIndex, right: QModelIndex):
        leftData  = self.sourceModel().data(left, QtCore.Qt.DisplayRole)
        rightData = self.sourceModel().data(right, QtCore.Qt.DisplayRole)
        return leftData < rightData


## ===========================================================


class ToDoTable( QtWidgets.QTreeView ):

    selectedToDo        = pyqtSignal( ToDo )
    todoUnselected      = pyqtSignal()
    addNewToDo          = pyqtSignal()
    addNewSubToDo       = pyqtSignal( ToDo )
    editToDo            = pyqtSignal( ToDo )
    removeToDo          = pyqtSignal( ToDo )
    convertToDoToTask   = pyqtSignal( ToDo )
    markCompleted       = pyqtSignal( ToDo )

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)

        self.data = None

        self.setSelectionBehavior( QAbstractItemView.SelectRows )
        self.setSelectionMode( QAbstractItemView.SingleSelection )
        self.setEditTriggers( QAbstractItemView.NoEditTriggers )
        self.setAlternatingRowColors( True )
        self.setSortingEnabled( True )

        self.setDragEnabled( True )
        self.setDropIndicatorShown( True )
        self.setDragDropMode( QAbstractItemView.InternalMove )
        self.setDragDropOverwriteMode(False)

        self.itemsModel = ToDoTreeModel(self)
        self.proxyModel = ToDoSortFilterProxyModel(self)
        self.proxyModel.setSourceModel( self.itemsModel )
        self.setModel( self.proxyModel )

        header = self.header()
        header.setDefaultAlignment( Qt.AlignCenter )
        header.setHighlightSections( False )
        header.setStretchLastSection( False )
        header.setSectionResizeMode( 0, QHeaderView.Stretch )

        self.doubleClicked.connect( self.itemDoubleClicked )

    def connectData(self, dataObject):
        self.data = dataObject
        self.itemsModel.setDataObject( dataObject )
        self.addNewToDo.connect( dataObject.addNewToDo )
        self.addNewSubToDo.connect( dataObject.addNewSubToDo )
        self.editToDo.connect( dataObject.editToDo )
        self.removeToDo.connect( dataObject.removeToDo )
        self.convertToDoToTask.connect( dataObject.convertToDoToTask )
        self.markCompleted.connect( dataObject.markToDoCompleted )

    def showCompletedItems(self, show):
        self.proxyModel.showCompleted( show )
        self.updateView()

    def updateView(self):
        if self.data is None:
            return
        self.itemsModel.setDataObject( self.data )

    def getToDo(self, itemIndex: QModelIndex ):
        sourceIndex = self.proxyModel.mapToSource( itemIndex )
        return self.itemsModel.getItem( sourceIndex )

    def contextMenuEvent( self, event ):
        evPos     = event.pos()
        globalPos = self.viewport().mapToGlobal( evPos )

        todo: ToDo = None
        mIndex = self.indexAt( evPos )
        if mIndex is not None:
            todo = self.getToDo( mIndex )

        contextMenu         = QMenu(self)
        addToDoAction       = contextMenu.addAction("New ToDo")
        addSubToDoAction    = contextMenu.addAction("New Sub ToDo")
        editToDoAction      = contextMenu.addAction("Edit ToDo")
        removeToDoAction    = contextMenu.addAction("Remove ToDo")
        convertToDoAction   = contextMenu.addAction("Convert to Task")
        markCompletedAction = contextMenu.addAction("Mark completed")

        if todo is None:
            ## context menu on background
            addSubToDoAction.setEnabled( False )
            editToDoAction.setEnabled( False )
            removeToDoAction.setEnabled( False )
            convertToDoAction.setEnabled( False )
            markCompletedAction.setEnabled( False )

        action = contextMenu.exec_( globalPos )

        if action == addToDoAction:
            self.addNewToDo.emit()
        elif action == addSubToDoAction:
            self.addNewSubToDo.emit( todo )
        elif action == editToDoAction:
            self.editToDo.emit( todo )
        elif action == removeToDoAction:
            self.removeToDo.emit( todo )
        elif action == convertToDoAction:
            self.convertToDoToTask.emit( todo )
        elif action == markCompletedAction:
            self.markCompleted.emit( todo )

    def selectionChanged(self, toSelection, fromSelection):
        super().selectionChanged( toSelection, fromSelection )
        modelIndex = self.currentIndex()
        todo = self.getToDo( modelIndex )
        if todo is not None:
            self.selectedToDo.emit( todo )
        else:
            self.todoUnselected.emit()

    def itemDoubleClicked(self, modelIndex):
        todo = self.getToDo( modelIndex )
        self.editToDo.emit( todo )

    def mousePressEvent(self, event):
        pos = event.pos()
        itemIndex = self.indexAt(pos)
        if itemIndex.isValid() is False:
            self.setCurrentIndex(itemIndex)
            self.clearSelection()
        super().mousePressEvent( event )


def get_todo_fgcolor( todo: ToDo ) -> QBrush:
    if todo.isCompleted():
        ## completed -- green
        return QBrush( get_completed_color() )
    ## normal
    return QBrush( QColor(0, 0, 0) )
