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

from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtWidgets import QDialog, QFileDialog, QMenu, QAction
from PyQt5.QtGui import QDesktopServices, QKeySequence

from hanlendar.domainmodel.local.task import LocalTask
from hanlendar.gui import uiloader


UiTargetClass, QtBaseClass = uiloader.load_ui_from_class_name(__file__)


_LOGGER = logging.getLogger(__name__)


class TaskDialog(QtBaseClass):  # type: ignore[valid-type,misc]

    def __init__(self, taskObject, parentWidget=None):
        super().__init__(parentWidget)
        self.ui = UiTargetClass()
        self.ui.setupUi(self)

        if taskObject is not None:
            self.task = copy.deepcopy(taskObject)
        else:
            self.task = LocalTask()

        self.completed = self.task.completed

        self.ui.reminderWidget.setTask(self.task)
        self.ui.recurrentWidget.setTask(self.task)

        if self.task.startDateTime is None:
            self.ui.deadlineBox.setChecked(True)
            if self.task.dueDateTime is None:
                dueDateTime = datetime.today()
                self.task.setOccurrenceDue(dueDateTime)
            self.ui.startDateTime.setDateTime(self.task.dueDateTime)
        else:
            self.ui.deadlineBox.setChecked(False)
            self.ui.startDateTime.setDateTime(self.task.startDateTime)
            if self.task.dueDateTime is None:
                dueDateTime = self.task.startDateTime + timedelta(hours=1)
                self.task.setOccurrence(self.task.startDateTime, dueDateTime)

        self.ui.descriptionEdit.setContextMenuPolicy(Qt.CustomContextMenu)  # type: ignore[attr-defined]

        self.ui.uidText.setText(self.task.UID)
        taskParent = self.task.getParent()
        if taskParent is not None:
            self.ui.parentUidText.setText(taskParent.UID)
        else:
            self.ui.parentUidText.setText("None")

        self.ui.titleEdit.setText(self.task.title)
        self.ui.descriptionEdit.setText(self.task.description)
        self.ui.completionSlider.setValue(self.task.completed)
        self.ui.priorityBox.setValue(self.task.priority)
        self.ui.dueDateTime.setDateTime(self.task.dueDateTime)

        self.ui.titleEdit.textChanged.connect(self._titleChanged)
        self.ui.descriptionEdit.textChanged.connect(self._descriptionChanged)
        self.ui.descriptionEdit.anchorClicked.connect(self._openLink)
        self.ui.descriptionEdit.customContextMenuRequested.connect(self.textEditContextMenuRequest)
        self.ui.completionSlider.valueChanged.connect(self._completedChanged)
        self.ui.priorityBox.valueChanged.connect(self._priorityChanged)
        self.ui.deadlineBox.stateChanged.connect(self._deadlineChanged)
        self.ui.startDateTime.dateTimeChanged.connect(self._startChanged)
        self.ui.dueDateTime.dateTimeChanged.connect(self._dueChanged)

        self.ui.openLocalFilePB.clicked.connect(self._openLocalFile)
        self.ui.openLocalDirPB.clicked.connect(self._openLocalDir)
        self.ui.addUrlPB.clicked.connect(self._addUrl)

        self.finished.connect(self._finished)

        self.ui.descriptionEdit.setUndoRedoEnabled(True)

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
        self.task.title = newValue

    def _descriptionChanged(self):
        newValue = self.ui.descriptionEdit.toHtml()
        self.task.description = newValue

    def _completedChanged(self, newValue):
        # self.task.completed = newValue
        self.completed = newValue

    def _priorityChanged(self, newValue):
        self.task.priority = newValue

    ## deadline checkbox
    def _deadlineChanged(self, _state):
        if self.ui.deadlineBox.isChecked():
            self.task.setDeadline()
        else:
            startDateTime = self.ui.startDateTime.dateTime()
            self.task.startDateTime = startDateTime.toPyDateTime()
        self.ui.recurrentWidget.refreshWidget()

    def _startChanged(self, newValue):
        startDateTime = newValue.toPyDateTime()
        startDateTime = startDateTime.replace(second=0)
        self.task.setOccurrence(startDateTime, self.task.dueDateTime)
        if self.task.startDateTime > self.task.dueDateTime:
            self.ui.dueDateTime.setDateTime(self.task.startDateTime)
        self.ui.recurrentWidget.refreshWidget()

    def _dueChanged(self, newValue):
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
        #         QDesktopServices.openUrl( QUrl("http://google.com") )
        #         QDesktopServices.openUrl( QUrl("file:///media/E/bluetooth.txt") )
        self.ui.urlEdit.setText(link.toLocalFile())
        QDesktopServices.openUrl(link)

    def textEditContextMenuRequest(self, point):
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

    def _finished(self, _value):
        self.task.completed = self.completed

    def _pasteUnformattedToDescription(self):
        richTextState = self.ui.descriptionEdit.acceptRichText()
        self.ui.descriptionEdit.setAcceptRichText(False)
        self.ui.descriptionEdit.paste()
        self.ui.descriptionEdit.setAcceptRichText(richTextState)


def find_action(menu: QMenu, actionText):
    actions = menu.actions()
    for act in actions:
        currText = act.text()
        if actionText in currText:
            return act
    return None
