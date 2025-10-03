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
# from datetime import datetime

from datetime import date

from hanlendar.domainmodel.recurrent import RepeatType, Recurrent
from hanlendar.domainmodel.task import Task

from .. import uiloader


UiTargetClass, QtBaseClass = uiloader.load_ui_from_class_name( __file__ )


_LOGGER = logging.getLogger(__name__)


class RecurrentWidget( QtBaseClass ):           # type: ignore

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)
        self.ui = UiTargetClass()
        self.ui.setupUi(self)

        self.task: Task = None
        self.readOnly: bool = False

        self.setReadOnly( False )

        ## recurrent combo box
        for item in RepeatType:
            itemName = item.name
            self.ui.repeatModeCB.addItem( itemName, item )

        self.ui.endDateEdit.setDate( date.today() )

        ## update GUI
        self._repeatModeChanged()

        self.ui.repeatModeCB.currentIndexChanged.connect( self._repeatModeChanged )
        self.ui.everySB.valueChanged.connect( self._everyValueChanged )
        self.ui.endDateCB.stateChanged.connect( self._finiteChanged )
        self.ui.endDateEdit.dateChanged.connect( self._endDateChanged )

        self.setTask( None )

    def setReadOnly(self, readOnly):
        self.readOnly = readOnly
        if self.readOnly is False:
            self.ui.repeatModeStack.setCurrentIndex( 0 )
        else:
            self.ui.repeatModeStack.setCurrentIndex( 1 )
        self.ui.everySB.setReadOnly( self.readOnly )
        self.ui.endDateEdit.setReadOnly( self.readOnly )
        self.ui.endDateCB.setDisabled( self.readOnly )

    def setTask(self, task: Task):
        self.task = task
        self.refreshWidget()

    def refreshWidget(self):
        if self.task is None:
            self._setRepeatMode( RepeatType.NEVER )
            return
        if self.task.recurrence is None:
            self._setRepeatMode( RepeatType.NEVER )
            return

        self._setRepeatMode( self.task.recurrence.mode )
        self.ui.everySB.setValue( self.task.recurrence.every )
        if self.task.recurrence.endDate is not None:
            self.ui.endDateCB.setChecked( True )
            self.ui.endDateEdit.setDate( self.task.recurrence.endDate )
        else:
            self.ui.endDateCB.setChecked( False )
        self._activateWidget()

    def _setRepeatMode(self, repeatMode):
        self.ui.repeatModeCB.blockSignals( True )
        index = RepeatType.indexOf( repeatMode )
        self.ui.repeatModeCB.setCurrentIndex( index )
        self.ui.repeatModeLabel.setText( repeatMode.name )
        self.ui.repeatModeCB.blockSignals( False )

    # ===================== update data ===================================

    def _repeatModeChanged(self):
        repeatMode = self.ui.repeatModeCB.currentData()
        if repeatMode is RepeatType.NEVER:
            if self.task is not None:
                self.task.recurrence = None
            self._disableWidget()
            return

        if self.task.recurrence is None:
            self.task.recurrence = Recurrent()
            self.task.recurrence.every = self.ui.everySB.value()

        self.task.recurrence.mode = repeatMode
        self._activateWidget()
        if repeatMode is RepeatType.ASPARENT:
            self.ui.everySB.setEnabled( False )
            self.ui.endDateEdit.setEnabled( False )
            self.ui.endDateCB.setEnabled( False )
            self.ui.endDateCB.setChecked( False )

    def _everyValueChanged(self, newValue):
        if self.task:
            self.task.recurrence.every = newValue
        self._updateNextRepeat()

    def _finiteChanged(self):
        if self.task.recurrence is None:
            return
        if self.ui.endDateCB.isChecked() is False:
            self.task.recurrence.endDate = None
            return
        if self.task.recurrence.endDate is None:
            endDate = self.ui.endDateEdit.date()
            self.task.recurrence.endDate = endDate.toPyDate()

    def _endDateChanged(self, newValue):
        if self.task.recurrence is None:
            return
        self.task.recurrence.endDate = newValue.toPyDate()

    ## ================= update GUI state ================

    def _disableWidget(self):
        self.ui.everySB.setEnabled( False )
        self.ui.endDateEdit.setEnabled( False )
        self.ui.endDateCB.setEnabled( False )
        self.ui.endDateCB.setChecked( False )
        self.ui.nextRepeatLabel.setText( "None" )

    def _activateWidget(self):
        self.ui.everySB.setEnabled( True )
        if self.readOnly is False:
            self.ui.endDateCB.setEnabled( True )
        if self.ui.endDateCB.isChecked():
            self.ui.endDateEdit.setEnabled( True )
        else:
            self.ui.endDateEdit.setEnabled( False )
        self._updateNextRepeat()

    def _updateNextRepeat(self):
        if self.task is None:
            return
        repeatText = self.task.printNextRecurrence()
        self.ui.nextRepeatLabel.setText( repeatText )
