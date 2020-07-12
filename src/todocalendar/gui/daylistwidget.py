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
from PyQt5.QtCore import QSize
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QWidget, QLabel
from PyQt5.QtWidgets import QHBoxLayout, QLayout
from PyQt5.QtGui import QPainter, QPainterPath, QPen, QColor

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


class DayItem( DrawWidget ):

    def __init__(self, task: Task, day: date, parentWidget=None):
        super().__init__( parentWidget )

        self.day  = day
        self.task = task

#         self.setStyleSheet( "background-color: red" )

    def recalculatePosition( self, xOffset, allowedWidth, allowedHeight ):
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
#         painter.fillPath( path, bgColor )
        painter.fillPath( path, QColor(0, 255, 0) )

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


class DayListContentWidget( QWidget ):

    def __init__(self, parentWidget=None):
        super().__init__( parentWidget )

        self.items = []

#         self.setStyleSheet( "background-color: green" )
#         self.setStyleSheet( "border: 1px solid black" )

#         hlayout = QHBoxLayout()
#         hlayout.setContentsMargins( 0, 0, 0, 0 )
#         hlayout.setAlignment( Qt.AlignTop )
#
#         self.setLayout( hlayout )

    def clear(self):
        for w in self.items:
            w.deleteLater()
        self.items.clear()

    def setTasks(self, tasksList, day: date ):
        self.clear()
        for task in tasksList:
            item = DayItem(task, day, self)
            self.items.append( item )
            item.show()
        self.repaintChildren()

    def resizeEvent(self, event):
        super().resizeEvent( event )
        self.repaintChildren()

    def repaintChildren(self):
        sItems = len(self.items)
        if sItems < 1:
            return
        itemWidth  = max( 0, int( (self.width() - 16) / sItems) )
        itemHeight = self.height()
        for i in range(0, sItems):
            widget = self.items[i]
            widget.setFixedWidth( itemWidth )
            xPos = itemWidth * i + 8
            widget.recalculatePosition( xPos, itemWidth, itemHeight )

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


class DayListWidget( QWidget ):

    def __init__(self, parentWidget=None):
        super().__init__( parentWidget )

#         self.setStyleSheet( "background-color: green" )

        hlayout = QHBoxLayout()
        hlayout.setContentsMargins( 0, 0, 0, 0 )
        hlayout.setSpacing( 0 )
        self.setLayout( hlayout )

        self.timeline = DayTimeline( self )
        hlayout.addWidget( self.timeline )

        self.content = DayListContentWidget( self )
        hlayout.addWidget( self.content )

    def setTasks(self, tasksList, day: date ):
        self.content.setTasks( tasksList, day )
