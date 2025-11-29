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

from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtWidgets import QDialog, QFileDialog, QAction
from PyQt5.QtGui import QDesktopServices, QKeySequence

from hanlendar.domainmodel.local.task import Task
from hanlendar.gui import uiloader
from hanlendar.gui.utils import enable_layout, hide_layout, find_action


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

        self.task: Task = None
        self.completed = None
        self._read_only: bool = True

        self.ui.titleEdit.textChanged.connect(self._titleChanged)
        self.ui.completionSlider.valueChanged.connect(self._completedChanged)
        self.ui.priorityBox.valueChanged.connect(self._priorityChanged)
        self.ui.deadlineBox.stateChanged.connect(self._deadlineChanged)
        self.ui.startDateTime.dateTimeChanged.connect(self._startChanged)
        self.ui.dueDateTime.dateTimeChanged.connect(self._dueChanged)

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

        self.ui.titleEdit.setReadOnly(read_only)
        self.ui.completionSlider.setDisabled(read_only)
        self.ui.priorityBox.setReadOnly(read_only)
        self.ui.deadlineBox.setDisabled(read_only)
        self.ui.startDateTime.setReadOnly(read_only)
        self.ui.dueDateTime.setReadOnly(read_only)

        self.ui.descriptionEdit.setReadOnly(read_only)
        self.ui.reminderWidget.setReadOnly(read_only=read_only)
        self.ui.recurrentWidget.setReadOnly(read_only=read_only)

        hide_layout(self.ui.urlLayout, hide_state=read_only)

        enable_layout(self.ui.bottomButtonsLayout, enable_state=not read_only)
        hide_layout(self.ui.bottomButtonsLayout, hide_state=read_only)

    def setTask(self, task: Task):
        self.task = None  ## prevents triggering change callbacks

        self._update_tabs_state(task)

        if task is None:
            self.ui.reminderWidget.setItem(None)
            self.ui.recurrentWidget.setItem(None)

            self.ui.uidText.clear()
            self.ui.parentUidText.clear()
            self.ui.titleEdit.clear()
            self.ui.completionSlider.setValue(0)
            self.ui.priorityBox.setValue(0)
            self.ui.deadlineBox.setChecked(False)
            todayDate = datetime.datetime.today()
            self.ui.startDateTime.setDateTime(todayDate)
            self.ui.dueDateTime.setDateTime(todayDate)
            self.ui.descriptionEdit.clear()
            self.ui.urlEdit.clear()
            return

        self.ui.reminderWidget.setItem(task.commonData)
        self.ui.recurrentWidget.setItem(task)

        self.completed = task.completed

        self.ui.uidText.setText(task.UID)
        taskParent = task.getParent()
        if taskParent is not None:
            self.ui.parentUidText.setText(taskParent.UID)
        else:
            self.ui.parentUidText.setText("None")

        self.ui.titleEdit.setText(task.title)
        self.ui.completionSlider.setValue(task.completed)
        self.ui.priorityBox.setValue(task.priority)

        if task.startDateTime is None:
            self.ui.deadlineBox.setChecked(True)
            if task.dueDateTime is not None:
                self.ui.startDateTime.setDateTime(task.dueDateTime)
        else:
            self.ui.deadlineBox.setChecked(False)
            self.ui.startDateTime.setDateTime(task.startDateTime)
        if task.dueDateTime is not None:
            self.ui.dueDateTime.setEnabled(True)
            self.ui.dueDateTime.setDateTime(task.dueDateTime)
        else:
            self.ui.dueDateTime.setEnabled(False)

        self.ui.descriptionEdit.setText(task.description)
        self.ui.urlEdit.setText(task.url)

        ## set at end - prevents triggering change callbacks
        self.task = task

    def _update_tabs_state(self, task: Task):
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

    def _titleChanged(self, newValue):
        if self._read_only:
            return
        if not self.task:
            return
        _LOGGER.debug("changing title from %s to %s", self.task.title, newValue)
        self.task.title = newValue

    def _descriptionChanged(self):
        if self._read_only:
            return
        if not self.task:
            return
        newValue = self.ui.descriptionEdit.toHtml()
        _LOGGER.debug("changing description from %s to %s", self.task.description, newValue)
        self.task.description = newValue

    def _completedChanged(self, newValue):
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
    def _deadlineChanged(self, _state):
        if self._read_only:
            return
        if not self.task:
            return
        _LOGGER.debug("changing deadline to %s", _state)
        if self.ui.deadlineBox.isChecked():
            self.task.setDeadline()
        else:
            startDateTime = self.ui.startDateTime.dateTime()
            start_date_time = startDateTime.toPyDateTime()
            self.task.setOccurrence(start_date_time, self.task.dueDateTime)
        self.ui.recurrentWidget.refreshWidget()

    def _startChanged(self, newValue):
        if self._read_only:
            return
        if not self.task:
            return
        _LOGGER.debug("changing start from %s to %s", self.task.startDateTime, newValue)
        startDateTime = newValue.toPyDateTime()
        startDateTime = startDateTime.replace(second=0)
        self.task.setOccurrence(startDateTime, self.task.dueDateTime)
        if self.task.startDateTime > self.task.dueDateTime:
            self.ui.dueDateTime.setDateTime(self.task.startDateTime)
        self.ui.recurrentWidget.refreshWidget()

    def _dueChanged(self, newValue):
        if self._read_only:
            return
        if not self.task:
            return
        _LOGGER.debug("changing due from %s to %s", self.task.dueDateTime, newValue)
        dueDateTime = newValue.toPyDateTime()
        dueDateTime = dueDateTime.replace(second=0)
        self.task.setOccurrence(self.task.startDateTime, dueDateTime)
        if self.task.startDateTime is not None and self.task.dueDateTime < self.task.startDateTime:
            self.ui.startDateTime.setDateTime(self.task.dueDateTime)
        self.ui.recurrentWidget.refreshWidget()

    def _openLocalFile(self):
        fielDialog = QFileDialog(self)
        fielDialog.setFileMode(QFileDialog.ExistingFile)
        dialogCode = fielDialog.exec_()
        if dialogCode == QDialog.Rejected:
            return
        selectedFile = fielDialog.selectedFiles()[0]
        fileUrl = QUrl.fromLocalFile(selectedFile)
        self.ui.urlEdit.setText(fileUrl.toString())

    def _openLocalDir(self):
        fielDialog = QFileDialog(self)
        fielDialog.setFileMode(QFileDialog.Directory)
        dialogCode = fielDialog.exec_()
        if dialogCode == QDialog.Rejected:
            return
        selectedFile = fielDialog.selectedFiles()[0]
        fileUrl = QUrl.fromLocalFile(selectedFile)
        self.ui.urlEdit.setText(fileUrl.toString())

    def _addUrl(self):
        urlText = self.ui.urlEdit.text()
        if len(urlText) < 1:
            return
        hrefText = f"""<a href="{urlText}">{urlText}</a> """
        self.ui.descriptionEdit.insertHtml(hrefText)
        self.ui.urlEdit.setText("")

    def _openLink(self, link):
        self.ui.urlEdit.setText(link.toLocalFile())
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
