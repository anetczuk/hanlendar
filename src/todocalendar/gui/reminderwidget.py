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
from todocalendar.domainmodel.reminder import Reminder

from PyQt5.QtCore import QTime
from PyQt5.QtWidgets import QListWidgetItem


UiTargetClass, QtBaseClass = uiloader.loadUiFromClassName( __file__ )


_LOGGER = logging.getLogger(__name__)


class ReminderWidget( QtBaseClass ):           # type: ignore

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)
        self.ui = UiTargetClass()
        self.ui.setupUi(self)

        self.task = None

        self.ui.daysBox.valueChanged.connect( self._daysChanged )
        self.ui.hoursEdit.timeChanged.connect( self._hoursChanged )

        self.ui.newPB.clicked.connect( self._newReminder )
        self.ui.removePB.clicked.connect( self._removeReminder )
        self.ui.reminderList.itemSelectionChanged.connect( self._selectReminder )

        self.setTask( None )

    def setTask(self, task: Task):
        self.task = task
        if self.task is None:
            self.setEnabled( False )
            self.ui.reminderList.clear()
            return

        self.setEnabled( True )
        self.refreshWidget()

    def _newReminder(self):
        if self.task.reminderList is None:
            self.task.reminderList = list()
        self.task.reminderList.append( Reminder() )
        self._activateWidget()

    def _removeReminder(self):
        assert self.task.reminderList is not None
        reminder = self._getCurrentReminder()
        self.task.reminderList.remove( reminder )
        self.refreshWidget()

    def _selectReminder(self):
        reminder: Reminder = self._getCurrentReminder()
        if reminder is None:
            self.ui.daysBox.setEnabled( False )
            self.ui.hoursEdit.setEnabled( False )
            self.ui.removePB.setEnabled( False )
            return

        self.ui.daysBox.setEnabled( True )
        self.ui.hoursEdit.setEnabled( True )
        self.ui.removePB.setEnabled( True )

        timeOffset = reminder.splitTimeOffset()
        self.ui.daysBox.setValue( timeOffset[0] )
        time = QTime.fromMSecsSinceStartOfDay( timeOffset[1] * 1000 )
        self.ui.hoursEdit.setTime( time )

    def _daysChanged(self, newValue):
        reminder: Reminder = self._getCurrentReminder()
        reminder.setDays( newValue )
        item = self.ui.reminderList.currentItem()
        item.setText( reminder.printPretty() )

    def _hoursChanged(self, newTime):
        reminder: Reminder = self._getCurrentReminder()
        millis = newTime.msecsSinceStartOfDay()
        reminder.setMillis( millis )
        item = self.ui.reminderList.currentItem()
        item.setText( reminder.printPretty() )

    # ===================================================================

    def refreshWidget(self):
        if self.task is None:
            self._disableWidget()
            return
        if self.task.reminderList is None:
            self._disableWidget()
            return
        if len( self.task.reminderList ) < 1:
            self._disableWidget()
            return
        self._activateWidget()

    def _disableWidget(self):
        self.ui.daysBox.setEnabled( False )
        self.ui.hoursEdit.setEnabled( False )
        self.ui.removePB.setEnabled( False )
        self.ui.reminderList.clear()
        self.ui.reminderList.setEnabled( False )

    def _activateWidget(self):
        self.ui.daysBox.setEnabled( False )
        self.ui.hoursEdit.setEnabled( False )
        self.ui.reminderList.setEnabled( True )

        self.ui.reminderList.clear()
        for i in range( 0, len(self.task.reminderList) ):
            rem = self.task.reminderList[ i ]
            item = QListWidgetItem( rem.printPretty() )
            self.ui.reminderList.insertItem( i, item )

    def _getCurrentReminder(self):
        selected = self.ui.reminderList.selectedItems()
        if len( selected ) < 1:
            return None
        currentRow = self.ui.reminderList.currentRow()
        if currentRow < 0:
            return None
        if currentRow >= len( self.task.reminderList ):
            return None
        return self.task.reminderList[ currentRow ]
