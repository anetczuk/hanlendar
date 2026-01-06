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
import pprint

from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtWidgets import QDialog, QFileDialog, QAction
from PyQt5.QtGui import QDesktopServices, QKeySequence

from hanlendar.domainmodel.local.task import Task
from hanlendar.gui import uiloader
from hanlendar.gui.utils import enable_layout, hide_layout, find_action
from hanlendar.domainmodel.calendardata import CalendarData


UiTargetClass, QtBaseClass = uiloader.load_ui_from_class_name(__file__)


_LOGGER = logging.getLogger(__name__)


##
## widget with task info
##
class TaskDetails(QtBaseClass):  # type: ignore[valid-type,misc]

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)
        self.ui = UiTargetClass()
        self.ui.setupUi(self)

        self.calendar_data: CalendarData = None
        self.task: Task = None
        ## store value in temporary variable to
        ## prevent adding "completed date" during field edit
        ## add "completed "date after accepting the changes
        self.completed = None
        self._read_only: bool = True

        self.ui.calendarCB.currentIndexChanged.connect(self._calendarIdChanged)
        self.ui.titleEdit.textChanged.connect(self._titleChanged)
        self.ui.completionSlider.valueChanged.connect(self._completedChanged)
        self.ui.priorityBox.valueChanged.connect(self._priorityChanged)
        self.ui.deadlineBox.stateChanged.connect(self._deadlineChanged)
        self.ui.startDateTime.dateTimeChanged.connect(self._startChanged)
        self.ui.dueDateTime.dateTimeChanged.connect(self._dueChanged)

        self.ui.locationEdit.textChanged.connect(self._locationChanged)
        self.ui.urlEdit.textChanged.connect(self._urlChanged)

        self.ui.descriptionEdit.setUndoRedoEnabled(True)
        self.ui.descriptionEdit.setContextMenuPolicy(Qt.CustomContextMenu)  # type: ignore[attr-defined]
        self.ui.descriptionEdit.textChanged.connect(self._descriptionChanged)
        self.ui.descriptionEdit.anchorClicked.connect(self._openLink)
        self.ui.descriptionEdit.customContextMenuRequested.connect(self._textEditContextMenuRequest)

        self.ui.openLocalFilePB.clicked.connect(self._openLocalFile)
        self.ui.openLocalDirPB.clicked.connect(self._openLocalDir)
        self.ui.addUrlPB.clicked.connect(self._addUrl)

        self.setTask(None)
        self.setReadOnly(read_only=True)

    def setReadOnly(self, *, read_only=True):
        self._read_only = read_only

        self._update_tabs_state(self.task)

        self.ui.calendarCB.setDisabled(read_only)
        self.ui.titleEdit.setReadOnly(read_only)
        self.ui.completionSlider.setDisabled(read_only)
        self.ui.priorityBox.setReadOnly(read_only)
        self.ui.deadlineBox.setDisabled(read_only)
        self.ui.startDateTime.setReadOnly(read_only=read_only)
        self.ui.dueDateTime.setReadOnly(read_only=read_only)

        self.ui.locationEdit.setReadOnly(read_only)
        self.ui.urlEdit.setReadOnly(read_only)
        self.ui.descriptionEdit.setReadOnly(read_only)
        self.ui.reminderWidget.setReadOnly(read_only=read_only)
        self.ui.recurrentWidget.setReadOnly(read_only=read_only)

        hide_layout(self.ui.urlLayout, hide_state=read_only)

        enable_layout(self.ui.bottomButtonsLayout, enable_state=not read_only)
        hide_layout(self.ui.bottomButtonsLayout, hide_state=read_only)

    def setCalendarData(self, calendar_data: CalendarData):
        self.calendar_data = calendar_data

    def setTask(self, task: Task):
        self.task = None  ## prevents triggering change callbacks

        self._update_tabs_state(task)

        if task is None:
            self.ui.reminderWidget.setItem(None)
            self.ui.recurrentWidget.setItem(None)

            self.ui.calendarCB.clear()
            self.ui.uidText.clear()
            self.ui.parentUidText.clear()
            self.ui.titleEdit.clear()
            self.ui.locationEdit.clear()
            self.ui.urlEdit.clear()
            self.ui.completionSlider.setValue(0)
            self.ui.priorityBox.setValue(0)
            self.ui.deadlineBox.setChecked(False)
            todayDate = datetime.datetime.now(datetime.timezone.utc)
            self.ui.startDateTime.setValue(todayDate)
            self.ui.dueDateTime.setValue(todayDate)
            self.ui.descriptionEdit.clear()
            self.ui.insertUrlEdit.clear()

            self.ui.unknownPropsTextEdit.clear()
            return

        self.ui.reminderWidget.setItem(task.commonData)
        self.ui.recurrentWidget.setItem(task)

        self.completed = task.completed

        self.ui.calendarCB.clear()
        curr_cal_id = task.commonData.calendar_id
        if self.calendar_data is not None:
            selected_cal = -1
            cal_items = self.calendar_data.getItems()
            for cal_index, cal_item in enumerate(cal_items):
                self.ui.calendarCB.addItem(cal_item[0], cal_item[1])
                if curr_cal_id == cal_item[1]:
                    selected_cal = cal_index
            if selected_cal < 0:
                _LOGGER.warning(
                    "unable to find item's calendar: %s curr cals: %s",
                    curr_cal_id,
                    self.calendar_data.items,
                )
            self.ui.calendarCB.setCurrentIndex(selected_cal)
        else:
            _LOGGER.warning("calendar data not given")
            if curr_cal_id is None:
                self.ui.calendarCB.addItem(CalendarData.DEFAULT_LABEL, curr_cal_id)
            else:
                self.ui.calendarCB.addItem(curr_cal_id, curr_cal_id)
            self.ui.calendarCB.setCurrentIndex(0)

        self.ui.uidText.setText(task.UID)
        taskParent = task.getParent()
        if taskParent is not None:
            self.ui.parentUidText.setText(taskParent.UID)
        else:
            self.ui.parentUidText.setText("None")

        self.ui.titleEdit.setText(task.title)
        self.ui.locationEdit.setText(task.location)
        self.ui.urlEdit.setText(task.url)
        self.ui.completionSlider.setValue(task.completed)
        self.ui.priorityBox.setValue(task.priority)

        if task.startDateTime is None:
            self.ui.deadlineBox.setChecked(True)
            self.ui.startDateTime.setNone()
        else:
            self.ui.deadlineBox.setChecked(False)
            self.ui.startDateTime.setValue(task.startDateTime)

        if task.dueDateTime is not None:
            self.ui.dueDateTime.setValue(task.dueDateTime)
        else:
            self.ui.startDateTime.setNone()

        self.ui.descriptionEdit.setText(task.description)
        self.ui.insertUrlEdit.setText(task.url)

        if task.unknownProps:
            content = pprint.pformat(task.unknownProps, indent=3)
            self.ui.unknownPropsTextEdit.setPlainText(content)
        else:
            self.ui.unknownPropsTextEdit.clear()

        ## set at end - prevents triggering change callbacks
        self.task = task

    def _update_tabs_state(self, task: Task):
        if task and task.unknownProps:
            self.ui.tabWidget.setTabEnabled(3, True)
        else:
            self.ui.tabWidget.setTabEnabled(3, False)

        if self._read_only is False or task is None:
            self.ui.tabWidget.setTabEnabled(1, True)
            self.ui.tabWidget.setTabEnabled(2, True)
            return

        if not task.reminderList:
            self.ui.tabWidget.setTabEnabled(1, False)
        else:
            self.ui.tabWidget.setTabEnabled(1, True)

        if task.recurrence is None:
            self.ui.tabWidget.setTabEnabled(2, False)
        else:
            self.ui.tabWidget.setTabEnabled(2, True)

    ## =====================================================================

    ## handle Ctrl+Shift+V key shortcut
    ## done "manually", because other methods does not work
    def keyPressEvent(self, event):
        event_key = event.key()
        flags = Qt.ControlModifier | Qt.ShiftModifier  # type: ignore[attr-defined]
        if event_key == Qt.Key_V and event.modifiers() == flags:  # type: ignore[attr-defined]
            self._pasteUnformattedToDescription()
            event.accept()  ## do not propagate event to parents
        super().keyPressEvent(event)

    def _calendarIdChanged(self):
        if self._read_only:
            return
        if not self.task:
            return
        cal_id = self.ui.calendarCB.currentData()
        self.task.commonData.calendar_id = cal_id

    def _titleChanged(self, newValue):
        if self._read_only:
            return
        if not self.task:
            return
        # _LOGGER.debug("changing title from %s to %s", self.task.title, newValue)
        self.task.title = newValue

    def _locationChanged(self):
        if self._read_only:
            return
        if not self.task:
            return
        newValue = self.ui.locationEdit.text()
        self.task.location = newValue

    def _urlChanged(self):
        if self._read_only:
            return
        if not self.task:
            return
        newValue = self.ui.urlEdit.text()
        self.task.url = newValue

    def _descriptionChanged(self):
        if self._read_only:
            return
        if not self.task:
            return
        newValue = self.ui.descriptionEdit.toHtml()
        # _LOGGER.debug("changing description from %s to %s", self.task.description, newValue)
        self.task.description = newValue

    def _completedChanged(self, newValue):
        self.ui.completionValueLabel.setNum(newValue)
        if self._read_only:
            return
        if not self.task:
            return
        _LOGGER.debug("changing completed from %s to %s", self.completed, newValue)
        self.completed = newValue

    def _priorityChanged(self, newValue):
        if self._read_only:
            return
        if not self.task:
            return
        _LOGGER.debug("changing priority from %s to %s", self.task.priority, newValue)
        self.task.priority = newValue

    ## deadline checkbox
    def _deadlineChanged(self, state):
        if self._read_only:
            return
        if not self.task:
            return
        _LOGGER.debug("changing deadline to %s", state)
        if self.ui.deadlineBox.isChecked():
            self.task.setDeadline()
            self.ui.startDateTime.setReadOnly(read_only=True)
        else:
            start_date_time = self.ui.startDateTime.dateTime()
            self.task.setOccurrence(start_date_time, self.task.dueDateTime)
            self.ui.startDateTime.setReadOnly(read_only=False)
        self.ui.recurrentWidget.refreshWidget()

    def _startChanged(self, newValue):
        if self._read_only:
            return
        if not self.task:
            return
        _LOGGER.debug("changing start from %s to %s", self.task.startDateTime, newValue)
        self.task.setOccurrence(newValue, self.task.dueDateTime)
        if self._compare_start_due() > 0:
            self.ui.dueDateTime.setValue(self.task.startDateTime)
        self.ui.recurrentWidget.refreshWidget()

    def _dueChanged(self, newValue):
        if self._read_only:
            return
        if not self.task:
            return
        _LOGGER.debug("changing due from %s to %s", self.task.dueDateTime, newValue)
        self.task.setOccurrence(self.task.startDateTime, newValue)
        if self._compare_start_due() > 0:
            self.ui.startDateTime.setValue(self.task.dueDateTime)
        self.ui.recurrentWidget.refreshWidget()

    ## -1 - start is less than due
    ##  0 - start is equal to due
    ##  1 - start is greater than due
    def _compare_start_due(self) -> int:
        if self.task.startDateTime is None:
            return -1
        if self.task.dueDateTime is None:
            return -1

        start_time = self.task.startDateTime
        due_time = self.task.dueDateTime

        if start_time > due_time:
            return 1
        if start_time == due_time:
            return 0
        return -1

    def _openLocalFile(self):
        fielDialog = QFileDialog(self)
        fielDialog.setFileMode(QFileDialog.ExistingFile)
        dialogCode = fielDialog.exec_()
        if dialogCode == QDialog.Rejected:
            return
        selectedFile = fielDialog.selectedFiles()[0]
        fileUrl = QUrl.fromLocalFile(selectedFile)
        self.ui.insertUrlEdit.setText(fileUrl.toString())

    def _openLocalDir(self):
        fielDialog = QFileDialog(self)
        fielDialog.setFileMode(QFileDialog.Directory)
        dialogCode = fielDialog.exec_()
        if dialogCode == QDialog.Rejected:
            return
        selectedFile = fielDialog.selectedFiles()[0]
        fileUrl = QUrl.fromLocalFile(selectedFile)
        self.ui.insertUrlEdit.setText(fileUrl.toString())

    def _addUrl(self):
        urlText = self.ui.insertUrlEdit.text()
        if len(urlText) < 1:
            return
        hrefText = f"""<a href="{urlText}">{urlText}</a> """
        self.ui.descriptionEdit.insertHtml(hrefText)
        self.ui.insertUrlEdit.setText("")

    def _openLink(self, link):
        self.ui.insertUrlEdit.setText(link.toLocalFile())
        QDesktopServices.openUrl(link)

    def _textEditContextMenuRequest(self, point):
        menu = self.ui.descriptionEdit.createStandardContextMenu()
        deleteAction = find_action(menu, "Delete")
        pastePlainAction = QAction(menu)
        menu.insertAction(deleteAction, pastePlainAction)
        pastePlainAction.setText("Paste unformatted")
        pastePlainAction.setShortcut(QKeySequence("Ctrl+Shift+V"))
        pastePlainAction.triggered.connect(self._pasteUnformattedToDescription)
        if self.ui.descriptionEdit.canPaste() is False:
            pastePlainAction.setEnabled(False)
        globalPos = self.ui.descriptionEdit.mapToGlobal(point)
        menu.exec_(globalPos)

    def _pasteUnformattedToDescription(self):
        richTextState = self.ui.descriptionEdit.acceptRichText()
        self.ui.descriptionEdit.setAcceptRichText(False)
        self.ui.descriptionEdit.paste()
        self.ui.descriptionEdit.setAcceptRichText(richTextState)
