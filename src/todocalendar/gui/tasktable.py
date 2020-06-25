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

from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QAbstractItemView, QHeaderView
from PyQt5.QtWidgets import QMenu
from PyQt5.QtCore import Qt, QItemSelectionModel
from PyQt5.QtCore import pyqtSignal

from todocalendar.domainmodel.task import Task


_LOGGER = logging.getLogger(__name__)


class TaskTable( QTableWidget ):

    selectedTask = pyqtSignal( int )
    addNewTask   = pyqtSignal()
    editTask     = pyqtSignal( Task )
    removeTask   = pyqtSignal( Task )

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)

        self.setSelectionBehavior( QAbstractItemView.SelectRows )
        self.setSelectionMode( QAbstractItemView.SingleSelection )
        self.setEditTriggers( QAbstractItemView.NoEditTriggers )
        self.setAlternatingRowColors( True )
        self.setShowGrid( False )

        headerLabels = [ "Summary", "Priority", "Complete", "Start Date", "Due Date" ]
        self.setColumnCount( len(headerLabels) )
        self.setHorizontalHeaderLabels( headerLabels )

        header = self.horizontalHeader()
        header.setHighlightSections( False )
        header.setSectionResizeMode( 0, QHeaderView.Stretch )

        self.itemSelectionChanged.connect( self.taskSelectionChanged )

        self.setTasks( [] )

    def clear(self):
        self.setRowCount( 0 )
        self.selectedTask.emit( -1 )

    def getTask(self, taskIndex):
        if taskIndex < 0:
            return None
        if taskIndex >= self.rowCount():
            return None
        tableItem = self.item( taskIndex, 0 )
        userData = tableItem.data( Qt.UserRole )
        return userData

    def setTasks( self, tasksList ):
        self.clear()
        
        self.setSortingEnabled( False )     ## workaround to fix disappearing cells content

        tasksSize = len( tasksList )
        self.setRowCount( tasksSize )

        for i in range(0, tasksSize):
            task: Task = tasksList[i]

            titleItem = QTableWidgetItem( task.title )
            titleItem.setData( Qt.UserRole, task )
            self.setItem( i, 0, titleItem )

            priorityItem = QTableWidgetItem( str(task.priority) )
            priorityItem.setTextAlignment( Qt.AlignHCenter | Qt.AlignVCenter )
            self.setItem( i, 1, priorityItem )

            completedItem = QTableWidgetItem( str(task.completed) )
            completedItem.setTextAlignment( Qt.AlignHCenter | Qt.AlignVCenter )
            self.setItem( i, 2, completedItem )

            startDate = task.startDate.date()
            startItem = QTableWidgetItem( str(startDate) )
            startItem.setTextAlignment( Qt.AlignHCenter | Qt.AlignVCenter )
            self.setItem( i, 3, startItem )

            dueDate = task.dueDate.date()
            dueItem = QTableWidgetItem( str(dueDate) )
            dueItem.setTextAlignment( Qt.AlignHCenter | Qt.AlignVCenter )
            self.setItem( i, 4, dueItem )

        self.setSortingEnabled( True )

    def taskSelectionChanged(self):
        taskIndex = self.currentRow()
        self.selectedTask.emit( taskIndex )

    def contextMenuEvent( self, event ):
        evPos     = event.pos()
        globalPos = self.viewport().mapToGlobal( evPos )

        task: Task = None
        item = self.itemAt( evPos )
        if item is not None:
            rowIndex = self.row( item )
            task = self.getTask( rowIndex )

        contextMenu = QMenu(self)
        addTaskAction = contextMenu.addAction("New Task")
        editTaskAction = contextMenu.addAction("Edit Task")
        removeTaskAction = contextMenu.addAction("Remove Task")

        if task is None:
            ## context menu on background
            editTaskAction.setEnabled( False )
            removeTaskAction.setEnabled( False )

        action = contextMenu.exec_( globalPos )

        if action == addTaskAction:
            self.addNewTask.emit()
        elif action == editTaskAction:
            self.editTask.emit( task )
        elif action == removeTaskAction:
            self.removeTask.emit( task )
