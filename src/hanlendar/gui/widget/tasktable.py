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

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import Qt, QModelIndex
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QAbstractItemView, QHeaderView
from PyQt5.QtGui import QColor, QBrush

from hanlendar.gui.customtreemodel import ItemTreeModel
from hanlendar.gui.taskcontextmenu import TaskContextMenu

from hanlendar.domainmodel.task import Task, TaskOccurrence


_LOGGER = logging.getLogger(__name__)


class TaskTreeModel( ItemTreeModel ):

    attrList = [ "title", "priority", "completed", "start", "due" ]

    def __init__(self, parent, *args):
        super().__init__(parent, *args)
        self.dataObject = None

    def setDataObject(self, dataObject):
        self.beginResetModel()
        self.dataObject = dataObject
        self.endResetModel()

    def data(self, index: QModelIndex, role):
        if role == QtCore.Qt.SizeHintRole:
            return QtCore.QSize(10, 30)

        task = self.getItem( index )
        if task is None:
            return None
        item: TaskOccurrence = task.currentOccurrence()
        if item is None:
            return None

        if role == Qt.UserRole:
            return task

        if role == Qt.TextAlignmentRole:
            attrIndex = index.column()
            if attrIndex > 0:
                return Qt.AlignHCenter | Qt.AlignVCenter

        if role == Qt.ForegroundRole:
            return get_task_fgcolor( item )

        if role == Qt.BackgroundRole:
            nowDate = date.today()
            if item.isInMonth( nowDate ):
                return QColor( "beige" )
            if item.isInPastMonths( nowDate ):
                return QColor( "moccasin" )

        if role == QtCore.Qt.DisplayRole:
            attrIndex = index.column()
            if attrIndex == 0:
                return item.title
            elif attrIndex == 1:
                return item.priority
            elif attrIndex == 2:
                return item.completed
            elif attrIndex == 3:
                dateString = "---"
                if item.startCurrent is not None:
                    dateString = item.startCurrent.strftime( "%Y-%m-%d %H:%M" )
                return dateString
            elif attrIndex == 4:
                dateString = "---"
                if item.dueCurrent is not None:
                    dateString = item.dueCurrent.strftime( "%Y-%m-%d %H:%M" )
                return dateString

        return None

    def headerLabels(self):
        return [ "Summary", "Priority", "Complete", "Start Date", "Due Date" ]

    def internalMoveMimeType(self):
        return "TasksTreeNode"

    ## overrided
    def moveItem(self, itemId, targetItem, targetIndex):
        if self.dataObject is None:
            return
        self.dataObject.moveTask( itemId, targetItem, targetIndex )

    def getRootList(self):
        if self.dataObject is None:
            return None
        manager = self.dataObject.getManager()
        return manager.getTasks()

#     def setRootList(self, newList):
#         if self.dataObject is None:
#             return
#         self.dataObject.setTasksList( newList )


## ===========================================================


class TaskSortFilterProxyModel( QtCore.QSortFilterProxyModel ):

    def __init__(self, parentObject=None):
        super().__init__(parentObject)
        self._showCompleted = False

    def showCompleted(self, show=True):
        self._showCompleted = show
        self.invalidateFilter()

    def filterAcceptsRow(self, sourceRow, sourceParent: QModelIndex):
        if self._showCompleted is True:
            return True
        dataIndex = self.sourceModel().index( sourceRow, 2, sourceParent )
        item = dataIndex.internalPointer()
        return item.isCompleted() is False

    def lessThan(self, left: QModelIndex, right: QModelIndex):
        leftData  = self.sourceModel().data(left, QtCore.Qt.DisplayRole)
        rightData = self.sourceModel().data(right, QtCore.Qt.DisplayRole)
        return leftData < rightData


## ===========================================================


class TaskTable( QtWidgets.QTreeView ):

    selectedTask    = pyqtSignal( Task )
    taskUnselected  = pyqtSignal()
    editTask        = pyqtSignal( Task )

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)

        self.data = None
        self.expandItems = False

        self.setSelectionBehavior( QAbstractItemView.SelectRows )
        self.setSelectionMode( QAbstractItemView.SingleSelection )
        self.setEditTriggers( QAbstractItemView.NoEditTriggers )
#         self.setAlternatingRowColors( True )
        self.setSortingEnabled( True )

#         self.setAlternatingRowColors( True )
#         self.setStyleSheet("""
#         QTableView::item:alternate {
#             background-color: #bfffbf;
#         }
#         QTableView::item {
#             background-color: #deffde;
#         }
#         """);

        self.setDragEnabled( True )
        self.setDropIndicatorShown( True )
        self.setDragDropMode( QAbstractItemView.InternalMove )
        self.setDragDropOverwriteMode(False)

        self.itemsModel = TaskTreeModel(self)
        self.proxyModel = TaskSortFilterProxyModel(self)
        self.proxyModel.setSourceModel( self.itemsModel )
        self.setModel( self.proxyModel )

        header = self.header()
        header.setDefaultAlignment( Qt.AlignCenter )
        header.setHighlightSections( False )
        header.setStretchLastSection( False )
        header.setSectionResizeMode( 0, QHeaderView.Stretch )

        self.taskContextMenu = TaskContextMenu( self )

        self.proxyModel.modelReset.connect( self.expandOnDemand )
        self.doubleClicked.connect( self.itemDoubleClicked )

    def connectData(self, dataObject):
        self.data = dataObject
        self.itemsModel.setDataObject( self.data )
        self.taskContextMenu.connectData( dataObject )
        self.editTask.connect( dataObject.editTask )

    def clear(self):
        self.setRowCount( 0 )
        self.emitSelectedTask()

    def showCompletedItems(self, show):
        self.proxyModel.showCompleted( show )
        self.updateView()

    def expandAllItems(self, expand):
        self.expandItems = expand
        self.expandOnDemand()

    def updateView(self, updatedTask: Task = None):
        if updatedTask is not None:
            taskIndex = self.getIndex( updatedTask )
            if taskIndex is not None:
                self.proxyModel.dataChanged.emit( taskIndex, taskIndex )
                return
        self.itemsModel.setDataObject( self.data )
        self.expandOnDemand()

    def getIndex(self, task: Task):
        modelIndex = self.itemsModel.getIndex( task )
        if modelIndex is None:
            return None
        proxyIndex = self.proxyModel.mapFromSource( modelIndex )
        return proxyIndex

    def getTask(self, itemIndex: QModelIndex ) -> TaskOccurrence:
        sourceIndex = self.proxyModel.mapToSource( itemIndex )
        return self.itemsModel.getItem( sourceIndex )

    def contextMenuEvent( self, event ):
        evPos      = event.pos()
        task: Task = None
        mIndex = self.indexAt( evPos )
        if mIndex is not None:
            task = self.getTask( mIndex )
        self.taskContextMenu.show( task )

    def selectionChanged(self, toSelection, fromSelection):
        super().selectionChanged( toSelection, fromSelection )
        modelIndex = self.currentIndex()
        item = self.getTask( modelIndex )
        if item is not None:
            self.selectedTask.emit( item )
        else:
            self.taskUnselected.emit()

    def itemDoubleClicked(self, modelIndex):
        item = self.getTask( modelIndex )
        self.taskContextMenu.editTask.emit( item )

    def mousePressEvent(self, event):
        pos = event.pos()
        itemIndex = self.indexAt(pos)
        if itemIndex.isValid() is False:
            self.setCurrentIndex(itemIndex)
            self.clearSelection()
        super().mousePressEvent( event )

    def expandOnDemand(self):
        if self.expandItems:
            self.expandAll()

    def drawBranches(self, painter, rect, index):
        bgcolor = index.data( Qt.BackgroundRole )
        if bgcolor is not None:
            painter.fillRect(rect, bgcolor)
        super().drawBranches(painter, rect, index)


def get_task_fgcolor( task: TaskOccurrence ) -> QBrush:
    if task.isCompleted():
        ## completed -- green
        return QBrush( get_completed_color() )
    if task.isTimedout():
        ## timed out
        return QBrush( get_timeout_color() )
    if task.isReminded():
        ## already reminded
        return QBrush( get_reminded_color() )
    taskFirstDate = task.getFirstDateTime()
    if taskFirstDate is not None:
        diff = taskFirstDate - datetime.today()
        if diff > timedelta( days=90 ):
            ## far task -- light gray
            return QBrush( QColor( 180, 180, 180 ) )
    ## normal
    return QBrush( QColor(0, 0, 0) )


def get_completed_color() -> QColor:
    return QColor(0, 160, 0)        ## green


def get_timeout_color() -> QColor:
    return QColor(255, 0, 0)        ## red


def get_reminded_color() -> QColor:
    return QColor(200, 0, 200)      ## magenta
