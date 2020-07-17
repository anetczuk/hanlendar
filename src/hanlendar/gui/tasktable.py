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

from datetime import datetime, date, timedelta

from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QAbstractItemView, QHeaderView
from PyQt5.QtCore import Qt, QItemSelectionModel
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QColor, QBrush

from hanlendar.gui.taskcontextmenu import TaskContextMenu

from hanlendar.domainmodel.task import Task


_LOGGER = logging.getLogger(__name__)


class TaskTable( QTableWidget ):

    selectedTask    = pyqtSignal( Task )
    taskUnselected  = pyqtSignal()
    editTask        = pyqtSignal( Task )

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)

        self.data = None
        self.showCompleted = False

        self.setSelectionBehavior( QAbstractItemView.SelectRows )
        self.setSelectionMode( QAbstractItemView.SingleSelection )
        self.setEditTriggers( QAbstractItemView.NoEditTriggers )

#         self.setAlternatingRowColors( True )
#         self.setStyleSheet("""
#         QTableView::item:alternate {
#             background-color: #bfffbf;
#         }
#         QTableView::item {
#             background-color: #deffde;
#         }
#         """);

        self.setShowGrid( False )

        headerLabels = [ "Summary", "Priority", "Complete", "Start Date", "Due Date" ]
        self.setColumnCount( len(headerLabels) )
        self.setHorizontalHeaderLabels( headerLabels )

        header = self.horizontalHeader()
        header.setHighlightSections( False )
        header.setSectionResizeMode( 0, QHeaderView.Stretch )

        self.taskContextMenu = TaskContextMenu( self )

        self.itemSelectionChanged.connect( self.taskSelectionChanged )
        self.itemClicked.connect( self.taskClicked )
        self.itemDoubleClicked.connect( self.taskDoubleClicked )

        self.setTasks( [] )

    def connectData(self, dataObject):
        self.data = dataObject
        self.taskContextMenu.connectData( dataObject )
        self.editTask.connect( dataObject.editTask )

    def clear(self):
        self.setRowCount( 0 )
        self.emitSelectedTask()

    def showCompletedTasks(self, show):
        self.showCompleted = show
        self.updateView()

    def updateView(self):
        tasksList = self.data.getManager().getTasks()
        self.setTasks( tasksList )

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

        if self.showCompleted is False:
            tasksList = [ task for task in tasksList if not task.isCompleted() ]

        tasksSize = len( tasksList )
        self.setRowCount( tasksSize )

        nowDate = date.today()

        for i in range(0, tasksSize):
            task: Task = tasksList[i]

            fgColor = getTaskForegroundColor( task )
            bgColor = None
            if task.hasEntryInMonth( nowDate ):
                bgColor = QColor( "beige" )
#                 bgColor = QColor( "#deffde" )
#                 bgColor = QColor( "#bfffbf" )

            titleItem = QTableWidgetItem( task.title )
            titleItem.setData( Qt.UserRole, task )
            titleItem.setForeground( fgColor )
            if bgColor is not None:
                titleItem.setBackground( bgColor )
            self.setItem( i, 0, titleItem )

            priorityItem = QTableWidgetItem( str(task.priority) )
            priorityItem.setTextAlignment( Qt.AlignHCenter | Qt.AlignVCenter )
            priorityItem.setForeground( fgColor )
            if bgColor is not None:
                priorityItem.setBackground( bgColor )
            self.setItem( i, 1, priorityItem )

            completedItem = QTableWidgetItem( str(task.completed) )
            completedItem.setTextAlignment( Qt.AlignHCenter | Qt.AlignVCenter )
            completedItem.setForeground( fgColor )
            if bgColor is not None:
                completedItem.setBackground( bgColor )
            self.setItem( i, 2, completedItem )

            startDate = "---"
            if task.startDate is not None:
                ## no start date -- deadline case
                startDate = task.startDate.strftime( "%Y-%m-%d %H:%M" )
            startItem = QTableWidgetItem( str(startDate) )
            startItem.setTextAlignment( Qt.AlignHCenter | Qt.AlignVCenter )
            startItem.setForeground( fgColor )
            if bgColor is not None:
                startItem.setBackground( bgColor )
            self.setItem( i, 3, startItem )

            dueDate = "---"
            if task.dueDate is not None:
                dueDate = task.dueDate.strftime( "%Y-%m-%d %H:%M" )
            #dueDate = task.dueDate.date()
            dueItem = QTableWidgetItem( str(dueDate) )
            dueItem.setTextAlignment( Qt.AlignHCenter | Qt.AlignVCenter )
            dueItem.setForeground( fgColor )
            if bgColor is not None:
                dueItem.setBackground( bgColor )
            self.setItem( i, 4, dueItem )

        self.setSortingEnabled( True )
        self.update()

    def contextMenuEvent( self, event ):
        evPos = event.pos()
        task: Task = None
        item = self.itemAt( evPos )
        if item is not None:
            rowIndex = self.row( item )
            task = self.getTask( rowIndex )
        self.taskContextMenu.show( task )

    def taskSelectionChanged(self):
        taskIndex = self.currentRow()
        task = self.getTask( taskIndex )
        self.emitSelectedTask( task )

    def taskClicked(self, item):
        taskIndex = self.row( item )
        task = self.getTask( taskIndex )
        self.emitSelectedTask( task )

    def taskDoubleClicked(self, item):
        rowIndex = self.row( item )
        task = self.getTask( rowIndex )
        self.editTask.emit( task )

    def emitSelectedTask( self, task=None ):
        if task is not None:
            self.selectedTask.emit( task )
        else:
            self.taskUnselected.emit()


def getTaskForegroundColor( task: Task ) -> QBrush:
    if task.isCompleted():
        ## completed -- green
        return QBrush( getCompletedColor() )
    if task.isTimedout():
        ## timed out
        return QBrush( getTimeoutColor() )
    if task.isReminded():
        ## already reminded
        return QBrush( getRemindedColor() )
    taskFirstDate = task.getFirstDateTime()
    if taskFirstDate is not None:
        diff = taskFirstDate - datetime.today()
        if diff > timedelta( days=90 ):
            ## far task -- light gray
            return QBrush( QColor( 180, 180, 180 ) )
    ## normal
    return QBrush( QColor(0, 0, 0) )


def getCompletedColor() -> QColor:
    return QColor(0, 160, 0)        ## green


def getTimeoutColor() -> QColor:
    return QColor(255, 0, 0)        ## red


def getRemindedColor() -> QColor:
    return QColor(200, 0, 200)      ## magenta
