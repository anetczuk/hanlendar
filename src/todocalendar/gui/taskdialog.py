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
from datetime import datetime, timedelta
import copy

from . import uiloader

from todocalendar.domainmodel.task import Task


UiTargetClass, QtBaseClass = uiloader.loadUiFromClassName( __file__ )


_LOGGER = logging.getLogger(__name__)


class TaskDialog( QtBaseClass ):           # type: ignore

    def __init__(self, taskObject, parentWidget=None):
        super().__init__(parentWidget)
        self.ui = UiTargetClass()
        self.ui.setupUi(self)

        if taskObject is not None:
            self.task = copy.deepcopy( taskObject )
        else:
            self.task = Task()

        self.ui.reminderWidget.setTask( self.task )

        if self.task.startDate is None:
            self.ui.deadlineBox.setChecked( True )
            if self.task.dueDate is None:
                self.task.dueDate = datetime.today()
            self.ui.startDateTime.setDateTime( self.task.dueDate )
        else:
            self.ui.deadlineBox.setChecked( False )
            self.ui.startDateTime.setDateTime( self.task.startDate )
            if self.task.dueDate is None:
                self.task.dueDate = self.task.startDate + timedelta(hours=1)

        self.ui.titleEdit.setText( self.task.title )
        self.ui.descriptionEdit.setText( self.task.description )
        self.ui.completionSlider.setValue( self.task.completed )
        self.ui.priorityBox.setValue( self.task.priority )
        self.ui.dueDateTime.setDateTime( self.task.dueDate )

        self.ui.titleEdit.textChanged.connect( self._titleChanged )
        self.ui.descriptionEdit.textChanged.connect( self._descriptionChanged )
        self.ui.completionSlider.valueChanged.connect( self._completedChanged )
        self.ui.priorityBox.valueChanged.connect( self._priorityChanged )
        self.ui.deadlineBox.stateChanged.connect( self._deadlineChanged )
        self.ui.startDateTime.dateTimeChanged.connect( self._startChanged )
        self.ui.dueDateTime.dateTimeChanged.connect( self._dueChanged )

    def _titleChanged(self, newValue):
        self.task.title = newValue

    def _descriptionChanged(self):
        newValue = self.ui.descriptionEdit.toPlainText()
        self.task.description = newValue

    def _completedChanged(self, newValue):
        self.task.completed = newValue

    def _priorityChanged(self, newValue):
        self.task.priority = newValue

    ## deadline checkbox
    def _deadlineChanged(self, newValue):
        if self.ui.deadlineBox.isChecked():
            self.task.setDeadline()
        else:
            startDateTime = self.ui.startDateTime.dateTime()
            self.task.startDate = startDateTime.toPyDateTime()

    def _startChanged(self, newValue):
        self.task.startDate = newValue.toPyDateTime()

    def _dueChanged(self, newValue):
        self.task.dueDate = newValue.toPyDateTime()
