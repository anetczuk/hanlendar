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

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QAbstractItemView, QHeaderView
from PyQt5.QtWidgets import QMenu
from PyQt5.QtGui import QColor, QBrush

from hanlendar.gui.tasktable import get_completed_color

from hanlendar.domainmodel.manager import Manager
from hanlendar.domainmodel.todo import ToDo


_LOGGER = logging.getLogger(__name__)


class TodosModel(QtCore.QAbstractTableModel):
    
    headerLabels = [ "Summary", "Priority", "Complete" ]
    attrList     = [ "title", "priority", "completed" ]
    
    def __init__(self, parent, todos=None, *args):
        super().__init__(parent, *args)
        if todos is not None:
            self.todosList = todos
        else:
            self.todosList = []

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.todosList)

    def columnCount(self, parent=QtCore.QModelIndex()):
        return len(self.headerLabels)

    def data(self, index, role):
        if not index.isValid():
            return None
        elif role != QtCore.Qt.DisplayRole:
            return None
        attrIndex = index.column()
        attrName = self._getAttrName(attrIndex)
        if attrName is None:
            return None
        todo: ToDo = self.todosList[ index.row() ]
        return getattr( todo, attrName )

    def headerData(self, col, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self.headerLabels[col]
        return None

    def sort(self, column, order = Qt.AscendingOrder):
        attrName = self._getAttrName( column )
        if attrName is None:
            _LOGGER.warning("invalid attribute index: %s", column)
            return
        reverseOrder = False
        if order == Qt.AscendingOrder:
            reverseOrder = True
        self.todosList.sort( key=lambda x: getattr(x, attrName), reverse=reverseOrder )
        self.layoutChanged.emit()

    def _getAttrName(self, attrIndex):
        if attrIndex < 0:
            return None
        if attrIndex >= len(self.attrList):
            return None
        return self.attrList[attrIndex]


class ToDoTable( QtWidgets.QTableView ):

    selectedToDo        = pyqtSignal( ToDo )
    todoUnselected      = pyqtSignal()
    addNewToDo          = pyqtSignal()
    editToDo            = pyqtSignal( ToDo )
    removeToDo          = pyqtSignal( ToDo )
    convertToDoToTask   = pyqtSignal( ToDo )
    markCompleted       = pyqtSignal( ToDo )

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)

        self.data = None
        self.showCompleted = False

        self.setSelectionBehavior( QAbstractItemView.SelectRows )
        self.setSelectionMode( QAbstractItemView.SingleSelection )
        self.setEditTriggers( QAbstractItemView.NoEditTriggers )
        self.setAlternatingRowColors( True )
        self.setShowGrid( False )

        model = TodosModel(self)
        self.setModel(model)

        header = self.horizontalHeader()
        header.setHighlightSections( False )
        header.setSectionResizeMode( 0, QHeaderView.Stretch )

        self.doubleClicked.connect( self.todoDoubleClicked )

        self.setToDos( [] )

    def connectData(self, dataObject):
        self.data = dataObject
        self.addNewToDo.connect( dataObject.addNewToDo )
        self.editToDo.connect( dataObject.editToDo )
        self.removeToDo.connect( dataObject.removeToDo )
        self.convertToDoToTask.connect( dataObject.convertToDoToTask )
        self.markCompleted.connect( dataObject.markToDoCompleted )

    def clear(self):
        self.setRowCount( 0 )
        self.emitSelectedToDo()

    def showCompletedToDos(self, show):
        self.showCompleted = show
        self.updateView()

    def updateView(self):
        todosList = self.data.getManager().getToDos()
        self.setToDos( todosList )
        self.setCurrentIndex( QtCore.QModelIndex() )        ## unselect

    def getToDo(self, todoIndex):
        if todoIndex < 0:
            return None
        todos = self.model().todosList
        if todoIndex >= len(todos):
            return None
        return todos[ todoIndex ]

    def setToDos( self, todosList ):
        self.model().todosList = todosList
        self.model().layoutChanged.emit()

    def contextMenuEvent( self, event ):
        evPos     = event.pos()
        globalPos = self.viewport().mapToGlobal( evPos )

        todo: ToDo = None
        mIndex = self.indexAt( evPos )
        if mIndex is not None:
            rowIndex = mIndex.row()
            todo = self.getToDo( rowIndex )

        contextMenu = QMenu(self)
        addToDoAction = contextMenu.addAction("New ToDo")
        editToDoAction = contextMenu.addAction("Edit ToDo")
        removeToDoAction = contextMenu.addAction("Remove ToDo")
        convertToDoAction = contextMenu.addAction("Convert to Task")
        markCompletedAction = contextMenu.addAction("Mark completed")

        if todo is None:
            ## context menu on background
            editToDoAction.setEnabled( False )
            removeToDoAction.setEnabled( False )
            convertToDoAction.setEnabled( False )
            markCompletedAction.setEnabled( False )

        action = contextMenu.exec_( globalPos )

        if action == addToDoAction:
            self.addNewToDo.emit()
        elif action == editToDoAction:
            self.editToDo.emit( todo )
        elif action == removeToDoAction:
            self.removeToDo.emit( todo )
        elif action == convertToDoAction:
            self.convertToDoToTask.emit( todo )
        elif action == markCompletedAction:
            self.markCompleted.emit( todo )

#     def todoSelectionChanged(self):
#         todoIndex = self.currentRow()
#         todo = self.getToDo( todoIndex )
#         self.emitSelectedToDo( todo )

    def selectionChanged(self, fromSelection, toSelection):
        super().selectionChanged( fromSelection, toSelection )
        modelIndex = self.currentIndex()
        rowIndex = modelIndex.row()
        todo = self.getToDo( rowIndex )
        self.emitSelectedToDo( todo )

    def todoDoubleClicked(self, modelIndex):
        rowIndex = modelIndex.row()
        todo = self.getToDo( rowIndex )
        self.editToDo.emit( todo )

    def emitSelectedToDo( self, todo=None ):
        if todo is not None:
            self.selectedToDo.emit( todo )
        else:
            self.todoUnselected.emit()

#     def dropEvent(self, event):
#         if event.source() != self:
#             ## do not allow dropping from other elements
#             return
#         ## internal drag & drop
#         sourceRows = set([mi.row() for mi in self.selectedIndexes()])
#         targetRow = self.indexAt(event.pos()).row()
#         sourceRows.discard(targetRow)
#         if len(sourceRows) != 1:
#             return
#         sourceRow = sourceRows.pop()
#         sourceToDo = self.getToDo( sourceRow )
#         targetToDo = self.getToDo( targetRow )
#         #print( "drop event:", sourceRow, targetRow, sourceToDo.title, targetToDo.title )
# 
#         manager: Manager = self.data.getManager()
#         if targetToDo is None:
#             manager.setToDoPriorityLeast( sourceToDo )
#             self.data.todoChanged.emit( sourceToDo )
#             self.updateView()
#             return
#         sourcePriority = sourceToDo.priority
#         targetPriority = targetToDo.priority
#         if targetPriority == sourcePriority:
#             ## no priority to change
#             return
#         if targetPriority > sourcePriority:
#             newPriority = targetPriority + 1
#             manager.setToDoPriorityRaise( sourceToDo, newPriority )
#         else:
#             newPriority = targetPriority - 1
#             manager.setToDoPriorityDecline( sourceToDo, newPriority )
#         self.data.todoChanged.emit( sourceToDo )
#         self.updateView()


def get_todo_fgcolor( todo: ToDo ) -> QBrush:
    if todo.isCompleted():
        ## completed -- green
        return QBrush( get_completed_color() )
    ## normal
    return QBrush( QColor(0, 0, 0) )
