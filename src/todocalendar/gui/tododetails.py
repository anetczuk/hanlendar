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
from datetime import datetime

from . import uiloader

from PyQt5.QtWidgets import QListWidgetItem
from PyQt5.QtGui import QDesktopServices

from todocalendar.domainmodel.todo import ToDo


UiTargetClass, QtBaseClass = uiloader.loadUiFromClassName( __file__ )


_LOGGER = logging.getLogger(__name__)


class ToDoDetails( QtBaseClass ):           # type: ignore

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)
        self.ui = UiTargetClass()
        self.ui.setupUi(self)

        self.ui.descriptionEdit.anchorClicked.connect( self._openLink )

        self.setToDo( None )

    def setToDo(self, todo: ToDo):
        if todo is None:
            self.ui.titleEdit.clear()
            self.ui.descriptionEdit.clear()
            self.ui.completionLabel.clear()
            self.ui.priorityBox.setValue( 0 )
            return

        self.ui.titleEdit.setText( todo.title )
        self.ui.descriptionEdit.setText( todo.description )
        self.ui.completionLabel.setText( str(todo.completed) + "%" )
        self.ui.priorityBox.setValue( todo.priority )

    def _openLink( self, link ):
        QDesktopServices.openUrl( link )
