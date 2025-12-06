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
from enum import Enum, unique

from PyQt5.QtCore import pyqtSignal

from hanlendar.domainmodel.item import DateDateTime, ensure_date_time
from hanlendar.gui import uiloader


UiTargetClass, QtBaseClass = uiloader.load_ui_from_class_name(__file__)


_LOGGER = logging.getLogger(__name__)


class DateTimeModeWidget(QtBaseClass):  # type: ignore[valid-type,misc]

    @unique
    class DateTimeMode(Enum):
        NONE = "None"
        DATE = "Date"
        DATETIME = "DateTime"

        @classmethod
        def indexOf(cls, key):
            index = 0
            for item in cls:
                if item == key:
                    return index
                if item.name == key:
                    return index
                index = index + 1
            return -1

    valueChanged = pyqtSignal(object)  # DateDateTime
    dateChanged = pyqtSignal(object)  # DateDateTime
    dateTimeChanged = pyqtSignal(object)  # DateDateTime

    def __init__(self, parentWidget=None):
        super().__init__(parentWidget)
        self.ui = UiTargetClass()
        self.ui.setupUi(self)

        self.ui.modeCB.clear()
        for item in DateTimeModeWidget.DateTimeMode:
            value = item.value
            self.ui.modeCB.addItem(value, item)

        self.setReadOnly(read_only=False)
        self.setMode(DateTimeModeWidget.DateTimeMode.NONE)

        self.ui.modeCB.currentIndexChanged.connect(self._modeChanged)
        self.ui.dateEdit.dateChanged.connect(self._dateChanged)
        self.ui.dateTimeEdit.dateTimeChanged.connect(self._dateTimeChanged)

    def setReadOnly(self, *, read_only=True):
        enabled = not read_only
        self.ui.modeCB.setEnabled(enabled)
        self.ui.dateEdit.setReadOnly(read_only)
        self.ui.dateTimeEdit.setReadOnly(read_only)

    def setMode(self, mode: "DateTimeModeWidget.DateTimeMode"):
        mode_index = DateTimeModeWidget.DateTimeMode.indexOf(mode)
        self.ui.stackedWidget.setCurrentIndex(mode_index)
        self.ui.modeCB.setCurrentIndex(mode_index)

    def setNone(self):
        self.setMode(DateTimeModeWidget.DateTimeMode.NONE)

    def setDate(self, value: datetime.date):
        if value is None:
            self.setMode(DateTimeModeWidget.DateTimeMode.NONE)
            return
        self.ui.dateEdit.setDate(value)
        self.setMode(DateTimeModeWidget.DateTimeMode.DATE)

    def setDateTime(self, value: datetime.datetime):
        if value is None:
            self.setMode(DateTimeModeWidget.DateTimeMode.NONE)
            return
        self.ui.dateTimeEdit.setDateTime(value)
        self.setMode(DateTimeModeWidget.DateTimeMode.DATETIME)

    def setValue(self, value: DateDateTime):
        if value is None:
            self.setMode(DateTimeModeWidget.DateTimeMode.NONE)
            return
        if isinstance(value, datetime.datetime):
            self.setDateTime(value)
        elif isinstance(value, datetime.date):
            self.setDate(value)
        else:
            _LOGGER.error("unhandled value type: %s", type(value))
            self.setMode(DateTimeModeWidget.DateTimeMode.NONE)

    def dateTime(self):
        return self._get_value()

    def _modeChanged(self):
        current_index = self.ui.modeCB.currentIndex()
        self.ui.stackedWidget.setCurrentIndex(current_index)
        self._emit_value()

    def _dateChanged(self, new_value):
        blocked = self.ui.dateTimeEdit.blockSignals(True)
        new_value = new_value.toPyDate()
        value_dt = ensure_date_time(new_value)
        self.ui.dateTimeEdit.setDateTime(value_dt)
        self.ui.dateTimeEdit.blockSignals(blocked)

        self._emit_value()

    def _dateTimeChanged(self, new_value):
        blocked = self.ui.dateEdit.blockSignals(True)
        new_value = new_value.toPyDateTime()
        self.ui.dateEdit.setDate(new_value.date())
        self.ui.dateEdit.blockSignals(blocked)

        self._emit_value()

    def _emit_value(self):
        emit_value = self._get_value()
        self.valueChanged.emit(emit_value)
        self.dateChanged.emit(emit_value)
        self.dateTimeChanged.emit(emit_value)

    def _get_value(self):
        current_data = self.ui.modeCB.currentData()
        if current_data == DateTimeModeWidget.DateTimeMode.NONE:
            return None
        if current_data == DateTimeModeWidget.DateTimeMode.DATE:
            newValue = self.ui.dateEdit.date()
            return newValue.toPyDate()
        if current_data == DateTimeModeWidget.DateTimeMode.DATETIME:
            newValue = self.ui.dateTimeEdit.dateTime()
            emit_value = newValue.toPyDateTime()
            return emit_value.replace(second=0, microsecond=0)
        _LOGGER.error("unhandled data type case: %s", current_data)
        return None
