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
import datetime

from hanlendar.domainmodel.recurrent import RepeatType, Recurrent
from hanlendar.domainmodel.item import CommonData
from hanlendar.domainmodel.local.task import LocalTask
from hanlendar.domainmodel.local.todo import LocalToDo

from hanlendar.gui import uiloader


UiTargetClass, QtBaseClass = uiloader.load_ui_from_class_name(__file__)


_LOGGER = logging.getLogger(__name__)


class RecurrentWidget(QtBaseClass):  # type: ignore[valid-type,misc]

    class RecurrenceProvider:

        def get_common_data(self) -> CommonData:
            return None

        def print_next_recurrence(self) -> str:
            return "None"

    class TaskProvider(RecurrenceProvider):

        def __init__(self, task: LocalTask):
            super().__init__()
            self.task: LocalTask = task

        def get_common_data(self) -> CommonData:
            return self.task.commonData

        def print_next_recurrence(self) -> str:
            return self.task.printNextRecurrence()

    class ToDoProvider(RecurrenceProvider):

        def __init__(self, todo: LocalToDo):
            super().__init__()
            self.todo: LocalToDo = todo

        def get_common_data(self) -> CommonData:
            return self.todo.commonData

        def print_next_recurrence(self) -> str:
            # TODO: implement recurrence for LocalToDo
            return "None"

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)
        self.ui = UiTargetClass()
        self.ui.setupUi(self)

        self.recurrence_provider: RecurrentWidget.RecurrenceProvider = None
        self.read_only: bool = False

        self.setReadOnly(read_only=False)

        ## recurrent combo box
        for item in RepeatType:
            itemName = item.name
            self.ui.repeatModeCB.addItem(itemName, item)

        self.ui.endDateEdit.setDate(datetime.date.today())

        ## update GUI
        self._repeatModeChanged()

        self.ui.repeatModeCB.currentIndexChanged.connect(self._repeatModeChanged)
        self.ui.everySB.valueChanged.connect(self._everyValueChanged)
        self.ui.endDateCB.stateChanged.connect(self._finiteChanged)
        self.ui.endDateEdit.dateChanged.connect(self._endDateChanged)

        self.setItem(None)

    def setReadOnly(self, *, read_only: bool = True):
        self.read_only = read_only
        if self.read_only is False:
            self.ui.repeatModeStack.setCurrentIndex(0)
        else:
            self.ui.repeatModeStack.setCurrentIndex(1)
        self.ui.everySB.setReadOnly(self.read_only)
        self.ui.endDateEdit.setReadOnly(self.read_only)
        self.ui.endDateCB.setDisabled(self.read_only)

    def setItem(self, item: LocalTask | LocalToDo):
        if item is None:
            self.recurrence_provider = None
        elif isinstance(item, LocalTask):
            self.setTask(item)
        elif isinstance(item, LocalToDo):
            self.setToDo(item)
        else:
            message = f"invalid type: {type(item)}, LocalTask or LocalToDo allowed"
            raise RuntimeError(message)

    def setTask(self, task: LocalTask):
        self.recurrence_provider = RecurrentWidget.TaskProvider(task)
        self.refreshWidget()

    def setToDo(self, todo: LocalToDo):
        self.recurrence_provider = RecurrentWidget.ToDoProvider(todo)
        self.refreshWidget()

    def refreshWidget(self):
        recurrence = self._get_recurrence()
        if recurrence is None:
            self._setRepeatMode(RepeatType.NEVER)
            return

        self._setRepeatMode(recurrence.mode)
        self.ui.everySB.setValue(recurrence.every)
        if recurrence.endDate is not None:
            self.ui.endDateCB.setChecked(True)
            self.ui.endDateEdit.setDate(recurrence.endDate)
        else:
            self.ui.endDateCB.setChecked(False)
        self._activateWidget()

    def _setRepeatMode(self, repeatMode):
        self.ui.repeatModeCB.blockSignals(True)
        index = RepeatType.indexOf(repeatMode)
        self.ui.repeatModeCB.setCurrentIndex(index)
        self.ui.repeatModeLabel.setText(repeatMode.name)
        self.ui.repeatModeCB.blockSignals(False)

    def _get_common_data(self) -> CommonData:
        if self.recurrence_provider is None:
            return None
        return self.recurrence_provider.get_common_data()

    def _get_recurrence(self) -> Recurrent:
        common_data = self._get_common_data()
        if common_data is None:
            return None
        return common_data.recurrence

    # ===================== update data ===================================

    def _repeatModeChanged(self):
        common_data = self._get_common_data()
        repeatMode = self.ui.repeatModeCB.currentData()
        if repeatMode is RepeatType.NEVER:
            if common_data is not None:
                common_data.recurrence = None
            self._disableWidget()
            return

        if common_data.recurrence is None:
            common_data.recurrence = Recurrent()
            common_data.recurrence.every = self.ui.everySB.value()

        common_data.recurrence.mode = repeatMode
        self._activateWidget()
        if repeatMode is RepeatType.ASPARENT:
            self.ui.everySB.setEnabled(False)
            self.ui.endDateEdit.setEnabled(False)
            self.ui.endDateCB.setEnabled(False)
            self.ui.endDateCB.setChecked(False)

    def _everyValueChanged(self, newValue):
        recurrence = self._get_recurrence()
        if recurrence:
            recurrence.every = newValue
        self._updateNextRepeat()

    def _finiteChanged(self):
        recurrence = self._get_recurrence()
        if recurrence is None:
            return
        if self.ui.endDateCB.isChecked() is False:
            recurrence.endDate = None
            return
        if recurrence.endDate is None:
            endDate = self.ui.endDateEdit.date()
            recurrence.endDate = endDate.toPyDate()

    def _endDateChanged(self, newValue):
        recurrence = self._get_recurrence()
        if recurrence is None:
            return
        recurrence.endDate = newValue.toPyDate()

    ## ================= update GUI state ================

    def _disableWidget(self):
        self.ui.everySB.setEnabled(False)
        self.ui.endDateEdit.setEnabled(False)
        self.ui.endDateCB.setEnabled(False)
        self.ui.endDateCB.setChecked(False)
        self.ui.nextRepeatLabel.setText("None")

    def _activateWidget(self):
        self.ui.everySB.setEnabled(True)
        if self.read_only is False:
            self.ui.endDateCB.setEnabled(True)
        if self.ui.endDateCB.isChecked():
            self.ui.endDateEdit.setEnabled(True)
        else:
            self.ui.endDateEdit.setEnabled(False)
        self._updateNextRepeat()

    def _updateNextRepeat(self):
        common_data = self._get_common_data()
        if common_data is None:
            self.ui.nextRepeatLabel.setText("None")
            return
        repeatText = self.recurrence_provider.print_next_recurrence()
        self.ui.nextRepeatLabel.setText(repeatText)
