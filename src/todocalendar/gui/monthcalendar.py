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

from PyQt5.QtWidgets import QCalendarWidget

from PyQt5.QtCore import Qt, QDate, QEvent, pyqtSignal, QPoint
from PyQt5.QtGui import QColor, QPalette, QPainterPath, QPen, QCursor
from PyQt5.QtWidgets import QTableView, QHeaderView

import abc
import datetime
from dateutil.relativedelta import relativedelta

from todocalendar.gui.taskcontextmenu import TaskContextMenu

from todocalendar.domainmodel.task import Entry, Task


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
        self.taskContextMenu.connectData( dataObject )
        self.editTask.connect( dataObject.editTask )

    def setCurrentPage(self, year, month):
        self.dateToCellRect.clear()
        minDate = datetime.date( year=year, month=month, day=1 )
        maxDate = minDate + relativedelta( months=1 ) - relativedelta( days=1 )
        self.setMinimumDate( minDate )
        self.setMaximumDate( maxDate )
        super().setCurrentPage( year, month )

    def getEntries(self, date: QDate):
        pyDate = date.toPyDate()
        entries = self.data.getEntries( pyDate, False )
        entries.sort( key=Entry.sortByDates )
        return entries

    def getTask(self, taskIndex):
        if taskIndex < 0:
            return None
        date = self.selectedDate()
        entries = self.getEntries(date)
        if taskIndex >= len(entries):
            return None
        return entries[ taskIndex ].task

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
            entries = self.getEntries( date )
            entriesSize = len(entries)
            itemsCapacity = int( rect.height() / self.cellItemHeight )
            entriesSize = min( entriesSize, itemsCapacity )
            for index in range(0, entriesSize):
                item: Entry = entries[index]
                selectedTask = selectedDay and (self.currentTaskIndex == index)
                bgColor = getTaskBackgroundColor( item.task, selectedTask )
                self.drawItem( painter, rect, index, item.getTitle(), bgColor )

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
        painter.drawText( rect.x() + 6, rect.y() + itemOffset, rect.width() - 12, 16, Qt.TextSingleLine | Qt.AlignTop | Qt.AlignLeft, text )

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

    def contextMenuEvent( self, event ):
        globalPos = QCursor.pos()
        pos = self.mapFromGlobal( globalPos )
        date = self.findDateByPos( pos )
        if date is None:
            return
        self.setSelectedDate( date )
        currDate = self.selectedDate()
        if date != currDate:
            return
        taskIndex = self.clickedTaskIndex( date )
        self.currentTaskIndex = taskIndex[0]
        task: Task = taskIndex[1]
        self.taskContextMenu.show( task )

    def dateClicked(self, date):
        taskIndex = self.clickedTaskIndex( date )
        self.currentTaskIndex = taskIndex[0]
        task = taskIndex[1]
        self.emitSelectedTask( task )
        self.updateCell( date )

    def dateDoubleClicked(self, date):
        taskIndex = self.clickedTaskIndex( date )
        task = taskIndex[1]
        if task is not None:
            self.editTask.emit( task )

    def clickedTaskIndex(self, date):
        entries = self.getEntries(date)
        if len(entries) < 1:
            return ( -1, None )
        rowIndex = self.clickedItemRow( date )
        taskIndex = rowIndex - 1
        if taskIndex < 0:
            return ( -1, None )
        if taskIndex >= len(entries):
            return ( -1, None )
        return ( taskIndex, entries[taskIndex].task )

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


def getTaskBackgroundColor( task: Task, isSelected=False ) -> QColor:
    bgColor = getTaskBgColor( task )
    if isSelected:
        red   = min( 255, bgColor.red()   + 40 )
        green = min( 255, bgColor.green() + 40 )
        blue  = min( 255, bgColor.blue()  + 40 )
        bgColor = QColor( red, green, blue, bgColor.alpha() )
    return bgColor


def getTaskBgColor( task: Task ) -> QColor:
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
