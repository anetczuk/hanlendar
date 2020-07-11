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

from PyQt5.QtCore import Qt, QDate, QEvent, pyqtSignal
from PyQt5.QtGui import QColor, QPalette, QPainterPath, QPen
from PyQt5.QtWidgets import QTableView, QHeaderView
from PyQt5.QtWidgets import QMenu

import abc
import datetime
from dateutil.relativedelta import relativedelta

from todocalendar.domainmodel.task import Entry, Task


class MonthCalendar( QCalendarWidget ):

    addTask  = pyqtSignal( QDate )

    def __init__( self, parent=None ):
        super().__init__( parent )

        self.data = None

        self.setGridVisible( True )
        self.setNavigationBarVisible( False )
        self.setVerticalHeaderFormat( QCalendarWidget.NoVerticalHeader )

        todayDate = datetime.date.today()
        self.setCurrentPage( todayDate.year, todayDate.month )

        self.taskColor = QColor( self.palette().color( QPalette.Highlight) )
        self.taskColor.setAlpha( 64 )
        self.highlightModel = None
        self.selectionChanged.connect( self.updateCells )

        self.cellsTable = self.findChild( QTableView )

        ## set first row of fixed size
        header = self.cellsTable.verticalHeader()
        header.setSectionResizeMode( 0, QHeaderView.Fixed )
        self.cellsTable.setRowHeight( 1, 12 )

    def setCurrentPage(self, year, month):
        minDate = datetime.date( year=year, month=month, day=1 )
        maxDate = minDate + relativedelta( months=1 ) - relativedelta( days=1 )
        self.setMinimumDate( minDate )
        self.setMaximumDate( maxDate )
        super().setCurrentPage( year, month )

    def paintCell(self, painter, rect, date: QDate):
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
            pyDate = date.toPyDate()
            entries = self.data.getEntries( pyDate )
            entries.sort( key=Entry.sortByDates )
            entriesSize = len(entries)
            itemsCapacity = int( rect.height() / 20 )
            entriesSize = min( entriesSize, itemsCapacity )
            for index in range(0, entriesSize):
                item: Entry = entries[index]
                bgColor = getTaskBackgroundColor( item.task )
                self.drawItem( painter, rect, index, item.getTitle(), bgColor )

        painter.restore()

    def drawItem(self, painter, rect, itemIndex, text, bgColor):
        itemOffset = 20 * ( itemIndex + 1 )
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

    def dateFromCell( self, cellIndex ):
        dayIndex = (cellIndex.row() - 1) * 7 + (cellIndex.column())
        return self.dateAt( dayIndex )

    def dateAt( self, dayIndex ):
        prevMonthDays = self.daysFromPreviousMonth()
        dayOffset = dayIndex - prevMonthDays
        currYear  = self.yearShown()
        currMonth = self.monthShown()
        currDate  = QDate( currYear, currMonth, 1 )
        return currDate.addDays( dayOffset )

    def daysFromPreviousMonth( self ):
        currYear     = self.yearShown()
        currMonth    = self.monthShown()
        firstOfMonth = datetime.date( currYear, currMonth, 1 )
        days = firstOfMonth.weekday()
        if days == 0:                       # 0 means Monday
            days += 7                       # there is always one row
        return days


def getTaskBackgroundColor( task: Task ) -> QColor:
    if task.isCompleted():
        ## completed -- green
        return QColor(0, 255, 0)
    if task.isTimedout():
        ## timed out -- red
        return QColor(255, 0, 0)
    if task.isReminded():
        ## already reminded -- orange
#         return QColor("brown")
        return QColor(255, 165, 0)    ## orange
    taskFirstDate = task.getFirstDateTime()
    if taskFirstDate is not None:
        diff = taskFirstDate - datetime.datetime.today()
        if diff > datetime.timedelta( days=90 ):
            ## far task -- light gray
            return QColor( 180, 180, 180 )
    ## normal
    return QColor(0, 255, 0)
