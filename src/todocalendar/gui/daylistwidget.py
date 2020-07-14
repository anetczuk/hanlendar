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
from datetime import date

# from . import uiloader

from PyQt5.QtCore import Qt
from PyQt5.QtCore import QSize, QRect, QDate
from PyQt5.QtCore import pyqtSignal
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QWidget, QLabel
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QMenu
from PyQt5.QtGui import QPainter, QPainterPath, QPen, QColor, QPalette

from todocalendar.gui.taskcontextmenu import TaskContextMenu
from todocalendar.gui.monthcalendar import getTaskBackgroundColor

from todocalendar.domainmodel.task import Task


# UiTargetClass, QtBaseClass = uiloader.loadUiFromClassName( __file__ )


_LOGGER = logging.getLogger(__name__)


class DrawWidget( QWidget ):
    def __init__(self, parentWidget=None):
        super().__init__( parentWidget )

        ## it seems to be redundant, but widget won't respect forcing sizing
        ## if it does not have layout and any child content
        hlayout = QHBoxLayout()
        hlayout.setContentsMargins( 0, 0, 0, 0 )
        self.setLayout( hlayout )
        hlayout.addWidget( QWidget(self) )


class DayTimeline( DrawWidget ):

    itemClicked = pyqtSignal()

    def __init__(self, parentWidget=None):
        super().__init__( parentWidget )
        self.setFixedWidth( 30 )

    def paintEvent(self, event):
        super().paintEvent( event )

        painter = QPainter(self)

        width  = self.width()
        height = self.height()

        bgColor = self.palette().color( self.backgroundRole() )
        painter.fillRect( 0, 0, width, height, bgColor )

        hourStep = height / 24

        pen = painter.pen()
        pen.setColor( QColor("black") )
        painter.setPen(pen)
        painter.drawText( 0, 0, width - 6, hourStep, Qt.TextSingleLine | Qt.AlignTop | Qt.AlignRight, "0" )

        for h in range(1, 24):
            hourHeight = hourStep * h
            text = str(h)

            pen = painter.pen()
            pen.setColor( QColor("gray") )
            painter.setPen(pen)
            painter.drawLine( 0, hourHeight, width, hourHeight )

            pen = painter.pen()
            pen.setColor( QColor("black") )
            painter.setPen(pen)
            painter.drawText( 0, hourHeight, width - 6, hourStep, Qt.TextSingleLine | Qt.AlignTop | Qt.AlignRight, text )

    def mousePressEvent(self, event):
        self.itemClicked.emit()


class DayItem( DrawWidget ):

    selectedItem       = pyqtSignal( DrawWidget )
    itemDoubleClicked  = pyqtSignal( DrawWidget )

    def __init__(self, task: Task, day: date, parentWidget=None):
        super().__init__( parentWidget )

        self.day  = day
        self.task = task

#         self.setStyleSheet( "background-color: red" )

    def recalculatePosition( self, lineRect: QRect ):
        allowedWidth  = lineRect.width()
        allowedHeight = lineRect.height()
        xOffset       = lineRect.x()

        daySpan = self.task.calculateTimeSpan( self.day )
        yOffset = allowedHeight * daySpan[0]
        self.move(xOffset, yOffset)

        spanDuration = daySpan[1] - daySpan[0]
        self.setFixedWidth( allowedWidth )
        self.setFixedHeight( allowedHeight * spanDuration )
        self.update()

    def paintEvent(self, event):
        super().paintEvent( event )

        painter = QPainter(self)

        width  = self.width()
        height = self.height()

        path = QPainterPath()
        path.addRoundedRect( 2, 0, width - 4, height, 5, 5 )

#         taskBgColor = monthcalendar.getTaskBackgroundColor( self.task )
        selected = self.isSelected()
        taskBgColor = getTaskBackgroundColor( self.task, selected )
        painter.fillPath( path, taskBgColor )

        pathPen = QPen( QColor("black") )
        pathPen.setWidth( 2 )
        painter.strokePath( path, pathPen )

        pen = painter.pen()
        pen.setColor( QColor("black") )
        painter.setPen(pen)
        if height < 32:
            painter.drawText( 6, 0, width - 12, height, Qt.TextSingleLine | Qt.AlignVCenter | Qt.AlignLeft, self.task.title )
        else:
            painter.drawText( 6, 0, width - 12, 32, Qt.TextSingleLine | Qt.AlignVCenter | Qt.AlignLeft, self.task.title )

    def mousePressEvent(self, event):
        self.selectedItem.emit( self )

    def mouseDoubleClickEvent(self, event):
        self.itemDoubleClicked.emit( self )

    def isSelected(self):
        return self.parent().isSelected(self)


class DayListContentWidget( QWidget ):

    selectedTask       = pyqtSignal( int )
    taskDoubleClicked  = pyqtSignal( int )

    def __init__(self, parentWidget=None):
        super().__init__( parentWidget )

        self.showCompleted = False
        self.items         = []
        self.currentIndex  = -1

    def clear(self):
        self.setCurrentIndex( -1 )
        for w in self.items:
            w.deleteLater()
        self.items.clear()

    def setCurrentIndex(self, index):
        self.currentIndex = index
        self.selectedTask.emit( index )
        self.update()

    def getCurrentTask(self):
        return self.getTask( self.currentIndex )

    def getTask(self, index):
        if index < 0:
            return None
        if index >= len(self.items):
            return None
        widget = self.items[ index ]
        return widget.task

    def setTasks(self, tasksList, day: date ):
        self.clear()
        
        if self.showCompleted is False:
            tasksList = [ task for task in tasksList if not task.isCompleted() ]
        
        for task in tasksList:
            item = DayItem(task, day, self)
            item.selectedItem.connect( self.handleItemSelect )
            item.itemDoubleClicked.connect( self.handleItemDoubleClick )
            self.items.append( item )
            item.show()
            
        self.update()

    def paintEvent(self, event):
        super().paintEvent( event )

        painter = QPainter(self)

        width  = self.width()
        height = self.height()

        pen = painter.pen()
        pen.setColor( QColor("gray") )
        painter.setPen(pen)

        hourStep = height / 24
        for h in range(1, 24):
            hourHeight = hourStep * h
            painter.drawLine( 0, hourHeight, width, hourHeight )

        self._repaintChildren( painter )

    def _repaintChildren(self, painter: QPainter):
        sItems = len(self.items)
        if sItems < 1:
            return

        if self.currentIndex >= 0:
            ## paint background
            lineRect = self._lineRect( self.currentIndex )
            bgColor = self.palette().color( QPalette.Highlight )
            painter.fillRect( lineRect, bgColor )

        for i in range(0, sItems):
            widget = self.items[i]
            lineRect = self._lineRect( i )
            widget.recalculatePosition( lineRect )

    def _lineRect(self, index) -> QRect:
        sItems = len(self.items)
        lineWidth  = max( 0, int( (self.width() - 16) / sItems) )
        lineHeight = self.height()
        xPos = lineWidth * index + 8
        return QRect( xPos, 0, lineWidth, lineHeight)

    def handleItemSelect(self, item: DayItem):
        itemIndex = self.getItemIndex( item )
        self.setCurrentIndex( itemIndex )

    def handleItemDoubleClick(self, item: DayItem):
        itemIndex = self.getItemIndex( item )
        self.taskDoubleClicked.emit( itemIndex )

    def getItemIndex(self, item: DayItem):
        try:
            return self.items.index( item )
        except ValueError:
            _LOGGER.exception("item not found")
            return -1

    def mousePressEvent(self, event):
        self.setCurrentIndex( -1 )

    def mouseDoubleClickEvent(self, event):
        self.taskDoubleClicked.emit( -1 )

    def isSelected(self, item: DayItem):
        if self.currentIndex < 0:
            return False
        itemIndex = self.getItemIndex(item)
        return itemIndex == self.currentIndex


class DayListWidget( QWidget ):

    selectedTask    = pyqtSignal( Task )
    taskUnselected  = pyqtSignal()
    editTask        = pyqtSignal( Task )

    def __init__(self, parentWidget=None):
        super().__init__( parentWidget )

#         self.setStyleSheet( "background-color: green" )

        self.data = None
        self.currentDate: QDate = QDate.currentDate()

        hlayout = QHBoxLayout()
        hlayout.setContentsMargins( 0, 0, 0, 0 )
        hlayout.setSpacing( 0 )
        self.setLayout( hlayout )

        self.timeline = DayTimeline( self )
        hlayout.addWidget( self.timeline )

        self.content = DayListContentWidget( self )
        hlayout.addWidget( self.content )

        self.taskContextMenu = TaskContextMenu( self )

        self.timeline.itemClicked.connect( self.unselectItem )
        self.content.selectedTask.connect( self.handleSelectedTask )
        self.content.taskDoubleClicked.connect( self.taskDoubleClicked )

    def connectData(self, dataObject):
        self.data = dataObject
        self.taskContextMenu.connectData( dataObject )
        self.editTask.connect( dataObject.editTask )

    def showCompletedTasks(self, show):
        self.content.showCompleted = show
        self.updateView()

    def updateView(self):
        if self.currentDate is None:
            return
        if self.data is None:
            return
        currDate = self.currentDate.toPyDate()
        tasksList = self.data.getManager().getTasksForDate( currDate )
        self.setTasks( tasksList, currDate )
        self.update()

    def setCurrentDate(self, date: QDate):
        self.currentDate = date
        self.updateView()

    def getTask(self, index):
        return self.content.getTask( index )

    def setTasks(self, tasksList, day: date ):
        self.content.setTasks( tasksList, day )

    def contextMenuEvent( self, event ):
        task: Task = self.content.getCurrentTask()
        self.taskContextMenu.show( task )

    def taskDoubleClicked(self, index):
        task = self.content.getTask( index )
        if task is None:
            return
        self.editTask.emit( task )

    def unselectItem(self):
        self.content.setCurrentIndex( -1 )

    def handleSelectedTask(self, index):
        task = self.content.getTask( index )
        self.emitSelectedTask( task )

    def emitSelectedTask( self, task=None ):
        if task is not None:
            self.selectedTask.emit( task )
        else:
            self.taskUnselected.emit()
