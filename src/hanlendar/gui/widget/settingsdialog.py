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

from ..qt import pyqtSignal
from .. import uiloader
from .. import tray_icon


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
