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

from . import uiloader

from todocalendar.domainmodel.task import Task
from todocalendar.domainmodel.recurrent import RepeatType, Recurrent


UiTargetClass, QtBaseClass = uiloader.loadUiFromClassName( __file__ )


_LOGGER = logging.getLogger(__name__)


class RecurrentWidget( QtBaseClass ):           # type: ignore

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)
        self.ui = UiTargetClass()
        self.ui.setupUi(self)

        self.task = None

        ## recurrent combo box
        for item in RepeatType:
            itemName = item.name
            self.ui.repeatModeCB.addItem( itemName, item )

        ## update GUI
        self._repeatModeChanged()

        self.ui.repeatModeCB.currentIndexChanged.connect( self._repeatModeChanged )
        self.ui.everySB.valueChanged.connect( self._everyValueChanged )

        self.setTask( None )

    def setTask(self, task: Task):
        self.task = task
        self.refreshWidget()

    def refreshWidget(self):
        if self.task is None:
            self.setEnabled( False )
            self._setRepeatMode( RepeatType.NEVER )
            return
        self.setEnabled( True )
        if self.task.recurrence is None:
            self._setRepeatMode( RepeatType.NEVER )
            return
        self._setRepeatMode( self.task.recurrence.mode )
        self.ui.everySB.setValue( self.task.recurrence.every )
        self._activateWidget()

    # ===================================================================

    def _setRepeatMode(self, repeatMode):
        index = RepeatType.indexOf( repeatMode )
        self.ui.repeatModeCB.setCurrentIndex( index )

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

    def _everyValueChanged(self, newValue):
        self.task.recurrence.every = newValue
        self._updateNextRepeat()

    def _disableWidget(self):
        self.ui.everySB.setEnabled( False )
        self.ui.endDateEdit.setEnabled( False )
        self.ui.endDateCB.setEnabled( False )
        self.ui.nextRepeatLabel.setText( "None" )

    def _activateWidget(self):
        self.ui.everySB.setEnabled( True )
        self.ui.endDateCB.setEnabled( True )
        if self.ui.endDateCB.isChecked():
            self.ui.endDateEdit.setEnabled( True )
        else:
            self.ui.endDateEdit.setEnabled( False )
        self._updateNextRepeat()

    def _updateNextRepeat(self):
        repeatText = self.task.printRecurrent()
        self.ui.nextRepeatLabel.setText( repeatText )
