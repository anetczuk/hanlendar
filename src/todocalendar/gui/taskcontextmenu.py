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

from PyQt5.QtCore import QObject
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QMenu
from PyQt5.QtGui import QCursor

from todocalendar.domainmodel.task import Task
from todocalendar.gui.dataobject import DataObject


class TaskContextMenu( QObject ):

    addNewTask      = pyqtSignal()
    editTask        = pyqtSignal( Task )
    removeTask      = pyqtSignal( Task )
    markCompleted   = pyqtSignal( Task )

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)

        self.contextMenu = QMenu(parentWidget)
        self.addTaskAction       = self.contextMenu.addAction("New Task")
        self.editTaskAction      = self.contextMenu.addAction("Edit Task")
        self.removeTaskAction    = self.contextMenu.addAction("Remove Task")
        self.markCompletedAction = self.contextMenu.addAction("Mark completed")

    def connectData(self, dataObject: DataObject):
        self.addNewTask.connect( dataObject.addNewTask )
        self.editTask.connect( dataObject.editTask )
        self.removeTask.connect( dataObject.removeTask )
        self.markCompleted.connect( dataObject.markTaskCompleted )

    def show(self, task):
        if task is None:
            ## context menu on background
            self.editTaskAction.setEnabled( False )
            self.removeTaskAction.setEnabled( False )
            self.markCompletedAction.setEnabled( False )
        else:
            self.editTaskAction.setEnabled( True )
            self.removeTaskAction.setEnabled( True )
            self.markCompletedAction.setEnabled( True )
            
        globalPos = QCursor.pos()
        action = self.contextMenu.exec_( globalPos )

        if action == self.addTaskAction:
            self.addNewTask.emit()
        elif action == self.editTaskAction:
            self.editTask.emit( task )
        elif action == self.removeTaskAction:
            self.removeTask.emit( task )
        elif action == self.markCompletedAction:
            self.markCompleted.emit( task )
