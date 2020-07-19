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

import datetime
from typing import List, Tuple
from dateutil.relativedelta import relativedelta

from PyQt5.QtWidgets import QCalendarWidget

from PyQt5.QtCore import Qt, QDate, pyqtSignal
from PyQt5.QtGui import QColor, QPalette, QPainterPath, QPen, QCursor
from PyQt5.QtWidgets import QTableView, QHeaderView

from hanlendar.gui.taskcontextmenu import TaskContextMenu

from hanlendar.domainmodel.task import Task, TaskOccurrence


class MonthCalendar( QCalendarWidget ):

    headerRowHeight = 12
    cellItemHeight  = 20

    selectedTask    = pyqtSignal( Task )
    taskUnselected  = pyqtSignal()
    editTask        = pyqtSignal( Task )

    def __init__( self, parent=None ):
        super().__init__( parent )

        self.data = None
        self.dateToCellRect = {}
        self.currentTaskIndex = -1

        self.showCompleted = False

        self.setGridVisible( True )
        self.setNavigationBarVisible( False )
        self.setVerticalHeaderFormat( QCalendarWidget.NoVerticalHeader )

        todayDate = datetime.date.today()
        self.setCurrentPage( todayDate.year, todayDate.month )

        self.taskColor = QColor( self.palette().color( QPalette.Highlight) )
        self.taskColor.setAlpha( 64 )

        self.cellsTable = self.findChild( QTableView )

        ## set first row of fixed size
        header = self.cellsTable.verticalHeader()
        header.setSectionResizeMode( 0, QHeaderView.Fixed )
        self.cellsTable.setRowHeight( 1, self.headerRowHeight )

        self.taskContextMenu = TaskContextMenu( self )

        self.selectionChanged.connect( self.updateCells )
        self.clicked.connect( self.dateClicked )
        self.activated.connect( self.dateDoubleClicked )

    def connectData(self, dataObject):
        self.data = dataObject
        self.taskContextMenu.connectData( dataObject )
        self.editTask.connect( dataObject.editTask )

    def showCompletedTasks(self, show=True):
        self.showCompleted = show
        self.updateCells()

    def setCurrentPage(self, year, month):
        self.dateToCellRect.clear()
        minDate = datetime.date( year=year, month=month, day=1 )
        maxDate = minDate + relativedelta( months=1 ) - relativedelta( days=1 )
        self.setMinimumDate( minDate )
        self.setMaximumDate( maxDate )
        super().setCurrentPage( year, month )

    def getTasks(self, date: QDate) -> List[TaskOccurrence]:
        pyDate = date.toPyDate()
        tasksList = self.data.getTaskOccurrences( pyDate, self.showCompleted )
        tasksList.sort( key=TaskOccurrence.sortByDates )
        return tasksList

    def getTask(self, taskIndex) -> Task:
        if taskIndex < 0:
            return None
        date = self.selectedDate()
        tasksList = self.getTasks(date)
        if taskIndex >= len(tasksList):
            return None
        taskOccurrence = tasksList[ taskIndex ]
        return taskOccurrence.task

    def paintCell(self, painter, rect, date: QDate):
        self.dateToCellRect[date] = rect

        painter.save()

        ## header
        painter.fillRect( rect.x(), rect.y(), rect.width(), 16, QColor("lightGray") )
        weekDay = date.dayOfWeek()
        if weekDay == 6 or weekDay == 7:
            pen = painter.pen()
            pen.setColor( QColor("red") )
            painter.setPen(pen)
            painter.drawText( rect, Qt.TextSingleLine | Qt.AlignTop | Qt.AlignRight, str( date.day() ) )
        else:
            painter.drawText( rect, Qt.TextSingleLine | Qt.AlignTop | Qt.AlignRight, str( date.day() ) )

        if self.data is not None:
            selectedDay = self.selectedDate() == date
            tasksList = self.getTasks( date )
            entriesSize = len(tasksList)
            itemsCapacity = int( rect.height() / self.cellItemHeight )
            entriesSize = min( entriesSize, itemsCapacity )
            for index in range(0, entriesSize):
                item: TaskOccurrence = tasksList[index]
                selectedTask = selectedDay and (self.currentTaskIndex == index)
                bgColor = get_task_bgcolor( item, selectedTask )
                self.drawItem( painter, rect, index, item.title, bgColor )

        painter.restore()

    def drawItem(self, painter, rect, itemIndex, text, bgColor):
        itemOffset = self.cellItemHeight * ( itemIndex + 1 )
        path = QPainterPath()
        path.addRoundedRect( rect.x() + 2, rect.y() + itemOffset, rect.width() - 4, 16, 5, 5 )
        painter.fillPath( path, bgColor )
#         painter.fillPath( path, QColor(0, 255, 0) )

        pathPen = QPen( QColor("black") )
        pathPen.setWidth( 2 )
        painter.strokePath( path, pathPen )

        pen = painter.pen()
        pen.setColor( QColor("black") )
        painter.setPen(pen)
        painter.drawText( rect.x() + 6, rect.y() + itemOffset, rect.width() - 12, 16,
                          Qt.TextSingleLine | Qt.AlignTop | Qt.AlignLeft,
                          text )

#     def dateFromCell( self, cellIndex ):
#         dayIndex = (cellIndex.row() - 1) * 7 + (cellIndex.column())
#         return self.dateAt( dayIndex )
#
#     def dateAt( self, dayIndex ):
#         prevMonthDays = self.daysFromPreviousMonth()
#         dayOffset = dayIndex - prevMonthDays
#         currYear  = self.yearShown()
#         currMonth = self.monthShown()
#         currDate  = QDate( currYear, currMonth, 1 )
#         return currDate.addDays( dayOffset )
#
#     def daysFromPreviousMonth( self ):
#         currYear     = self.yearShown()
#         currMonth    = self.monthShown()
#         firstOfMonth = datetime.date( currYear, currMonth, 1 )
#         days = firstOfMonth.weekday()
#         if days == 0:                       # 0 means Monday
#             days += 7                       # there is always one row
#         return days

    def contextMenuEvent( self, _ ):
        globalPos = QCursor.pos()
        pos = self.mapFromGlobal( globalPos )
        contextDate = self.findDateByPos( pos )
        if contextDate is None:
            return
        if contextDate < self.minimumDate():
            return
        if contextDate > self.maximumDate():
            return
        self.setSelectedDate( contextDate )
        taskIndex = self.clickedTaskIndex( contextDate )
        self.currentTaskIndex = taskIndex[0]
        task: Task = taskIndex[1]
        if task is not None:
            self.taskContextMenu.show( task )
        else:
            self.taskContextMenu.showNewTask( contextDate )

    def dateClicked(self, date):
        taskIndex = self.clickedTaskIndex( date )
        self.currentTaskIndex = taskIndex[0]
        task = taskIndex[1]
        self.emitSelectedTask( task )
        self.updateCell( date )

    def dateDoubleClicked(self, date):
        taskIndex = self.clickedTaskIndex( date )
        task = taskIndex[1]
        if task is None:
            return
        self.editTask.emit( task )

    def clickedTaskIndex(self, date) -> Tuple[int, Task]:
        tasksList = self.getTasks(date)
        if len(tasksList) < 1:
            return ( -1, None )
        rowIndex = self.clickedItemRow( date )
        taskIndex = rowIndex - 1
        if taskIndex < 0:
            return ( -1, None )
        if taskIndex >= len(tasksList):
            return ( -1, None )
        taskOccurrence = tasksList[taskIndex]
        return ( taskIndex, taskOccurrence.task )

    def clickedItemRow(self, date):
        globalPos = QCursor.pos()
        pos = self.mapFromGlobal( globalPos )
        cellRect = self.dateToCellRect[date]
        cellRel  = pos - cellRect.topLeft()
        rowIndex = int( cellRel.y() / self.cellItemHeight )
        return rowIndex

    def findDateByPos( self, relativePos ):
        for date, rect in self.dateToCellRect.items():
            if rect.contains( relativePos ):
                return date
        return None

    def emitSelectedTask( self, task=None ):
        if task is not None:
            self.selectedTask.emit( task )
        else:
            self.taskUnselected.emit()


def get_task_bgcolor( task: TaskOccurrence, isSelected=False ) -> QColor:
    bgColor = get_task_base_bgcolor( task )
    if isSelected:
        red   = min( 255, bgColor.red()   + 40 )
        green = min( 255, bgColor.green() + 40 )
        blue  = min( 255, bgColor.blue()  + 40 )
        bgColor = QColor( red, green, blue, bgColor.alpha() )
    return bgColor


def get_task_base_bgcolor( task: TaskOccurrence ) -> QColor:
    if task.isCompleted():
        ## completed -- gray
        return QColor( 160, 160, 160 )
    if task.isTimedout():
        ## timed out -- red
        return QColor(220, 0, 0)
    if task.isReminded():
        ## already reminded -- orange
        return QColor(220, 135, 0)    ## orange
#     taskFirstDate = task.getFirstDateTime()
#     if taskFirstDate is not None:
#         diff = taskFirstDate - datetime.datetime.today()
#         if diff > datetime.timedelta( days=90 ):
#             ## far task -- light gray
#             return QColor( 160, 160, 160 )
    ## normal
    return QColor(0, 220, 0)
