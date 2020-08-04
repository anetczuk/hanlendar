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

from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QWidget, QSplitter, QCheckBox, QTabWidget, QTableWidget, QTreeView


def load_state(window: QMainWindow, settings: QSettings):
    settings.beginGroup( window.objectName() )
    geometry = settings.value("geometry")
    state = settings.value("windowState")
    if geometry is not None:
        window.restoreGeometry( geometry )
    if state is not None:
        window.restoreState( state )
    settings.endGroup()

    ## store geometry of all widgets
    widgets = window.findChildren(QWidget)
    for w in widgets:
        wKey = get_widget_key(w)
        settings.beginGroup( wKey )
        geometry = settings.value("geometry")
        if geometry is not None:
            w.restoreGeometry( geometry )
        settings.endGroup()

    widgets = window.findChildren(QSplitter)
    for w in widgets:
        wKey = get_widget_key(w)
        settings.beginGroup( wKey )
        state = settings.value("widgetState")
        if state is not None:
            w.restoreState( state )
        settings.endGroup()

    widgets = window.findChildren(QCheckBox)
    for w in widgets:
        wKey = get_widget_key(w)
        settings.beginGroup( wKey )
        state = settings.value("checkState")
        if state is not None:
            w.setCheckState( int(state) )
        settings.endGroup()

    widgets = window.findChildren(QTabWidget)
    for w in widgets:
        wKey = get_widget_key(w)
        settings.beginGroup( wKey )
        state = settings.value("currentIndex")
        if state is not None:
            currIndex = int(state)
            w.setCurrentIndex( currIndex )
        settings.endGroup()

    widgets = window.findChildren( QTableWidget )
    for w in widgets:
        wKey = get_widget_key(w)
        settings.beginGroup( wKey )
        colsNum = w.columnCount()
        for c in range(0, colsNum):
            state = settings.value( "column" + str(c) )
            if state is not None:
                currWidth = int(state)
                w.setColumnWidth( c, currWidth )
        sortColumn = settings.value( "sortColumn" )
        sortOrder = settings.value( "sortOrder" )
        if sortColumn is not None and sortOrder is not None:
            w.sortByColumn( int(sortColumn), int(sortOrder) )
        settings.endGroup()

    widgets = window.findChildren( QTreeView )
    for w in widgets:
        wKey = get_widget_key(w)
        settings.beginGroup( wKey )
        colsNum = w.header().count()
        for c in range(0, colsNum):
            state = settings.value( "column" + str(c) )
            if state is not None:
                currWidth = int(state)
                w.setColumnWidth( c, currWidth )
        sortColumn = settings.value( "sortColumn" )
        sortOrder = settings.value( "sortOrder" )
        if sortColumn is not None and sortOrder is not None:
            w.sortByColumn( int(sortColumn), int(sortOrder) )
        settings.endGroup()


def save_state(window: QMainWindow, settings: QSettings):
    settings.beginGroup( window.objectName() )
    settings.setValue("geometry", window.saveGeometry() )
    settings.setValue("windowState", window.saveState() )
    settings.endGroup()

    ## store geometry of all widgets
    widgets = window.findChildren( QWidget )
    for w in widgets:
        wKey = get_widget_key(w)
        settings.beginGroup( wKey )
        settings.setValue("geometry", w.saveGeometry() )
        settings.endGroup()

    widgets = window.findChildren( QSplitter )
    for w in widgets:
        wKey = get_widget_key(w)
        settings.beginGroup( wKey )
        settings.setValue("widgetState", w.saveState() )
        settings.endGroup()

    widgets = window.findChildren( QCheckBox )
    for w in widgets:
        wKey = get_widget_key(w)
        settings.beginGroup( wKey )
        settings.setValue("checkState", w.checkState() )
        settings.endGroup()

    widgets = window.findChildren( QTabWidget )
    for w in widgets:
        wKey = get_widget_key(w)
        settings.beginGroup( wKey )
        settings.setValue("currentIndex", w.currentIndex() )
        settings.endGroup()

    widgets = window.findChildren( QTableWidget )
    for w in widgets:
        wKey = get_widget_key(w)
        colsNum = w.columnCount()
        settings.beginGroup( wKey )
        for c in range(0, colsNum):
            settings.setValue( "column" + str(c), w.columnWidth(c) )
        header = w.horizontalHeader()
        sortColumn = header.sortIndicatorSection()
        settings.setValue( "sortColumn", sortColumn )
        sortOrder = header.sortIndicatorOrder()
        settings.setValue( "sortOrder", sortOrder )
        settings.endGroup()

    widgets = window.findChildren( QTreeView )
    for w in widgets:
        wKey = get_widget_key(w)
        header = w.header()
        colsNum = header.count()
        settings.beginGroup( wKey )
        for c in range(0, colsNum):
            settings.setValue( "column" + str(c), w.columnWidth(c) )
        sortColumn = header.sortIndicatorSection()
        settings.setValue( "sortColumn", sortColumn )
        sortOrder = header.sortIndicatorOrder()
        settings.setValue( "sortOrder", sortOrder )
        settings.endGroup()


def get_widget_key(widget):
    if widget is None:
        return None
    retKey = widget.objectName()
    widget = widget.parent()
    while widget is not None:
        retKey = widget.objectName() + "-" + retKey
        widget = widget.parent()
    return retKey
