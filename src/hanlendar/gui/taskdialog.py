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

from PyQt5.QtWidgets import QDialog, QFileDialog
from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QDesktopServices

from hanlendar.domainmodel.task import Task

from . import uiloader


UiTargetClass, QtBaseClass = uiloader.load_ui_from_class_name( __file__ )


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

        self.completed = self.task.completed

        self.ui.reminderWidget.setTask( self.task )
        self.ui.recurrentWidget.setTask( self.task )

        if self.task.occurrenceStart is None:
            self.ui.deadlineBox.setChecked( True )
            if self.task.occurrenceDue is None:
                self.task.dueDateTime = datetime.today()
            self.ui.startDateTime.setDateTime( self.task.occurrenceDue )
        else:
            self.ui.deadlineBox.setChecked( False )
            self.ui.startDateTime.setDateTime( self.task.occurrenceStart )
            if self.task.occurrenceDue is None:
                self.task.dueDateTime = self.task.occurrenceStart + timedelta(hours=1)

        self.ui.titleEdit.setText( self.task.title )
        self.ui.descriptionEdit.setText( self.task.description )
        self.ui.completionSlider.setValue( self.task.completed )
        self.ui.priorityBox.setValue( self.task.priority )
        self.ui.dueDateTime.setDateTime( self.task.occurrenceDue )

        self.ui.titleEdit.textChanged.connect( self._titleChanged )
        self.ui.descriptionEdit.textChanged.connect( self._descriptionChanged )
        self.ui.descriptionEdit.anchorClicked.connect( self._openLink )
        self.ui.completionSlider.valueChanged.connect( self._completedChanged )
        self.ui.priorityBox.valueChanged.connect( self._priorityChanged )
        self.ui.deadlineBox.stateChanged.connect( self._deadlineChanged )
        self.ui.startDateTime.dateTimeChanged.connect( self._startChanged )
        self.ui.dueDateTime.dateTimeChanged.connect( self._dueChanged )

        self.ui.openLocalFilePB.clicked.connect( self._openLocalFile )
        self.ui.openLocalDirPB.clicked.connect( self._openLocalDir )
        self.ui.addUrlPB.clicked.connect( self._addUrl )

        self.finished.connect( self._finished )

    def _titleChanged(self, newValue):
        self.task.title = newValue

    def _descriptionChanged(self):
        newValue = self.ui.descriptionEdit.toHtml()
        self.task.description = newValue

    def _completedChanged(self, newValue):
        #self.task.completed = newValue
        self.completed = newValue

    def _priorityChanged(self, newValue):
        self.task.priority = newValue

    ## deadline checkbox
    def _deadlineChanged(self, _):
        if self.ui.deadlineBox.isChecked():
            self.task.setDeadline()
        else:
            startDateTime = self.ui.startDateTime.dateTime()
            self.task.startDateTime = startDateTime.toPyDateTime()
        self.ui.recurrentWidget.refreshWidget()

    def _startChanged(self, newValue):
        self.task.startDateTime = newValue.toPyDateTime()
        self.task.startDateTime = self.task.occurrenceStart.replace( second=0 )
        if self.task.occurrenceStart > self.task.occurrenceDue:
            self.ui.dueDateTime.setDateTime( self.task.occurrenceStart )
        self.ui.recurrentWidget.refreshWidget()

    def _dueChanged(self, newValue):
        self.task.dueDateTime = newValue.toPyDateTime()
        self.task.dueDateTime = self.task.dueDateTime.replace( second=0 )
        if self.task.occurrenceStart is not None and self.task.occurrenceDue < self.task.occurrenceStart:
            self.ui.startDateTime.setDateTime( self.task.occurrenceDue )
        self.ui.recurrentWidget.refreshWidget()

    def _openLocalFile(self):
        fielDialog = QFileDialog( self )
        fielDialog.setFileMode( QFileDialog.ExistingFile )
        dialogCode = fielDialog.exec_()
        if dialogCode == QDialog.Rejected:
            return
        selectedFile = fielDialog.selectedFiles()[0]
        fileUrl = QUrl.fromLocalFile( selectedFile )
        self.ui.urlEdit.setText( fileUrl.toString() )

    def _openLocalDir(self):
        fielDialog = QFileDialog( self )
        fielDialog.setFileMode( QFileDialog.Directory )
        dialogCode = fielDialog.exec_()
        if dialogCode == QDialog.Rejected:
            return
        selectedFile = fielDialog.selectedFiles()[0]
        fileUrl = QUrl.fromLocalFile( selectedFile )
        self.ui.urlEdit.setText( fileUrl.toString() )

    def _addUrl(self):
        urlText = self.ui.urlEdit.text()
        if len(urlText) < 1:
            return
        hrefText = "<a href=\"%s\">%s</a> " % (urlText, urlText)
        self.ui.descriptionEdit.insertHtml( hrefText )
        self.ui.urlEdit.setText( "" )

    def _openLink( self, link ):
#         QDesktopServices.openUrl( QUrl("http://google.com") )
#         QDesktopServices.openUrl( QUrl("file:///media/E/bluetooth.txt") )
        self.ui.urlEdit.setText( link.toLocalFile() )
        QDesktopServices.openUrl( link )

    def _finished(self, _):
        self.task.completed = self.completed
