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

from hanlendar.gui.tasktable import get_completed_color

from hanlendar.domainmodel.todo import ToDo


_LOGGER = logging.getLogger(__name__)


class TodosTreeModel( QtCore.QAbstractItemModel ):

    headerLabels = [ "Summary", "Priority", "Complete" ]
    attrList     = [ "title", "priority", "completed" ]

    mimeType     = "TodosTreeNode"

    def __init__(self, parent, *args):
        super().__init__(parent, *args)
        self.setList( None )

    def setList(self, todos):
        self.beginResetModel()
        self.todosList = todos
        self.endResetModel()

    ## for invalid parent return elements form root list
    def index(self, row, column, parent: QModelIndex):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()
        parentItem: ToDo = self._getToDo( parent )
        children = self._getChildren( parentItem )
        if children is None:
            return QModelIndex()
        childItem = children[ row ]
        if childItem is None:
            return QModelIndex()
        return self.createIndex(row, column, childItem)

    def parent(self, index: QModelIndex):
        if not index.isValid():
            return QModelIndex()
        indexItem = self._getToDo( index )
        parentItem = self._findParent( indexItem )
        if parentItem is None:
            return QModelIndex()
        parentRow = self._findRow( parentItem )
        return self.createIndex( parentRow, 0, parentItem )

    ## for invalid parent returns number of elements in root list
    def rowCount(self, parent: QModelIndex):
        todo: ToDo = self._getToDo( parent )
        children = self._getChildren( todo )
        if children is None:
            return 0
        return len( children )

    def columnCount(self, _):
        return len(self.headerLabels)

    def data(self, index: QModelIndex, role):
        if role == QtCore.Qt.SizeHintRole:
            return QtCore.QSize(10, 30)

        todo: ToDo = self._getToDo( index )
        if todo is None:
            return None
        if role == Qt.ForegroundRole:
            return get_todo_fgcolor( todo )
        if role == QtCore.Qt.DisplayRole:
            attrIndex = index.column()
            attrName = self._getAttrName(attrIndex)
            if attrName is None:
                return None
            return getattr( todo, attrName )
        return None

    def flags(self, index: QModelIndex):
        if not index.isValid():
            return super().flags(index) | Qt.ItemIsDropEnabled
        return super().flags(index) | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled

    def headerData(self, col, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self.headerLabels[col]
        return None

    # pylint: disable=R0201
    def supportedDropActions(self):
        return Qt.MoveAction

    # pylint: disable=R0201
    def supportedDragActions(self):
        return Qt.MoveAction

    def mimeTypes(self):
        ret = []
        ret.append( self.mimeType )
        return ret

    def canDropMimeData(self, data, action, row, column, parent):
        if row != -1:
            ## disable dropping between elements (it conflicts with sorting)
            return False
        return super().canDropMimeData(data, action, row, column, parent)

    def mimeData(self, indexes):
        encodedData = QtCore.QByteArray()
        stream = QtCore.QDataStream(encodedData, QtCore.QIODevice.WriteOnly)
        for ind in indexes:
            if ind.column() != 0:
                continue
            todo = ind.internalPointer()
            coords = ToDo.getToDoCoords( self.todosList, todo )
            # pylint: disable=W0106
            stream << QtCore.QVariant(coords)
        mimeObject = QtCore.QMimeData()
        mimeObject.setData( self.mimeType, encodedData )
        return mimeObject

    def dropMimeData(self, data, action, row, _, parent):
        if action == Qt.IgnoreAction:
            return True
        if not data.hasFormat( self.mimeType ):
            return False

        if action != Qt.MoveAction:
            _LOGGER.warning("unhandled action: %s", action)
            return False

        self.beginResetModel()

        ## adding child to parent
#         print( "target:", row, column, parent.internalPointer() )

        targetParent = parent.internalPointer()
        encodedData = data.data( self.mimeType )
        stream = QtCore.QDataStream(encodedData, QtCore.QIODevice.ReadOnly)
        while not stream.atEnd():
            value = QtCore.QVariant()
            # pylint: disable=W0104
            stream >> value
            todoCoords = value.value()
            todo = ToDo.detachToDoByCoords( self.todosList, todoCoords )
            if targetParent is not None:
                targetParent.addSubtodo( todo, row )
            elif row < 0:
                self.todosList.append( todo )
            else:
                self.todosList.insert( row, todo )

        self.endResetModel()
        return True

    ## =====================================================

    def _findRow(self, todo: ToDo):
        parent = self._findParent( todo )
        children = self._getChildren( parent )
        return children.index( todo )

    def _findParent(self, child: ToDo):
        if self.todosList is None:
            return None
        for item in self.todosList:
            if item == child:
                return None
            ret = item.findParent( child )
            if ret is not None:
                return ret
        return None

    def _getChildren(self, todo: ToDo):
        if todo is None:
            return self.todosList
        return todo.subtodos

    # pylint: disable=R0201
    def _getToDo(self, modelIndex: QModelIndex):
        if modelIndex.isValid():
            return modelIndex.internalPointer()
        return None

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
        self._showCompletedTasks = False

    def showCompleted(self, show=True):
        self._showCompletedTasks = show
        self.invalidateFilter()

    def filterAcceptsRow(self, sourceRow, sourceParent: QModelIndex):
        if self._showCompletedTasks is True:
            return True
        dataIndex = self.sourceModel().index( sourceRow, 2, sourceParent )
        todo: ToDo = dataIndex.internalPointer()
        return todo.isCompleted() is False

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

        self.todosModel = TodosTreeModel(self)
        self.proxyModel = ToDoSortFilterProxyModel(self)
        self.proxyModel.setSourceModel( self.todosModel )
        self.setModel( self.proxyModel )

        header = self.header()
        header.setDefaultAlignment( Qt.AlignCenter )
        header.setHighlightSections( False )
        header.setStretchLastSection( False )
        header.setSectionResizeMode( 0, QHeaderView.Stretch )

        self.doubleClicked.connect( self.todoDoubleClicked )

        self.setToDos( [] )

    def connectData(self, dataObject):
        self.data = dataObject
        self.addNewToDo.connect( dataObject.addNewToDo )
        self.addNewSubToDo.connect( dataObject.addNewSubToDo )
        self.editToDo.connect( dataObject.editToDo )
        self.removeToDo.connect( dataObject.removeToDo )
        self.convertToDoToTask.connect( dataObject.convertToDoToTask )
        self.markCompleted.connect( dataObject.markToDoCompleted )

    def showCompletedToDos(self, show):
        self.proxyModel.showCompleted( show )
        self.updateView()

    def updateView(self):
        if self.data is None:
            return
        todosList = self.data.getManager().getToDos()
        self.setToDos( todosList )

    def getToDo(self, todoIndex: QModelIndex ):
        sourceIndex = self.proxyModel.mapToSource( todoIndex )
        # pylint: disable=W0212
        return self.todosModel._getToDo( sourceIndex )

    def setToDos( self, todosList ):
        self.setCurrentIndex( QtCore.QModelIndex() )        ## unselect
        ## disabling and enabling sorting fixes keeps sort order after data change
        self.setSortingEnabled( False )
        self.todosModel.setList( todosList )
        self.setSortingEnabled( True )

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

    def selectionChanged(self, fromSelection, toSelection):
        super().selectionChanged( fromSelection, toSelection )
        modelIndex = self.currentIndex()
        todo = self.getToDo( modelIndex )
        if todo is not None:
            self.selectedToDo.emit( todo )
        else:
            self.todoUnselected.emit()

    def todoDoubleClicked(self, modelIndex):
        todo = self.getToDo( modelIndex )
        self.editToDo.emit( todo )


def get_todo_fgcolor( todo: ToDo ) -> QBrush:
    if todo.isCompleted():
        ## completed -- green
        return QBrush( get_completed_color() )
    ## normal
    return QBrush( QColor(0, 0, 0) )
