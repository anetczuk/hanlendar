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

from PyQt5.QtWidgets import QMessageBox


_LOGGER = logging.getLogger(__name__)


class ImportICalendarCommand( QUndoCommand ):

    def __init__(self, dataObject, content, silent, parentCommand=None):
        super().__init__(parentCommand)

        self.data = dataObject
        self.domainModel = self.data.getManager()
        self.content  = content
        self.newTasks = []
        self.silent = silent
        self.setText("Import iCalendar")

    def redo(self):
        self.newTasks = self.domainModel.importICalendar( self.content )
        if self.newTasks is None:
            if self.silent is False:
                QMessageBox.warning( None, "Import iCalendar", "Unable to import data" )
                self.silent = True              ## do not show message on repeated redo
            return

        message = "Added tasks:"
        for item in self.newTasks:
            message += "\n%s: %s" % ( str(item.startDateTime), item.title )
        _LOGGER.info( "import iCalendar: %s", message )

        if self.silent is False:
            QMessageBox.information( None, "Import iCalendar", message )
            self.silent = True                  ## do not show message on repeated redo

        self.data.tasksChanged.emit()

    def undo(self):
        if self.newTasks is None:
            return
        for item in self.newTasks:
            self.domainModel.removeTask( item )
        self.newTasks = []
        self.data.tasksChanged.emit()
