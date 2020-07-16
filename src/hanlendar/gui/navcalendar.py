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

from PyQt5.QtCore import Qt
from PyQt5.QtCore import QDate
from PyQt5.QtGui import QColor
from PyQt5.QtGui import QPalette
from PyQt5.QtWidgets import QTableView
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QMenu

import abc
import datetime


class NavCalendarHighlightModel():
    def __init__( self ):
        pass

    @abc.abstractmethod
    def isHighlighted(self, date: QDate ):
        raise NotImplementedError('You need to define this method in derived class!')


class NavCalendar( QCalendarWidget ):

    addTask  = pyqtSignal( QDate )

    def __init__( self, *args ):
        QCalendarWidget.__init__( self, *args )

        self.cellsTable = self.findChild( QTableView )

        self.taskColor = QColor( self.palette().color( QPalette.Highlight) )
        self.taskColor.setAlpha( 64 )
        self.highlightModel = None
        self.selectionChanged.connect( self.updateCells )

    def paintCell(self, painter, rect, date):
        QCalendarWidget.paintCell(self, painter, rect, date)

        if self.isHighlighted( date ) is False:
            return

        painter.fillRect( rect, self.taskColor )

#         first_day = self.firstDayOfWeek()
#         current_date = self.selectedDate()
#         current_day = current_date.dayOfWeek()
#
#         if first_day <= current_day:
#             first_date = current_date.addDays(first_day - current_day)
#         else:
#             first_date = current_date.addDays(first_day - 7 - current_day)
#         last_date = first_date.addDays(6)
#
#         if first_date <= date <= last_date:
#             painter.fillRect( rect, self.taskColor )

    def isHighlighted(self, date):
        if self.highlightModel is None:
            return False
        return self.highlightModel.isHighlighted( date )

    def contextMenuEvent( self, event ):
        evPos     = event.pos()
        globalPos = self.mapToGlobal( evPos )
        tabPos    = self.cellsTable.mapFromGlobal( globalPos )
        cellIndex = self.cellsTable.indexAt( tabPos )
        if cellIndex.row() < 1:
            ## skip row with days of week
            return
        if cellIndex.column() < 1:
            ## skip column with number of week
            return

        contextMenu = QMenu(self)
        addTaskAction  = contextMenu.addAction("New Task")
        action = contextMenu.exec_( globalPos )

        if action == addTaskAction:
            dayIndex = (cellIndex.row() - 1) * 7 + (cellIndex.column() - 1)
            contextDate = self.dateAt( dayIndex )
            self.addTask.emit( contextDate )

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

