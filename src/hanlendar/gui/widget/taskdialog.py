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
import copy

from PyQt5.QtWidgets import QDialog

from hanlendar.domainmodel.local.task import LocalTask, Task
from hanlendar.gui import uiloader
from hanlendar.domainmodel.calendardata import CalendarData


UiTargetClass, QtBaseClass = uiloader.load_ui_from_class_name(__file__)


_LOGGER = logging.getLogger(__name__)


##
## modal window with editable task
##
class TaskDialog(QtBaseClass):  # type: ignore[valid-type,misc]

    def __init__(self, task: Task, calendar_data: CalendarData, parentWidget=None):
        super().__init__(parentWidget)
        self.ui = UiTargetClass()
        self.ui.setupUi(self)

        self.task: Task = None

        if task is not None:
            self.task = copy.deepcopy(task)
        else:
            self.task = LocalTask()

        self.ui.detailsWidget.setReadOnly(read_only=False)
        self.ui.detailsWidget.setCalendarData(calendar_data)
        self.ui.detailsWidget.setTask(self.task)
        self.finished.connect(self._finished)

    def getTask(self):
        return self.task

    def _finished(self, value):
        if value == QDialog.Rejected:
            ## changes rejected
            return
        self.task.completed = self.ui.detailsWidget.completed
