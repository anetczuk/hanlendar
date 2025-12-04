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

from hanlendar.domainmodel.local.todo import LocalToDo
from hanlendar.gui import uiloader
from hanlendar.gui.utils import enable_layout, hide_layout, find_action


UiTargetClass, QtBaseClass = uiloader.load_ui_from_class_name(__file__)


_LOGGER = logging.getLogger(__name__)


class ToDoDetails(QtBaseClass):  # type: ignore[valid-type,misc]

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)
        self.ui = UiTargetClass()
        self.ui.setupUi(self)

        self.todo: LocalToDo = None
        self._read_only: bool = True

        self.ui.titleEdit.textChanged.connect(self._titleChanged)
        self.ui.completionSlider.valueChanged.connect(self._completedChanged)
        self.ui.priorityBox.valueChanged.connect(self._priorityChanged)
        self.ui.startDateTime.dateTimeChanged.connect(self._startChanged)
        self.ui.dueDateTime.dateTimeChanged.connect(self._dueChanged)
        self.ui.completedDateTime.dateTimeChanged.connect(self._completedDateChanged)

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

        self.setToDo(None)
        self.setReadOnly(read_only=True)

    def setReadOnly(self, *, read_only=True):
        self._read_only = read_only

        self._update_tabs_state(self.todo)

        self.ui.titleEdit.setReadOnly(read_only)
        self.ui.completionSlider.setDisabled(read_only)
        self.ui.priorityBox.setReadOnly(read_only)
        self.ui.startDateTime.setReadOnly(read_only=read_only)
        self.ui.dueDateTime.setReadOnly(read_only=read_only)
        self.ui.completedDateTime.setReadOnly(read_only=read_only)

        self.ui.locationEdit.setReadOnly(read_only)
        self.ui.urlEdit.setReadOnly(read_only)
        self.ui.descriptionEdit.setReadOnly(read_only)
        self.ui.reminderWidget.setReadOnly(read_only=read_only)
        self.ui.recurrentWidget.setReadOnly(read_only=read_only)

        self.ui.insertUrlEdit.setReadOnly(read_only)

        hide_layout(self.ui.urlLayout, hide_state=read_only)

        enable_layout(self.ui.bottomButtonsLayout, enable_state=not read_only)
        hide_layout(self.ui.bottomButtonsLayout, hide_state=read_only)

    def setToDo(self, todo: LocalToDo):
        self.todo = None  ## prevents triggering change callbacks

        self._update_tabs_state(todo)

        if todo is None:
            self.ui.reminderWidget.setItem(None)
            self.ui.recurrentWidget.setItem(None)

            self.ui.uidText.clear()
            self.ui.parentUidText.clear()
            self.ui.titleEdit.clear()
            self.ui.locationEdit.clear()
            self.ui.urlEdit.clear()
            self.ui.completionSlider.setValue(0)
            self.ui.priorityBox.setValue(0)
            todayDate = datetime.datetime.today()
            self.ui.startDateTime.setValue(todayDate)
            self.ui.dueDateTime.setValue(todayDate)
            self.ui.completedDateTime.setDateTime(todayDate)
            self.ui.descriptionEdit.clear()
            self.ui.insertUrlEdit.clear()

            self.ui.unknownPropsTextEdit.clear()
            return

        self.ui.reminderWidget.setItem(todo.commonData)
        self.ui.recurrentWidget.setItem(todo)

        self.ui.uidText.setText(todo.UID)
        todoParent = todo.getParent()
        if todoParent is not None:
            self.ui.parentUidText.setText(todoParent.UID)
        else:
            self.ui.parentUidText.setText("None")

        self.ui.titleEdit.setText(todo.title)
        self.ui.locationEdit.setText(todo.location)
        self.ui.urlEdit.setText(todo.url)
        self.ui.completionSlider.setValue(todo.completed)
        self.ui.priorityBox.setValue(todo.priority)

        self.ui.startDateTime.setValue(todo.startDateTime)
        self.ui.dueDateTime.setValue(todo.dueDateTime)
        self.ui.completedDateTime.setValue(todo.completedDateTime)

        self.ui.descriptionEdit.setText(todo.description)

        if todo.unknownProps:
            content = pprint.pformat(todo.unknownProps, indent=3)
            self.ui.unknownPropsTextEdit.setPlainText(content)
        else:
            self.ui.unknownPropsTextEdit.clear()

        ## set at end - prevents triggering change callbacks
        self.todo = todo

    def _update_tabs_state(self, todo: LocalToDo):
        if todo and todo.unknownProps:
            self.ui.tabWidget.setTabEnabled(3, True)
        else:
            self.ui.tabWidget.setTabEnabled(3, False)

        if self._read_only is False or todo is None:
            self.ui.tabWidget.setTabEnabled(1, True)
            self.ui.tabWidget.setTabEnabled(2, True)
            return

        common_data = todo.commonData
        if not common_data.reminderList:
            self.ui.tabWidget.setTabEnabled(1, False)
        else:
            self.ui.tabWidget.setTabEnabled(1, True)

        if common_data.recurrence is None:
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
        if not self.todo:
            return
        _LOGGER.debug("changing title from %s to %s", self.todo.title, newValue)
        self.todo.title = newValue

    def _locationChanged(self):
        if self._read_only:
            return
        if not self.todo:
            return
        newValue = self.ui.locationEdit.text()
        self.todo.location = newValue

    def _urlChanged(self):
        if self._read_only:
            return
        if not self.todo:
            return
        newValue = self.ui.urlEdit.text()
        self.todo.url = newValue

    def _descriptionChanged(self):
        if self._read_only:
            return
        if not self.todo:
            return
        newValue = self.ui.descriptionEdit.toHtml()
        _LOGGER.debug("changing description from %s to %s", self.todo.description, newValue)
        self.todo.description = newValue

    def _completedChanged(self, newValue):
        self.ui.completionValueLabel.setNum(newValue)
        if self._read_only:
            return
        if not self.todo:
            return
        _LOGGER.debug("changing completed from %s to %s", self.todo.completed, newValue)
        self.todo.setCompleted(newValue)

        if newValue < 100:
            self.ui.completedDateTime.setNone()
            return

        ## completed is 100
        if self.todo.completedDateTime:
            self.ui.completedDateTime.setDateTime(self.todo.completedDateTime)
        else:
            curr_dt = datetime.datetime.now(datetime.timezone.utc)
            curr_dt = curr_dt.astimezone()
            self.ui.completedDateTime.setDateTime(curr_dt)

    def _priorityChanged(self, newValue):
        if self._read_only:
            return
        if not self.todo:
            return
        _LOGGER.debug("changing priority from %s to %s", self.todo.priority, newValue)
        self.todo.priority = newValue

    def _startChanged(self, newValue):
        if self._read_only:
            return
        if not self.todo:
            return
        _LOGGER.debug("changing start date from %s to %s", self.todo.startDateTime, newValue)
        self.todo.setStartDateTime(newValue)
        if self._compare_start_due() > 0:
            self.ui.dueDateTime.setValue(self.todo.startDateTime)
        self.ui.recurrentWidget.refreshWidget()

    def _dueChanged(self, newValue):
        if self._read_only:
            return
        if not self.todo:
            return
        _LOGGER.debug("changing due date from %s to %s", self.todo.dueDateTime, newValue)
        self.todo.setDueDateTime(newValue)
        if self._compare_start_due() > 0:
            self.ui.startDateTime.setValue(self.todo.dueDateTime)
        self.ui.recurrentWidget.refreshWidget()

    ## -1 - start is less than due
    ##  0 - start is equal to due
    ##  1 - start is greater than due
    def _compare_start_due(self) -> int:
        if self.todo.startDateTime is None:
            return -1
        if self.todo.dueDateTime is None:
            return -1

        start_time = self.todo.startDateTime
        due_time = self.todo.dueDateTime

        if start_time > due_time:
            return 1
        if start_time == due_time:
            return 0
        return -1

    def _completedDateChanged(self, newValue):
        if self._read_only:
            return
        if not self.todo:
            return
        _LOGGER.debug("changing completed date from %s to %s", self.todo.completedDateTime, newValue)
        if newValue is None:
            self.todo.setCompletedDateTime(None)
        else:
            self.todo.setCompletedDateTime(newValue)
        self.setToDo(self.todo)

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
