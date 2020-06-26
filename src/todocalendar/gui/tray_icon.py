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
from enum import Enum, unique

from .qt import qApp, QSystemTrayIcon, QMenu, QAction
from .qt import QIcon

from . import resources


_LOGGER = logging.getLogger(__name__)


@unique
class TrayIconTheme(Enum):
    WHITE   = 'calendar-white.png'
    BLACK   = 'calendar-black.png'

    @classmethod
    def findByName(cls, name):
        for item in cls:
            if item.name == name:
                return item
        return None

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


class TrayIcon(QSystemTrayIcon):
    def __init__(self, parent):
        super().__init__(parent)

        self.activated.connect( self._icon_activated )

        '''
            Define and add steps to work with the system tray icon
            show - show window
            hide - hide window
            exit - exit from application
        '''
        self.toggle_window_action = QAction("Show", self)
        quit_action = QAction("Exit", self)
        self.toggle_window_action.triggered.connect( self._toggleParent )
        quit_action.triggered.connect( qApp.quit )

        tray_menu = QMenu()
        tray_menu.addAction( self.toggle_window_action )
        tray_menu.addAction( quit_action )
        self.setContextMenu( tray_menu )

#     def displayMessage(self, message):
#         timeout = 10000
#         ## under xfce4 there is problem with balloon icon -- it changes tray icon, so
#         ## it cannot be changed back to proper one. Workaround is to use NoIcon parameter
#         self.showMessage("Keyboard", message, QSystemTrayIcon.NoIcon, timeout)

#     def setInfo(self, message):
#         self.setToolTip("Keyboard: " + message)

    def setIconTheme(self, theme: TrayIconTheme):
        _LOGGER.debug("setting tray theme: %r", theme)
        fileName = theme.value
        iconPath = resources.getImagePath( fileName )
        self.setIcon( QIcon( iconPath ) )

    def _icon_activated(self, reason):
#         print("tray clicked, reason:", reason)
        if reason == 3:
            ## clicked
            self._toggleParent()

    def _toggleParent(self):
        parent = self.parent()
        if parent.isHidden():
            parent.show()
        else:
            parent.hide()
        self.updateLabel()

    def updateLabel(self):
        parent = self.parent()
        if parent.isHidden():
            self.toggle_window_action.setText("Show")
        else:
            self.toggle_window_action.setText("Hide")
