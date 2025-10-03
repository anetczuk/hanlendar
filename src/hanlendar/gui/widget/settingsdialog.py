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

from enum import Enum, unique, auto

from hanlendar.domainmodel.caldav.manager import CalDAVConnector

from PyQt5.QtWidgets import QRadioButton, QMessageBox

from ..qt import pyqtSignal
from .. import uiloader
from .. import tray_icon


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
        return items[ index ][ 1 ]


class AppSettings():

    def __init__(self):
        self.trayIcon = tray_icon.TrayIconTheme.WHITE

        self.databaseMode   = DatabaseMode.LOCAL
        self.serverURL      = ""
        self.serverUser     = ""
        self.serverPassword = ""
        self.calendarName   = ""

    def loadSettings(self, settings):
        settings.beginGroup("app_settings")

        trayName = settings.value("trayIcon", None, type=str)
        self.trayIcon = tray_icon.TrayIconTheme.findByName(trayName, tray_icon.TrayIconTheme.WHITE)

        databaseName = settings.value("databaseMode", None, type=str)
        self.databaseMode = DatabaseMode.findByName(databaseName, DatabaseMode.LOCAL)

        self.serverURL      = settings.value( "serverURL", "", type=str )
        self.serverUser     = settings.value( "serverUser", "", type=str )
        self.serverPassword = settings.value( "serverPassword", "", type=str )
        self.calendarName   = settings.value( "calendarName", "", type=str )

        settings.endGroup()

    def saveSettings(self, settings):
        settings.beginGroup("app_settings")

        settings.setValue("trayIcon", self.trayIcon.name)

        settings.setValue("databaseMode", self.databaseMode.name)

        settings.setValue( "serverURL", self.serverURL )
        settings.setValue( "serverUser", self.serverUser )
        settings.setValue( "serverPassword", self.serverPassword )
        settings.setValue( "calendarName", self.calendarName )

        settings.endGroup()


UiTargetClass, QtBaseClass = uiloader.load_ui_from_class_name(__file__)


_LOGGER = logging.getLogger(__name__)


class SettingsDialog(QtBaseClass):  # type: ignore

    iconThemeChanged = pyqtSignal( tray_icon.TrayIconTheme )
    exportLocal      = pyqtSignal( CalDAVConnector )

    def __init__(self, appSettings, parentWidget=None):
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

        self.ui.serverData.setEnabled(False)
        self.ui.localRB.toggled.connect(self.ui.serverData.setDisabled)
        self.ui.caldavRB.toggled.connect(self.ui.serverData.setEnabled)

        self.ui.serverURLLE.setText( self.appSettings.serverURL )
        self.ui.serverUserLE.setText( self.appSettings.serverUser )
        self.ui.serverPasswordLE.setText( self.appSettings.serverPassword )
        self.ui.calendarLE.setText( self.appSettings.calendarName )

        databaseIndex = DatabaseMode.indexOf(self.appSettings.databaseMode)
        databaseIndex = max(0, databaseIndex)
        gbChildren = self.ui.databaseGB.findChildren(QRadioButton)
        gbChildren[ databaseIndex ].toggle()

        self.ui.testURLPB.clicked.connect(self._testConnection)
        self.ui.exportLocalPB.clicked.connect(self._exportLocalData)

    def accept(self):
        # # set settings object
        self.appSettings.trayIcon = self.ui.trayThemeCB.currentData()

        databaseIndex = self._getDatabaseModeIndex()
        databaseIndex = max(0, databaseIndex)
        self.appSettings.databaseMode = DatabaseMode.getByIndex(databaseIndex, DatabaseMode.LOCAL)

        self.appSettings.serverURL      = self.ui.serverURLLE.text()
        self.appSettings.serverUser     = self.ui.serverUserLE.text()
        self.appSettings.serverPassword = self.ui.serverPasswordLE.text()
        self.appSettings.calendarName   = self.ui.calendarLE.text()

        super().accept()

    def _getDatabaseModeIndex(self):
        gbChildren = self.ui.databaseGB.findChildren(QRadioButton)
        for index in range(0, len(gbChildren)):
            item = gbChildren[ index ]
            if item.isChecked():
                return index
        return -1

    def _testConnection(self):
        serverURL      = self.ui.serverURLLE.text()
        serverUser     = self.ui.serverUserLE.text()
        serverPassword = self.ui.serverPasswordLE.text()
        calendarName   = self.ui.calendarLE.text()

        try:
            connector = CalDAVConnector()
            connector.connectToServer( serverURL, serverUser, serverPassword )
        except Exception as ex:
            _LOGGER.warning("unable to connect to server: %s", ex)
            message = str(ex)
            QMessageBox.critical(self, "Connection test", "Connection problem:\n" + message)

        try:
            connector.connectToCalendar( calendarName, allow_throw=True )
            QMessageBox.information(self, "Connection test", "Successfully connected to calendar")
        except Exception as ex:
            _LOGGER.warning("unable to get calendar: %s", ex)
            QMessageBox.information(self, "Connection test", "Successfully connected to server. New calendar will be created.")

    def _exportLocalData(self):
        serverURL      = self.ui.serverURLLE.text()
        serverUser     = self.ui.serverUserLE.text()
        serverPassword = self.ui.serverPasswordLE.text()
        calendarName   = self.ui.calendarLE.text()

        try:
            connector = CalDAVConnector()
            connector.connectToServer( serverURL, serverUser, serverPassword )
        except Exception as ex:
            _LOGGER.warning("unable to connect to server: %s", ex)
            message = str(ex)
            QMessageBox.critical(self, "Connection test", "Connection problem:\n" + message)
            return

        connector.connectToCalendar( calendarName )
        self.exportLocal.emit( connector )

    ## =====================================================

    def _trayThemeChanged(self):
        selectedTheme = self.ui.trayThemeCB.currentData()
        self.appSettings.trayIcon = selectedTheme
        self.iconThemeChanged.emit(selectedTheme)

    ## =====================================================

    def _setCurrentTrayTheme(self, trayTheme: str):
        themeIndex = tray_icon.TrayIconTheme.indexOf(trayTheme)
        if themeIndex < 0:
            _LOGGER.debug("could not find index for theme: %r", trayTheme)
            return
        self.ui.trayThemeCB.setCurrentIndex(themeIndex)


def load_keys_to_dict(settings):
    state = dict()
    for key in settings.childKeys():
        value = settings.value(key, "", type=str)
        if value:
            # not empty
            state[ key ] = value
    return state
