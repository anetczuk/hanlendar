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

# import logging

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QAbstractItemView, QHeaderView
from PyQt5.QtWidgets import QMenu
from PyQt5.QtGui import QColor, QBrush

from hanlendar.gui.tasktable import get_completed_color

from hanlendar.domainmodel.manager import Manager
from hanlendar.domainmodel.todo import ToDo


# _LOGGER = logging.getLogger(__name__)


class ToDoTable( QTableWidget ):

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

        headerLabels = [ "Summary", "Priority", "Complete" ]
        self.setColumnCount( len(headerLabels) )
        self.setHorizontalHeaderLabels( headerLabels )

        header = self.horizontalHeader()
        header.setHighlightSections( False )
        header.setSectionResizeMode( 0, QHeaderView.Stretch )

        self.itemSelectionChanged.connect( self.todoSelectionChanged )
        self.itemClicked.connect( self.todoClicked )
        self.itemDoubleClicked.connect( self.todoDoubleClicked )

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

    def getToDo(self, todoIndex):
        if todoIndex < 0:
            return None
        if todoIndex >= self.rowCount():
            return None
        tableItem = self.item( todoIndex, 0 )
        userData = tableItem.data( Qt.UserRole )
        return userData

    def setToDos( self, todosList ):
        self.clear()

        self.setSortingEnabled( False )     ## workaround to fix disappearing cells content

        if self.showCompleted is False:
            todosList = [ todo for todo in todosList if not todo.isCompleted() ]

        todosSize = len( todosList )
        self.setRowCount( todosSize )

        for i in range(0, todosSize):
            todo: ToDo = todosList[i]

            fgColor = get_todo_fgcolor( todo )
            titleItem = QTableWidgetItem( todo.title )
            titleItem.setData( Qt.UserRole, todo )
            titleItem.setForeground( fgColor )
            self.setItem( i, 0, titleItem )

            priorityItem = QTableWidgetItem()
            priorityItem.setData( Qt.EditRole, todo.priority )                      ## handles int type properly
            priorityItem.setTextAlignment( Qt.AlignHCenter | Qt.AlignVCenter )
            priorityItem.setForeground( fgColor )
            self.setItem( i, 1, priorityItem )

            completedItem = QTableWidgetItem()
            completedItem.setData( Qt.EditRole, todo.completed )                    ## handles int type properly
            completedItem.setTextAlignment( Qt.AlignHCenter | Qt.AlignVCenter )
            completedItem.setForeground( fgColor )
            self.setItem( i, 2, completedItem )

        self.setSortingEnabled( True )

        # printTree( self )

    def contextMenuEvent( self, event ):
        evPos     = event.pos()
        globalPos = self.viewport().mapToGlobal( evPos )

        todo: ToDo = None
        item = self.itemAt( evPos )
        if item is not None:
            rowIndex = self.row( item )
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

    def todoSelectionChanged(self):
        todoIndex = self.currentRow()
        todo = self.getToDo( todoIndex )
        self.emitSelectedToDo( todo )

    def todoClicked(self, item):
        todoIndex = self.row( item )
        todo = self.getToDo( todoIndex )
        self.emitSelectedToDo( todo )

    def todoDoubleClicked(self, item):
        rowIndex = self.row( item )
        todo = self.getToDo( rowIndex )
        self.editToDo.emit( todo )

    def emitSelectedToDo( self, todo=None ):
        if todo is not None:
            self.selectedToDo.emit( todo )
        else:
            self.todoUnselected.emit()

    def dropEvent(self, event):
        if event.source() != self:
            ## do not allow dropping from other elements
            return
        ## internal drag & drop
        sourceRows = set([mi.row() for mi in self.selectedIndexes()])
        targetRow = self.indexAt(event.pos()).row()
        sourceRows.discard(targetRow)
        if len(sourceRows) != 1:
            return
        sourceRow = sourceRows.pop()
        sourceToDo = self.getToDo( sourceRow )
        targetToDo = self.getToDo( targetRow )
        #print( "drop event:", sourceRow, targetRow, sourceToDo.title, targetToDo.title )

        manager: Manager = self.data.getManager()
        if targetToDo is None:
            manager.setToDoPriorityLeast( sourceToDo )
            self.data.todoChanged.emit( sourceToDo )
            self.updateView()
            return
        sourcePriority = sourceToDo.priority
        targetPriority = targetToDo.priority
        if targetPriority == sourcePriority:
            ## no priority to change
            return
        if targetPriority > sourcePriority:
            newPriority = targetPriority + 1
            manager.setToDoPriorityRaise( sourceToDo, newPriority )
        else:
            newPriority = targetPriority - 1
            manager.setToDoPriorityDecline( sourceToDo, newPriority )
        self.data.todoChanged.emit( sourceToDo )
        self.updateView()


def get_todo_fgcolor( todo: ToDo ) -> QBrush:
    if todo.isCompleted():
        ## completed -- green
        return QBrush( get_completed_color() )
    ## normal
    return QBrush( QColor(0, 0, 0) )
