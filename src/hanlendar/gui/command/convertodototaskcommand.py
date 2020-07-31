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

from hanlendar.gui.command.addtaskcommand import AddTaskCommand
from hanlendar.gui.command.removetodocommand import RemoveToDoCommand


_LOGGER = logging.getLogger(__name__)


class ConvertToDoToTaskCommand( QUndoCommand ):

    def __init__(self, dataObject, currentTodo, newTask, parentCommand=None):
        super().__init__(parentCommand)

        AddTaskCommand( dataObject, newTask, self )
        RemoveToDoCommand( dataObject, currentTodo, self )

        self.setText( "Convert ToDo to Task" )

    def redo(self):
        super().redo()

    def undo(self):
        super().undo()
