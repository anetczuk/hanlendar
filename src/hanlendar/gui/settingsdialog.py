#     ClevoKeyboardControl. Control of keyboard backlights.
#
#     Copyright (C) 2018  Arkadiusz Netczuk <dev.arnet@gmail.com>
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <https://www.gnu.org/licenses/>.
#


import logging
import copy

from . import uiloader
from .qt import pyqtSignal
from . import tray_icon


class AppSettings():

    def __init__(self):
        self.trayIcon = tray_icon.TrayIconTheme.WHITE

    def loadSettings(self, settings):
        settings.beginGroup( "app_settings" )

        trayName = settings.value("trayIcon", None, type=str)
        self.trayIcon = tray_icon.TrayIconTheme.findByName( trayName )

        if self.trayIcon is None:
            self.trayIcon = tray_icon.TrayIconTheme.WHITE

        settings.endGroup()

    def saveSettings(self, settings):
        settings.beginGroup( "app_settings" )

        settings.setValue("trayIcon", self.trayIcon.name)

        settings.endGroup()


UiTargetClass, QtBaseClass = uiloader.load_ui_from_class_name( __file__ )


_LOGGER = logging.getLogger(__name__)


class SettingsDialog(QtBaseClass):           # type: ignore

    iconThemeChanged         = pyqtSignal( tray_icon.TrayIconTheme )

    def __init__(self, appSettings, parentWidget=None):
        super().__init__(parentWidget)
        self.ui = UiTargetClass()
        self.ui.setupUi(self)

        if appSettings is not None:
            self.appSettings = copy.deepcopy( appSettings )
        else:
            self.appSettings = AppSettings()

        ## tray combo box
        for item in tray_icon.TrayIconTheme:
            itemName = item.name
            self.ui.trayThemeCB.addItem( itemName, item )

        index = tray_icon.TrayIconTheme.indexOf( self.appSettings.trayIcon )
        self.ui.trayThemeCB.setCurrentIndex( index )

        self.ui.trayThemeCB.currentIndexChanged.connect( self._trayThemeChanged )

    ## =====================================================

    def _trayThemeChanged(self):
        selectedTheme = self.ui.trayThemeCB.currentData()
        self.appSettings.trayIcon = selectedTheme
        self.iconThemeChanged.emit( selectedTheme )

    ## =====================================================

    def _setCurrentTrayTheme( self, trayTheme: str ):
        themeIndex = tray_icon.TrayIconTheme.indexOf( trayTheme )
        if themeIndex < 0:
            _LOGGER.debug("could not find index for theme: %r", trayTheme)
            return
        self.ui.trayThemeCB.setCurrentIndex( themeIndex )


def load_keys_to_dict(settings):
    state = dict()
    for key in settings.childKeys():
        value = settings.value(key, "", type=str)
        if value:
            # not empty
            state[ key ] = value
    return state
