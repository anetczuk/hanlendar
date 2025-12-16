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
import copy
import abc

from enum import Enum, unique, auto

from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QMessageBox

from hanlendar import persist
from hanlendar.domainmodel.caldav.manager import CalDAVConnector
from hanlendar.gui import uiloader, tray_icon
from hanlendar.gui.qt import pyqtSignal
from hanlendar.persist import serialize, deserialize


@unique
class DatabaseMode(Enum):
    LOCAL = auto()
    CALDAV = auto()

    @classmethod
    def findByName(cls, name, defaultValue=None):
        for item in cls:
            if item.name == name:
                return item
        return defaultValue

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

    @classmethod
    def getByIndex(cls, index, defaultValue=None):
        items = list(cls.__members__.items())
        if len(items) <= index:
            return defaultValue
        return items[index][1]


class CalendarItem:

    def __init__(self):
        pass

    @abc.abstractmethod
    def isEnabled(self) -> bool:
        message = "You need to define this method in derived class!"
        raise NotImplementedError(message)

    @abc.abstractmethod
    def getCalendarName(self) -> str:
        message = "You need to define this method in derived class!"
        raise NotImplementedError(message)

    @abc.abstractmethod
    def getCalendarMode(self) -> DatabaseMode:
        message = "You need to define this method in derived class!"
        raise NotImplementedError(message)


class LocalCalendarItem(CalendarItem, persist.Versionable):

    ##  1: added 'enabled'
    _class_version = 1

    def __init__(self, calendar_name: str = None):
        super().__init__()
        if calendar_name is None:
            calendar_name = "local"
        self.enabled: bool = True
        self.calendarName: str = calendar_name

    # ruff: noqa: PLR0912
    def _convertstate_(self, state_dict, state_version):  # pylint: disable=R0915,R0912
        _LOGGER.info("converting object from version %s to %s", state_version, self._class_version)

        if state_version is None:
            state_version = -1

        state_version = max(state_version, 0)

        if state_version == 0:
            state_dict["enabled"] = True
            state_version += 1

        return state_dict

    def __eq__(self, other):
        if not isinstance(other, LocalCalendarItem):
            return NotImplemented
        return self.__dict__ == other.__dict__

    def _key(self):
        return (self.enabled, self.calendarName)

    def __hash__(self):
        return hash(self._key())

    ## override
    def isEnabled(self) -> bool:
        return self.enabled

    ## override
    def getCalendarName(self) -> str:
        return self.calendarName

    ## override
    def getCalendarMode(self) -> DatabaseMode:
        return DatabaseMode.LOCAL


class CalDAVCalendarItem(CalendarItem, persist.Versionable):

    ##  1: added 'enabled'
    _class_version = 1

    def __init__(self, cal_name: str = None):
        super().__init__()
        if cal_name is None:
            cal_name = ""
        self.enabled: bool = True
        self.serverURL: str = ""
        self.serverUser: str = ""
        self.serverPassword: str = ""
        self.calendarName: str = cal_name

    # ruff: noqa: PLR0912
    def _convertstate_(self, state_dict, state_version):  # pylint: disable=R0915,R0912
        _LOGGER.info("converting object from version %s to %s", state_version, self._class_version)

        if state_version is None:
            state_version = -1

        state_version = max(state_version, 0)

        if state_version == 0:
            state_dict["enabled"] = True
            state_version += 1

        return state_dict

    def __eq__(self, other):
        if not isinstance(other, CalDAVCalendarItem):
            return NotImplemented
        return self.__dict__ == other.__dict__

    def _key(self):
        return (self.enabled, self.serverURL, self.serverUser, self.serverPassword, self.calendarName)

    def __hash__(self):
        return hash(self._key())

    ## override
    def isEnabled(self) -> bool:
        return self.enabled

    ## override
    def getCalendarName(self) -> str:
        return self.calendarName

    ## override
    def getCalendarMode(self) -> DatabaseMode:
        return DatabaseMode.CALDAV


## ====================================================================


class AppSettings:

    ##  0: first version
    ##  1: serialize CalendarItem
    _version = 1

    def __init__(self):
        self.trayIcon = tray_icon.TrayIconTheme.WHITE
        self.calendar_items: list[CalendarItem] = []

    def __eq__(self, other):
        if not isinstance(other, AppSettings):
            return NotImplemented
        return self.__dict__ == other.__dict__

    def _key(self):
        return (self.trayIcon, self.calendar_items)

    def __hash__(self):
        return hash(self._key())

    def getCalendar(self, cal_index: int) -> CalendarItem:
        if cal_index < 0:
            return None
        if cal_index >= len(self.calendar_items):
            return None
        return self.calendar_items[cal_index]

    def setCalendarMode(self, cal_index: int, cal_mode: DatabaseMode, cal_name: str = None) -> CalendarItem:
        curr_cal: CalendarItem = self.getCalendar(cal_index)
        if curr_cal is None:
            return None
        if curr_cal.getCalendarMode() == cal_mode:
            return None
        new_cal = self.createCalendar(cal_mode, cal_name)
        if new_cal is None:
            return None
        self.calendar_items[cal_index] = new_cal
        return new_cal

    def createCalendar(self, cal_mode: DatabaseMode, cal_name: str):
        if cal_mode == DatabaseMode.LOCAL:
            return LocalCalendarItem(cal_name)
        if cal_mode == DatabaseMode.CALDAV:
            return CalDAVCalendarItem(cal_name)
        _LOGGER.warning("unhandled mode: %s", cal_mode)
        return None

    def addLocalCalendar(self, calendar_name: str):
        item = LocalCalendarItem(calendar_name)
        self.calendar_items.append(item)

    def addCalDAVCalendar(self, server_url: str, user: str, passwd: str, calendar_name: str):
        item = CalDAVCalendarItem()
        item.serverURL = server_url
        item.serverUser = user
        item.serverPassword = passwd
        item.calendarName = calendar_name
        self.calendar_items.append(item)

    def loadSettings(self, settings: QSettings):
        settings.beginGroup("app_settings")

        version = settings.value("version", None, type=int)
        if version is None:
            version = 0

        if version < AppSettings._version:
            _LOGGER.info("converting version from %s to %s", version, AppSettings._version)

        trayName = settings.value("trayIcon", None, type=str)
        self.trayIcon = tray_icon.TrayIconTheme.findByName(trayName, tray_icon.TrayIconTheme.WHITE)

        dict_data = {}
        if version < 1:
            databaseName = settings.value("databaseMode", None, type=str)
            databaseMode = DatabaseMode.findByName(databaseName, DatabaseMode.LOCAL)

            cal_list: list[CalendarItem] = []
            cal: CalendarItem = None
            if databaseMode == DatabaseMode.CALDAV:
                cal = CalDAVCalendarItem()
                cal.serverURL = settings.value("serverURL", "", type=str)
                cal.serverUser = settings.value("serverUser", "", type=str)
                cal.serverPassword = settings.value("serverPassword", "", type=str)
                cal.calendarName = settings.value("calendarName", "", type=str)
                cal_list.append(cal)
                dict_data["calendar_items"] = cal_list

            elif databaseMode == DatabaseMode.LOCAL:
                cal = LocalCalendarItem()
                cal_list.append(cal)
                dict_data["calendar_items"] = cal_list

            else:
                _LOGGER.warning("unhandled database type: %s", databaseMode)
                cal = LocalCalendarItem()
                cal_list.append(cal)
                dict_data["calendar_items"] = cal_list

            version += 1

        if version == AppSettings._version:
            cal_list = dict_data.get("calendar_items", [])
            raw_data = settings.value("calendars")
            if raw_data is not None:
                items = deserialize(raw_data)
                cal_list.extend(items)
            dict_data["calendar_items"] = cal_list
        else:
            _LOGGER.info("expected version %s after conversion, got %s", AppSettings._version, version)

        self.calendar_items = dict_data.get("calendar_items", self.calendar_items)

        settings.endGroup()

    def saveSettings(self, settings: QSettings):
        settings.beginGroup("app_settings")

        settings.setValue("version", AppSettings._version)

        settings.setValue("trayIcon", self.trayIcon.name)

        raw_data = serialize(self.calendar_items)
        settings.setValue("calendars", raw_data)

        settings.endGroup()


## ============================================================
## ============================================================


UiTargetClass, QtBaseClass = uiloader.load_ui_from_class_name(__file__)


_LOGGER = logging.getLogger(__name__)


class SettingsDialog(QtBaseClass):  # type: ignore[valid-type,misc]

    iconThemeChanged = pyqtSignal(tray_icon.TrayIconTheme)
    exportLocal = pyqtSignal(CalDAVConnector)

    def __init__(self, appSettings: AppSettings = None, parentWidget=None):
        super().__init__(parentWidget)
        self.ui = UiTargetClass()
        self.ui.setupUi(self)

        if appSettings is not None:
            self.appSettings = copy.deepcopy(appSettings)
        else:
            self.appSettings = AppSettings()

        # # tray combo box
        for item in tray_icon.TrayIconTheme:
            itemName = item.name
            self.ui.trayThemeCB.addItem(itemName, item)

        trayIndex = tray_icon.TrayIconTheme.indexOf(self.appSettings.trayIcon)
        self.ui.trayThemeCB.setCurrentIndex(trayIndex)
        self.ui.trayThemeCB.currentIndexChanged.connect(self._trayThemeChanged)

        self.ui.caltypeTW.currentChanged.connect(self._calTypeChanged)

        self.ui.localEnabledCB.stateChanged.connect(self._changeCalEnable)
        self.ui.localCalendarNameLE.textChanged.connect(self._changedCalendarName)

        self.ui.caldavEnabledCB.stateChanged.connect(self._changeCalEnable)
        self.ui.serverURLLE.textChanged.connect(self._changedServerURL)
        self.ui.serverUserLE.textChanged.connect(self._changedServerUser)
        self.ui.serverPasswordLE.textChanged.connect(self._changedServerPasswd)
        self.ui.serverCalendarLE.textChanged.connect(self._changedCalendarName)

        self.ui.testURLPB.clicked.connect(self._testConnection)
        self.ui.newCalPB.clicked.connect(self._newCalendar)
        self.ui.removeCalendarPB.clicked.connect(self._removeSelected)

        self.ui.callistWidget.currentRowChanged.connect(self._selectedItemChanged)

        # self.ui.exportLocalPB.clicked.connect(self._exportLocalData)

        self._refreshWidget()

    ## =====================================================

    def _trayThemeChanged(self):
        selectedTheme = self.ui.trayThemeCB.currentData()
        self.appSettings.trayIcon = selectedTheme
        self.iconThemeChanged.emit(selectedTheme)

    ## =====================================================

    def _selectedItemChanged(self, currentRow: int):
        self._refreshWidget(currentRow)

    ## values:
    ##    0 - disabled
    ##    2 - enabled
    def _changeCalEnable(self, _new_state: int):
        curr_cal = self._getCurrentCalendar()
        self._updateCalendarFromWidget(curr_cal)
        self._refreshCalList()

    def _changedCalendarName(self, _new_text: str):
        curr_cal = self._getCurrentCalendar()
        self._updateCalendarFromWidget(curr_cal)
        self._refreshCalList()

    def _changedServerURL(self, _new_text: str):
        curr_cal = self._getCurrentCalendar()
        self._updateCalendarFromWidget(curr_cal)
        self._refreshCalList()

    def _changedServerUser(self, _new_text: str):
        curr_cal = self._getCurrentCalendar()
        self._updateCalendarFromWidget(curr_cal)
        self._refreshCalList()

    def _changedServerPasswd(self, _new_text: str):
        curr_cal = self._getCurrentCalendar()
        self._updateCalendarFromWidget(curr_cal)
        self._refreshCalList()

    def _newCalendar(self):
        self.appSettings.addLocalCalendar("new calendar")
        new_index = len(self.appSettings.calendar_items) - 1
        self._refreshWidget(new_index)

    def _removeSelected(self):
        current_item = self.ui.callistWidget.currentRow()
        del self.appSettings.calendar_items[current_item]
        self._refreshWidget(current_item)

    def _calTypeChanged(self, index):
        current_item = self.ui.callistWidget.currentRow()
        if current_item < 0:
            return
        mode = DatabaseMode.getByIndex(index)
        if mode is None:
            _LOGGER.warning("unable to get calendar mode by index %s", index)
            return

        new_cal = self._createCalendarFromWidget()
        if new_cal is not None:
            self.appSettings.calendar_items[current_item] = new_cal
            self._refreshCalList()

    def _testConnection(self):
        serverURL = self.ui.serverURLLE.text()
        serverUser = self.ui.serverUserLE.text()
        serverPassword = self.ui.serverPasswordLE.text()
        calendarName = self.ui.serverCalendarLE.text()

        try:
            connector = CalDAVConnector()
            connector.connectToServer(serverURL, serverUser, serverPassword)
        except Exception as ex:  # pylint: disable=W0718
            _LOGGER.warning("unable to connect to server: %s", ex)
            message = str(ex)
            QMessageBox.critical(self, "Connection test", "Connection problem:\n" + message)
            return

        try:
            connector.connectToCalendar(calendarName, allow_throw=True)
            QMessageBox.information(self, "Connection test", "Successfully connected to calendar")
        except Exception as ex:  # pylint: disable=W0718
            _LOGGER.warning("unable to get calendar: %s", ex)
            QMessageBox.critical(self, "Connection test", "Unable t connect to calendar:\n" + message)

    ## ====================================================

    def _getCurrentCalendar(self):
        current_item = self.ui.callistWidget.currentRow()
        return self.appSettings.getCalendar(current_item)

    def _refreshWidget(self, selectItem: int = -1):
        self._refreshCalList()

        blocked = self.ui.callistWidget.blockSignals(True)
        self.ui.callistWidget.setCurrentRow(selectItem)
        self.ui.callistWidget.blockSignals(blocked)

        curr_cal: CalendarItem = self.appSettings.getCalendar(selectItem)
        if curr_cal is None:
            self.ui.caltypeTW.setEnabled(False)
            self.ui.removeCalendarPB.setEnabled(False)
            local = LocalCalendarItem("")
            local.enabled = False
            self._setCalendarData(local)  ## set empty
            return

        self.ui.caltypeTW.setEnabled(True)
        self.ui.removeCalendarPB.setEnabled(True)
        self._setCalendarData(curr_cal)

    def _refreshCalList(self):
        cal_items_len = len(self.appSettings.calendar_items)
        cal_widget_len = self.ui.callistWidget.count()

        blocked = self.ui.callistWidget.blockSignals(True)
        if cal_widget_len > cal_items_len:
            for index in range(cal_widget_len - 1, cal_items_len - 1, -1):
                self.ui.callistWidget.takeItem(index)
        elif cal_items_len > cal_widget_len:
            for _index in range(cal_widget_len, cal_items_len):
                self.ui.callistWidget.addItem("")

        for index in range(cal_items_len):
            cal = self.appSettings.calendar_items[index]
            cal_name: str = cal.getCalendarName()
            cal_mode: DatabaseMode = cal.getCalendarMode()
            calendar_label: str = f"{cal_name}: {cal_mode.name}"

            cal_widget = self.ui.callistWidget.item(index)
            cal_widget.setText(calendar_label)
        self.ui.callistWidget.blockSignals(blocked)

    def _setCalendarData(self, prop_cal: CalendarItem):
        if isinstance(prop_cal, LocalCalendarItem):
            blocked = self.ui.caltypeTW.blockSignals(True)
            self.ui.caltypeTW.setCurrentIndex(0)
            self.ui.caltypeTW.blockSignals(blocked)

            check_state = 2 if prop_cal.isEnabled() else 0

            ## local tab
            blocked = self.ui.localEnabledCB.blockSignals(True)
            self.ui.localEnabledCB.setCheckState(check_state)
            self.ui.localEnabledCB.blockSignals(blocked)

            blocked = self.ui.localCalendarNameLE.blockSignals(True)
            self.ui.localCalendarNameLE.setText(prop_cal.calendarName)
            self.ui.localCalendarNameLE.blockSignals(blocked)

            ## caldav tab
            blocked = self.ui.caldavEnabledCB.blockSignals(True)
            self.ui.caldavEnabledCB.setCheckState(check_state)
            self.ui.caldavEnabledCB.blockSignals(blocked)

            blocked = self.ui.serverURLLE.blockSignals(True)
            self.ui.serverURLLE.setText("")
            self.ui.serverURLLE.blockSignals(blocked)

            blocked = self.ui.serverUserLE.blockSignals(True)
            self.ui.serverUserLE.setText("")
            self.ui.serverUserLE.blockSignals(blocked)

            blocked = self.ui.serverPasswordLE.blockSignals(True)
            self.ui.serverPasswordLE.setText("")
            self.ui.serverPasswordLE.blockSignals(blocked)

            blocked = self.ui.serverCalendarLE.blockSignals(True)
            self.ui.serverCalendarLE.setText(prop_cal.calendarName)
            self.ui.serverCalendarLE.blockSignals(blocked)

        elif isinstance(prop_cal, CalDAVCalendarItem):
            blocked = self.ui.caltypeTW.blockSignals(True)
            self.ui.caltypeTW.setCurrentIndex(1)
            self.ui.caltypeTW.blockSignals(blocked)

            check_state = 2 if prop_cal.isEnabled() else 0

            ## local tab
            blocked = self.ui.localEnabledCB.blockSignals(True)
            self.ui.localEnabledCB.setCheckState(check_state)
            self.ui.localEnabledCB.blockSignals(blocked)

            blocked = self.ui.localCalendarNameLE.blockSignals(True)
            self.ui.localCalendarNameLE.setText(prop_cal.calendarName)
            self.ui.localCalendarNameLE.blockSignals(blocked)

            ## caldav tab
            blocked = self.ui.caldavEnabledCB.blockSignals(True)
            self.ui.caldavEnabledCB.setCheckState(check_state)
            self.ui.caldavEnabledCB.blockSignals(blocked)

            blocked = self.ui.serverURLLE.blockSignals(True)
            self.ui.serverURLLE.setText(prop_cal.serverURL)
            self.ui.serverURLLE.blockSignals(blocked)

            blocked = self.ui.serverUserLE.blockSignals(True)
            self.ui.serverUserLE.setText(prop_cal.serverUser)
            self.ui.serverUserLE.blockSignals(blocked)

            blocked = self.ui.serverPasswordLE.blockSignals(True)
            self.ui.serverPasswordLE.setText(prop_cal.serverPassword)
            self.ui.serverPasswordLE.blockSignals(blocked)

            blocked = self.ui.serverCalendarLE.blockSignals(True)
            self.ui.serverCalendarLE.setText(prop_cal.calendarName)
            self.ui.serverCalendarLE.blockSignals(blocked)

        else:
            _LOGGER.warning("unhandled calendar type: %s", prop_cal.getCalendarMode())

    def _createCalendarFromWidget(self) -> CalendarItem:
        curr_index = self.ui.caltypeTW.currentIndex()
        mode = DatabaseMode.getByIndex(curr_index)
        if mode is None:
            _LOGGER.warning("unable to get calendar mode by index %s", curr_index)
            return None

        if mode == DatabaseMode.LOCAL:
            local_calendar = LocalCalendarItem()
            self._updateCalendarFromWidget(local_calendar)
            return local_calendar

        if mode == DatabaseMode.CALDAV:
            caldav_calendar = CalDAVCalendarItem()
            self._updateCalendarFromWidget(caldav_calendar)
            return caldav_calendar

        _LOGGER.warning("unhandled database type: %s", mode)
        return None

    def _updateCalendarFromWidget(self, calendar: CalendarItem) -> bool:
        mode = calendar.getCalendarMode()

        if isinstance(calendar, LocalCalendarItem):
            calendar.enabled = self.ui.localEnabledCB.checkState() != 0
            calendar.calendarName = self.ui.localCalendarNameLE.text()
            return True

        if isinstance(calendar, CalDAVCalendarItem):
            calendar.enabled = self.ui.caldavEnabledCB.checkState() != 0
            calendar.serverURL = self.ui.serverURLLE.text()
            calendar.serverUser = self.ui.serverUserLE.text()
            calendar.serverPassword = self.ui.serverPasswordLE.text()
            calendar.calendarName = self.ui.serverCalendarLE.text()
            return True

        _LOGGER.warning("unhandled database type: %s", mode)
        return False


## =========================================================================


def load_keys_to_dict(settings):
    state = {}
    for key in settings.childKeys():
        value = settings.value(key, "", type=str)
        if value:
            # not empty
            state[key] = value
    return state
