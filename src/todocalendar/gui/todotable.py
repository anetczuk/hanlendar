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

from todocalendar.domainmodel.todo import ToDo


# _LOGGER = logging.getLogger(__name__)


class ToDoTable( QTableWidget ):

    selectedToDo        = pyqtSignal( int )
    addNewToDo          = pyqtSignal()
    editToDo            = pyqtSignal( ToDo )
    removeToDo          = pyqtSignal( ToDo )
    convertToDoToTask   = pyqtSignal( ToDo )
    markCompleted       = pyqtSignal( ToDo )

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)

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

    def clear(self):
        self.setRowCount( 0 )
        self.selectedToDo.emit( -1 )

    def showCompletedToDos(self, show):
        self.showCompleted = show

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

            titleItem = QTableWidgetItem( todo.title )
            titleItem.setData( Qt.UserRole, todo )
            self.setItem( i, 0, titleItem )

            priorityItem = QTableWidgetItem( str(todo.priority) )
            priorityItem.setTextAlignment( Qt.AlignHCenter | Qt.AlignVCenter )
            self.setItem( i, 1, priorityItem )

            completedItem = QTableWidgetItem( str(todo.completed) )
            completedItem.setTextAlignment( Qt.AlignHCenter | Qt.AlignVCenter )
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
        rowIndex = self.currentRow()
        self.selectedToDo.emit( rowIndex )

    def todoClicked(self, item):
        rowIndex = self.row( item )
        self.selectedToDo.emit( rowIndex )

    def todoDoubleClicked(self, item):
        rowIndex = self.row( item )
        todo = self.getToDo( rowIndex )
        self.editToDo.emit( todo )
