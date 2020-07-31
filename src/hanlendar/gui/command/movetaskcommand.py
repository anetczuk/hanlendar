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

from PyQt5.QtWidgets import QUndoCommand


_LOGGER = logging.getLogger(__name__)


class MoveTaskCommand( QUndoCommand ):

    def __init__(self, dataObject, taskCoords, parentTask, targetIndex, parentCommand=None):
        super().__init__(parentCommand)

        self.data = dataObject
        self.domainModel = self.data.getManager()
        self.taskCoords = taskCoords
        self.task = self.domainModel.getTaskByCoords( taskCoords )
        self.parentTask  = parentTask
        self.targetIndex = targetIndex

        self.setText( "Move Task: " + self.task.title )

    def redo(self):
        self.domainModel.removeTask( self.task )
        self.parentTask.addSubItem( self.task, self.targetIndex )
        self.data.tasksChanged.emit()

    def undo(self):
        self.parentTask.removeSubItem( self.task )
        self.domainModel.insertTask( self.task, self.taskCoords )
        self.data.tasksChanged.emit()
